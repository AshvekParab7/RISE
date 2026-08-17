from django.utils import timezone
from .chunker import chunk_text
from .document_processor import extract_document
from .embeddings import embed_text
from ..models import ResourceChunk

def process_resource(resource):
    try:
        text = extract_document(resource)
        ResourceChunk.objects.filter(resource=resource).delete()
        chunks = chunk_text(text)
        ResourceChunk.objects.bulk_create([ResourceChunk(resource=resource, student=resource.student, subject=resource.subject, text=chunk['text'], chunk_index=chunk['chunk_index'], embedding=embed_text(chunk['text'])) for chunk in chunks])
        resource.processing_status = resource.ProcessingStatus.READY
        resource.processing_error = ''
        resource.processed_at = timezone.now()
        resource.is_ai_ready = True
    except Exception as exc:
        resource.processing_status = resource.ProcessingStatus.FAILED
        resource.processing_error = 'RISE could not process this file.'
    resource.save(update_fields=['processing_status', 'processing_error', 'processed_at', 'is_ai_ready', 'updated_at'])
    return resource
