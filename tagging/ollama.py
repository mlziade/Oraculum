import os
import requests
import json
import base64

class OllamaService:
    def __init__(self):
        self.base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.timeout = int(os.getenv('OLLAMA_TIMEOUT', '30'))
        self.default_model = os.getenv('OLLAMA_DEFAULT_MODEL')
        
        # List of vision-capable models
        self.vision_models = [
            'gemma3:4b',
            'gemma3:12b',
            'qwen2.5vl:3b',
            'qwen2.5vl:7b',
            'llava:7b',
            'llama3.2-vision:11b',
        ]
    
    def is_server_running(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def list_models(self) -> list[dict]:
        """Get list of available models from Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            response.raise_for_status()
            return response.json().get('models', [])
        except requests.RequestException as e:
            raise Exception(f"Failed to list models: {e}")
    
    def generate_text(self, prompt: str, model: str = None, **kwargs) -> str:
        """Generate text using Ollama"""
        model = model or self.default_model
        if not model:
            raise ValueError("No model specified and OLLAMA_DEFAULT_MODEL is not set.")
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json().get('response', '')
        except requests.RequestException as e:
            raise Exception(f"Failed to generate text: {e}")
    
    def generate_with_image(self, prompt: str, image_paths: str | list[str], model: str = None) -> str:
        """Generate text with image input using vision models"""
        model = model or self.default_model
        if not model:
            raise ValueError("No model specified and OLLAMA_DEFAULT_MODEL is not set.")
        
        if model not in self.vision_models:
            raise ValueError(f"Model {model} is not vision-capable. Use one of: {self.vision_models}")
        
        # Handle single image path or list of image paths
        if isinstance(image_paths, str):
            image_paths = [image_paths]
        
        # Encode all images to base64
        encoded_images = []
        for image_path in image_paths:
            try:
                with open(image_path, 'rb') as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')
                    encoded_images.append(image_data)
            except FileNotFoundError:
                raise Exception(f"Image file not found: {image_path}")
        
        payload = {
            "model": model,
            "prompt": prompt,
            "images": encoded_images,
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json().get('response', '')
        except requests.RequestException as e:
            raise Exception(f"Failed to generate with image: {e}")
    
    def get_vision_models(self) -> list[str]:
        """Get list of vision-capable models"""
        return self.vision_models.copy()
    
    def is_vision_model(self, model: str) -> bool:
        """Check if a model supports vision"""
        return model in self.vision_models
