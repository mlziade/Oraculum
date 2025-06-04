# Oraculum

## Description

Oraculum is an intelligent image gallery application to manage and handle all your pictures locally. It allows the user to search for, filter through and group their pictures based on tags, facial recognition, themes, etc.

## Goals

My goal is to create a fast MVP project that runs on top of easy technologies that I'm familiar with, so I can focus on the real problems before optimizing and adding full features. I might add a simple interface using vanilla HTML/CSS/JS to prove the concept, but I would like to build it as a SPA application in the future with a modern look.

## Technologies

### Backend

- Django (with Django REST Framework)
- Ollama (for locally running Vision Models)
- OpenCV (for easy Face Detection)
- SQLite

## Features

### Current Functionality
- ✅ **Image Upload & Management**: Upload images with automatic processing
- ✅ **Local AI-Powered Tagging**: Automatic tag classification using local LLM vision models
- ✅ **Facial Extraction**: Face detection with bounding box coordinates and confidence scoring
- ✅ **Processing Queue**: Asynchronous job processing with status tracking

### Roadmap
- 🚧 **Tag Classifications**: Hierarchical tag organization with customizable categories
- 🚧 **Facial Recognition Clustering**: Identity matching and grouping across multiple images
- 🚧 **Image Similarity**: Content-based image similarity search
- 🚧 **Natural Language Search**: Query images using conversational language (e.g., "show me photos of people celebrating outdoors") with semantic understanding and relevance scoring
- 🚧 **Bulk Operations**: Batch image processing and management
- 🚧 **Export/Import**: Data export and backup functionality
- 🚧 **Duplicate Detection**: Automatic duplicate image identification

## License

This project is licensed under the MIT License - see the LICENSE file for details.