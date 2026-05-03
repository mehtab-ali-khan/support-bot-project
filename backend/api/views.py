from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pgvector.django import CosineDistance
from .serializers import PDFUploadSerializer
from .models import DocumentChunk
from .embeddings import get_embedding
from .rag import generate_answer
import pdfplumber


def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


class HealthCheckView(APIView):
    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class PDFUploadView(APIView):
    def post(self, request):
        serializer = PDFUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        file = serializer.validated_data["file"]

        if not file.name.endswith(".pdf"):
            return Response(
                {"error": "Only PDF files are allowed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with pdfplumber.open(file) as pdf:

                if len(pdf.pages) == 0:
                    return Response(
                        {"error": "PDF file is empty"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                extracted_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"

                if not extracted_text.strip():
                    return Response(
                        {
                            "error": "No text found in PDF. It may be a scanned image PDF."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        except Exception as e:
            return Response(
                {"error": f"Could not process PDF: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        DocumentChunk.objects.all().delete()
        chunks = chunk_text(extracted_text)

        for index, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            DocumentChunk.objects.create(
                text=chunk, chunk_index=index, embedding=embedding
            )

        return Response(
            {
                "message": "PDF uploaded and chunked successfully",
                "pages": len(pdf.pages),
                "total_chunks": len(chunks),
                "characters": len(extracted_text),
            },
            status=status.HTTP_200_OK,
        )


class AskView(APIView):
    def post(self, request):
        question = request.data.get("question", "")

        if not question.strip():
            return Response(
                {"error": "No question provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        if DocumentChunk.objects.count() == 0:
            return Response(
                {"error": "No document uploaded yet. Please upload a PDF first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        question_embedding = get_embedding(question, task_type="RETRIEVAL_QUERY")

        similar_chunks = DocumentChunk.objects.order_by(
            CosineDistance("embedding", question_embedding)
        )[:3]

        result = generate_answer(question, similar_chunks)

        return Response(
            {
                "question": question,
                "answer": result.get("answer", ""),
                "confidence": result.get("confidence", ""),
                "sources": result.get("sources", []),
            },
            status=status.HTTP_200_OK,
        )
