from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from .serializers import PDFUploadSerializer
from .langchain_rag import ingest_document, answer_question
import pdfplumber


def is_document_uploaded():
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM langchain_pg_embedding e
                JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                WHERE c.name = 'document_chunks'
            """)
            count = cursor.fetchone()[0]
            return count > 0
    except Exception:
        return False


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

        if not file.name.lower().endswith(".pdf"):
            return Response(
                {"error": "Only PDF files are allowed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with pdfplumber.open(file) as pdf:
                pages_count = len(pdf.pages)
                if pages_count == 0:
                    return Response(
                        {"error": "PDF file is empty"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                extracted_pages = []
                for page_number, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()
                    if page_text:
                        extracted_pages.append({"page": page_number, "text": page_text})

                if not extracted_pages:
                    return Response(
                        {"error": "No text found in PDF."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        except Exception as e:
            return Response(
                {"error": f"Could not process PDF: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total_chunks = ingest_document(extracted_pages, source=file.name)

        return Response(
            {
                "message": "PDF uploaded and processed successfully",
                "pages": pages_count,
                "total_chunks": total_chunks,
            },
            status=status.HTTP_200_OK,
        )


class AskView(APIView):
    def post(self, request):
        question = request.data.get("question", "")

        if not is_document_uploaded():
            return Response(
                {"error": "No document uploaded yet. Please upload a PDF first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not question.strip():
            return Response(
                {"error": "No question provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = answer_question(question)
            return Response(
                {
                    "question": question,
                    "answer": result["answer"],
                    "sources": result["sources"],
                    "tools_used": result.get("tools_used", []),
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
