from rest_framework import serializers
from .models import Picture
from tagging.models import Tag, TagClassification


class TagClassificationSerializer(serializers.ModelSerializer):
    """Serializer for TagClassification model."""
    
    class Meta:
        model = TagClassification
        fields = ['id', 'name']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""
    classification = TagClassificationSerializer(read_only=True)
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'classification']


class PictureSerializer(serializers.ModelSerializer):
    """Serializer for Picture model with nested tags."""
    tags = TagSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()
    miniature = serializers.SerializerMethodField()
    
    class Meta:
        model = Picture
        fields = [
            'id', 'title', 'description', 'image', 'miniature', 
            'created_at', 'updated_at', 'tags'
        ]
    
    def get_image(self, obj):
        """Return image URL if exists, None otherwise."""
        return obj.image.url if obj.image else None
    
    def get_miniature(self, obj):
        """Return miniature URL if exists, None otherwise."""
        return obj.miniature.url if obj.miniature else None


class PictureListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing pictures without heavy nested data."""
    tags_count = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    miniature = serializers.SerializerMethodField()
    
    class Meta:
        model = Picture
        fields = [
            'id', 'title', 'description', 'image', 'miniature', 
            'created_at', 'updated_at', 'tags_count'
        ]
    
    def get_tags_count(self, obj):
        """Return the count of tags for this picture."""
        return obj.tags.count()
    
    def get_image(self, obj):
        """Return image URL if exists, None otherwise."""
        return obj.image.url if obj.image else None
    
    def get_miniature(self, obj):
        """Return miniature URL if exists, None otherwise."""
        return obj.miniature.url if obj.miniature else None