import os
import time
import base64
import requests
from typing import Dict, Any, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.timeout = 30  # seconds
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
    
    def extract_text_from_image(self, image_data: bytes, image_type: str = "main") -> Tuple[bool, Dict[str, Any]]:
        """
        Extract text from image using Gemini API with retry mechanism
        
        Args:
            image_data: Raw image bytes
            image_type: Type of image ("main" or "secondary")
            
        Returns:
            Tuple of (success: bool, result: dict)
        """
        # Convert image to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Prepare the request payload
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": """Extract all text content from this image. Please provide:
1. All visible text in the image
2. Any UI labels, buttons, form fields, or interface elements
3. Headers, titles, and navigation items
4. Any error messages or notifications
5. Organize the text logically (top to bottom, left to right)

Please format the response as structured text that preserves the layout and hierarchy."""
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",  # Gemini handles multiple formats
                                "data": image_base64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,  # Low temperature for consistent text extraction
                "topK": 1,
                "topP": 1,
                "maxOutputTokens": 2048
            }
        }
        
        # Attempt with retry mechanism
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Attempting Gemini API call (attempt {attempt + 1}/{self.max_retries}) for {image_type} image")
                logger.info(f"Waiting for Gemini API response (timeout: {self.timeout}s)...")
                
                response = requests.post(
                    f"{self.api_url}?key={self.api_key}",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Gemini API responded successfully (status: {response.status_code})")
                    
                    # Extract text from Gemini response
                    extracted_text = self._parse_gemini_response(result)
                    logger.info(f"Gemini response: Extracted {len(extracted_text)} characters of text from {image_type} image")
                    
                    success_result = {
                        "success": True,
                        "extracted_text": extracted_text,
                        "raw_response": result,
                        "image_type": image_type,
                        "processed_at": datetime.utcnow().isoformat(),
                        "attempt": attempt + 1
                    }
                    
                    logger.info(f"Successfully extracted text from {image_type} image on attempt {attempt + 1}")
                    return True, success_result
                    
                elif response.status_code == 429:  # Rate limit
                    logger.warning(f"Gemini API responded with rate limit (status: {response.status_code}) on attempt {attempt + 1}, retrying...")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                        continue
                        
                elif response.status_code >= 500:  # Server errors
                    logger.warning(f"Gemini API responded with server error (status: {response.status_code}) on attempt {attempt + 1}, retrying...")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))
                        continue
                        
                else:  # Client errors (400, 401, 403, etc.)
                    error_result = {
                        "success": False,
                        "error": f"Gemini API client error: {response.status_code}",
                        "details": response.text,
                        "image_type": image_type,
                        "failed_at": datetime.utcnow().isoformat(),
                        "attempt": attempt + 1
                    }
                    logger.error(f"Gemini API responded with client error (status: {response.status_code}): {response.text}")
                    return False, error_result
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request exception on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                    
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
        
        # All retries failed
        error_result = {
            "success": False,
            "error": "All retry attempts failed",
            "details": f"Failed after {self.max_retries} attempts",
            "image_type": image_type,
            "failed_at": datetime.utcnow().isoformat(),
            "max_retries_reached": True
        }
        
        logger.error(f"Failed to extract text from {image_type} image after {self.max_retries} attempts")
        return False, error_result
    
    def _parse_gemini_response(self, response: Dict[str, Any]) -> str:
        """
        Parse Gemini API response to extract text content
        """
        try:
            if 'candidates' in response and len(response['candidates']) > 0:
                candidate = response['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    if len(parts) > 0 and 'text' in parts[0]:
                        return parts[0]['text'].strip()
            
            # Fallback if structure is different
            logger.warning("Unexpected Gemini response structure, returning raw response")
            return str(response)
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            return f"Error parsing response: {str(e)}"

# Global instance
gemini_service = GeminiService()