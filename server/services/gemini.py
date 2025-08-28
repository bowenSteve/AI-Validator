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
                            "text": """You are a highly accurate OCR specialist extracting text for business data validation. This text will be used for critical business processes, so ACCURACY IS PARAMOUNT.

CRITICAL REQUIREMENTS:
- Company names must be spelled EXACTLY as shown (e.g., "LIGHTNING" not "LIGHTENING")
- Addresses must include all numbers, street names, and unit numbers precisely
- Pay special attention to easily confused letters: I/L, O/0, S/5, G/6, B/8
- Double-check spelling of business-critical terms

EXTRACT ALL TEXT INCLUDING:
1. Company/Organization names (verify spelling carefully)
2. Complete addresses with all components
3. Names, titles, and contact information
4. Form labels, buttons, and UI elements
5. Headers, navigation, and section titles
6. Error messages or status indicators

FORMAT REQUIREMENTS:
- Preserve original layout and hierarchy
- Use consistent spacing and line breaks
- Group related information together
- List items in logical reading order (top-to-bottom, left-to-right)

CONFIDENCE INDICATORS:
- If any text is unclear or ambiguous, note: [UNCERTAIN: text]
- For partially visible text, note: [PARTIAL: text]
- Maintain high confidence in business names and addresses

EXAMPLE OUTPUT FORMAT:
Organization Name: [EXACT NAME HERE]
Address: [COMPLETE ADDRESS]
City: [CITY NAME]
State: [STATE]
Postal Code: [ZIP CODE]

Remember: Business validation depends on your accuracy. When in doubt, be conservative but precise."""
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
                    
                    # Parse confidence indicators
                    confidence_score = self._calculate_confidence_score(extracted_text)
                    has_uncertainties = "[UNCERTAIN:" in extracted_text or "[PARTIAL:" in extracted_text
                    
                    # Additional business text validation
                    validation_result = self.validate_business_text(extracted_text)
                    
                    success_result = {
                        "success": True,
                        "extracted_text": extracted_text,
                        "confidence_score": confidence_score,
                        "has_uncertainties": has_uncertainties,
                        "validation": validation_result,
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
    
    def _calculate_confidence_score(self, extracted_text: str) -> float:
        """
        Calculate confidence score based on uncertainty markers and text quality
        """
        if not extracted_text:
            return 0.0
            
        total_length = len(extracted_text)
        if total_length == 0:
            return 0.0
        
        # Count uncertainty markers
        uncertain_markers = extracted_text.count("[UNCERTAIN:")
        partial_markers = extracted_text.count("[PARTIAL:")
        
        # Calculate penalty for uncertainty markers
        uncertainty_penalty = (uncertain_markers * 10) + (partial_markers * 5)
        
        # Base confidence starts at 100%
        confidence = 100.0
        
        # Apply uncertainty penalties
        confidence = max(0.0, confidence - uncertainty_penalty)
        
        # Additional quality indicators
        if len(extracted_text.strip()) < 10:
            confidence *= 0.5  # Very short text is suspicious
            
        # Check for structured output (good sign)
        structured_indicators = [
            "Organization Name:",
            "Address:",
            "City:",
            "State:",
            "Postal Code:"
        ]
        
        structure_score = sum(1 for indicator in structured_indicators if indicator in extracted_text)
        if structure_score > 2:
            confidence = min(100.0, confidence * 1.1)  # Boost for good structure
        
        return round(confidence, 2)
    
    def validate_business_text(self, extracted_text: str) -> Dict[str, Any]:
        """
        Additional validation for business-critical text
        """
        validation_issues = []
        suggestions = []
        
        # Check for common OCR confusion patterns
        confusion_patterns = {
            'LIGHTENING': 'LIGHTNING',
            'LIGHTINING': 'LIGHTNING', 
            'LIGTENING': 'LIGHTNING',
            'LIGHTNENG': 'LIGHTNING'
        }
        
        text_upper = extracted_text.upper()
        for wrong, correct in confusion_patterns.items():
            if wrong in text_upper:
                validation_issues.append(f"Possible OCR error: '{wrong}' should likely be '{correct}'")
                suggestions.append(f"Double-check if '{wrong}' should be '{correct}'")
        
        # Check for suspicious character patterns
        suspicious_patterns = [
            (r'\d{1}[IL]{1}', "Number followed by I/L might be address confusion"),
            (r'[IL]{1}\d{1}', "I/L followed by number might be address confusion"), 
            (r'[O0]{2,}', "Multiple O/0 characters should be verified"),
            (r'\s{3,}', "Excessive spacing might indicate OCR issues")
        ]
        
        import re
        for pattern, message in suspicious_patterns:
            if re.search(pattern, extracted_text):
                validation_issues.append(message)
        
        return {
            'has_validation_issues': len(validation_issues) > 0,
            'validation_issues': validation_issues,
            'suggestions': suggestions,
            'needs_human_review': len(validation_issues) > 2
        }

# Global instance
gemini_service = GeminiService()