from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from django.conf import settings
import json
import re

CONNECTION_STRING = (
    f"postgresql+psycopg2://"
    f"{settings.DATABASES['default']['USER']}:"
    f"{settings.DATABASES['default']['PASSWORD']}@"
    f"{settings.DATABASES['default']['HOST']}:"
    f"{settings.DATABASES['default']['PORT']}/"
    f"{settings.DATABASES['default']['NAME']}"
)

COLLECTION_NAME = "document_chunks"

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=settings.GEMINI_API_KEY,
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", google_api_key=settings.GEMINI_API_KEY, temperature=0
)

summary_prompt = PromptTemplate(
    template="""Summarize the uploaded document using only the context below.

Write a short high-level summary. Mention the document type if it is clear.
Do not invent missing details.

Context:
{context}

Summary:""",
    input_variables=["context"],
)

tools = [
    {
        "name": "search_document",
        "description": "Search the uploaded document for relevant information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_document_summary",
        "description": "Get a summary of what the uploaded document is about",
        "parameters": {"type": "object", "properties": {}},
    },
]


def get_vectorstore(pre_delete=False):
    return PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
        pre_delete_collection=pre_delete,
    )


def format_docs(docs):
    formatted_docs = []
    for doc in docs:
        page = doc.metadata.get("page")
        chunk_index = doc.metadata.get("chunk_index")
        label = f"[Page {page}, chunk {chunk_index}]"
        formatted_docs.append(f"{label}\n{doc.page_content}")
    return "\n\n".join(formatted_docs)


def clean_text(text):
    text = re.sub(r"\b(?:[A-Za-z]\s+){2,}[A-Za-z]\b", _join_spaced_letters, text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _join_spaced_letters(match):
    return match.group(0).replace(" ", "")


def ingest_document(pages, source="uploaded.pdf"):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        add_start_index=True,
    )

    if isinstance(pages, str):
        pages = [{"page": 1, "text": pages}]

    page_docs = [
        Document(
            page_content=clean_text(page["text"]),
            metadata={"page": page["page"], "source": source},
        )
        for page in pages
        if page.get("text", "").strip()
    ]

    chunks = splitter.split_documents(page_docs)
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index

    vectorstore = get_vectorstore(pre_delete=True)
    vectorstore.add_documents(chunks)
    return len(chunks)


def serialize_scored_docs(scored_docs, content_limit=300):
    return [
        {
            "page": doc.metadata.get("page"),
            "chunk_index": doc.metadata.get("chunk_index"),
            "source": doc.metadata.get("source"),
            "score": float(score),
            "content": doc.page_content[:content_limit],
        }
        for doc, score in scored_docs
    ]


def search_document(query, k=5):
    vectorstore = get_vectorstore()
    scored_docs = vectorstore.similarity_search_with_score(query, k=k)

    return {
        "query": query,
        "chunks": serialize_scored_docs(scored_docs, content_limit=1000),
    }


def get_document_summary():
    vectorstore = get_vectorstore()
    scored_docs = vectorstore.similarity_search_with_score(
        "document overview summary main topics", k=8
    )
    source_docs = [doc for doc, _score in scored_docs]

    chain = summary_prompt | llm | StrOutputParser()
    summary = chain.invoke({"context": format_docs(source_docs)})

    return {
        "summary": summary,
        "sources": serialize_scored_docs(scored_docs, content_limit=300),
    }


def run_tool_call(tool_call):
    tool_name = tool_call["name"]
    tool_args = tool_call.get("args", {})

    if tool_name == "search_document":
        return search_document(tool_args["query"])

    if tool_name == "get_document_summary":
        return get_document_summary()

    return {"error": f"Unknown tool: {tool_name}"}


def collect_sources(tool_results):
    sources = []
    for result in tool_results:
        if "chunks" in result:
            sources.extend(result["chunks"])
        if "sources" in result:
            sources.extend(result["sources"])
    return sources


def answer_question(question):
    max_tool_rounds = 3
    tool_llm = llm.bind_tools(tools)
    messages = [
        SystemMessage(content="""You are a document question-answering assistant.

You have access to tools for reading the uploaded document.
Use search_document for specific factual questions.
Use get_document_summary when the user asks for an overview or summary.
For multi-part questions, handle every part before giving the final answer.
If the user asks for a summary or overview plus a specific fact, call get_document_summary and then call search_document for the specific fact.
If one tool result does not answer every part of the question, call another tool with a focused query.
If a tool result does not contain the answer, say that the uploaded document does not contain enough information.
Do not guess or use outside knowledge."""),
        HumanMessage(content=question),
    ]

    tool_results = []
    tools_used = []

    for _round in range(max_tool_rounds):
        response = tool_llm.invoke(messages)
        tool_calls = getattr(response, "tool_calls", None) or []

        if not tool_calls:
            return {
                "answer": response.content,
                "sources": collect_sources(tool_results),
                "tools_used": tools_used,
            }

        messages.append(response)

        for tool_call in tool_calls:
            result = run_tool_call(tool_call)
            tool_results.append(result)
            tools_used.append(tool_call["name"])
            messages.append(
                ToolMessage(
                    content=json.dumps(result),
                    tool_call_id=tool_call["id"],
                )
            )

    messages.append(
        HumanMessage(
            content="Use the tool results already provided and give the final answer now."
        )
    )
    final_response = llm.invoke(messages)

    return {
        "answer": final_response.content,
        "sources": collect_sources(tool_results),
        "tools_used": tools_used,
    }
