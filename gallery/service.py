import os
import uuid
from django.db.models import QuerySet


def hash_upload_path(instance: object, filename: str) -> str:
    """Generate a random hash filename while preserving the extension."""
    ext = os.path.splitext(filename)[1]  # Get the file extension
    random_filename = f"{uuid.uuid4().hex}{ext}"
    return os.path.join('pictures/', random_filename)


def miniature_upload_path(instance: object, filename: str) -> str:
    """Generate a random hash filename for miniatures while preserving the extension."""
    ext = os.path.splitext(filename)[1]  # Get the file extension
    random_filename = f"{uuid.uuid4().hex}{ext}"
    return os.path.join('miniatures/', random_filename)


def query_picture_by_tags(tag_names: list) -> QuerySet:
    """
    Query pictures by tags using OR logic (non-additive).
    Returns pictures that have ANY of the specified tags.
    
    Args:
        tag_names: List of tag names to search for
        
    Returns:
        QuerySet of pictures that match any of the tags
    """
    from .models import Picture
    return Picture.objects.filter(
        tags__name__in=tag_names
    ).distinct().prefetch_related('tags', 'tags__classification')


def serialize_pictures(pictures: QuerySet) -> list:
    """
    Serialize a queryset of pictures to dictionary format using DRF serializers.
    
    Args:
        pictures: QuerySet of Picture objects
        
    Returns:
        List of dictionaries representing the pictures
    """
    from .serializers import PictureSerializer
    serializer = PictureSerializer(pictures, many=True)
    return serializer.data


def serialize_pictures_list(pictures: QuerySet) -> list:
    """
    Serialize a queryset of pictures using the simplified list serializer.
    Better for performance when you don't need full tag details.
    
    Args:
        pictures: QuerySet of Picture objects
        
    Returns:
        List of dictionaries representing the pictures (simplified)
    """
    from .serializers import PictureListSerializer
    serializer = PictureListSerializer(pictures, many=True)
    return serializer.data
