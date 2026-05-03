from django.db import models
from pgvector.django import VectorField


class DocumentChunk(models.Model):
    text = models.TextField()
    chunk_index = models.IntegerField()
    embedding = VectorField(dimensions=3072, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chunk {self.chunk_index} — {self.text[:50]}"
