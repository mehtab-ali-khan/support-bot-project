from google import genai
from google.genai import types
from django.conf import settings
import json

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def generate_answer(question, chunks):
    context = "\n\n".join([chunk.text for chunk in chunks])

    prompt = f"""You are a helpful assistant that answers questions about uploaded documents.
Answer the question using ONLY the context provided below.
If the answer is not in the context, say "I don't have that information."

Respond ONLY with a valid JSON object in this exact format with no extra text:
{{
    "answer": "your answer here",
    "confidence": "high or medium or low",
    "sources": ["first relevant chunk text snippet", "second relevant chunk text snippet" ,"third relevant chunk text snippet"]
}}

Confidence rules:
- high: answer is clearly and directly stated in context
- medium: answer can be inferred from context
- low: answer is only partially in context

Few-shot examples:

Example 1:
Context: "John has 5 years of experience in Python and Django. He worked at TechCorp from 2019 to 2024."
Question: "How many years of Python experience does John have?"
Response:
{{
    "answer": "John has 5 years of experience in Python and Django, working at TechCorp from 2019 to 2024.",
    "confidence": "high",
    "sources": ["John has 5 years of experience in Python and Django."]
}}

Example 2:
Context: "John completed his Bachelor's degree in Computer Science from FAST University in 2019."
Question: "Where did John study?"
Response:
{{
    "answer": "John studied Computer Science at FAST University, completing his Bachelor's degree in 2019.",
    "confidence": "high",
    "sources": ["John completed his Bachelor's degree in Computer Science from FAST University in 2019."]
}}

Example 3:
Context: "John has worked on React, Node.js and PostgreSQL projects."
Question: "Does John know machine learning?"
Response:
{{
    "answer": "I don't have that information.",
    "confidence": "low",
    "sources": []
}}

Now answer this:
Context:
{context}

Question: {question}

Response:"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0, response_mime_type="application/json"
        ),
    )

    try:
        result = json.loads(response.text)
    except json.JSONDecodeError:
        result = {"answer": response.text, "confidence": "low", "sources": []}

    return result
