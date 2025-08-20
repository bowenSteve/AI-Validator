import os
import requests
from typing import Dict, Any, Tuple
import logging
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)

class GeminiValidator:
    """Specialized Gemini service for validating data transfer accuracy"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.timeout = 30
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
    
    def validate_data_transfer(self, source_text: str, destination_text: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Use Gemini to intelligently validate if data was transferred correctly
        
        Args:
            source_text: Text extracted from the source image
            destination_text: Text extracted from the destination image
            
        Returns:
            Tuple of (success: bool, result: dict)
        """
        
        # Create a comprehensive prompt for Gemini to analyze data transfer accuracy
        prompt = f"""You are an expert data validation specialist analyzing whether information was correctly transferred from a source document into a destination form/system.

CONTEXT:
- Users copy data from source documents (like PDFs, forms, applications) 
- They paste this data into web forms, applications, or other systems
- Your job is to verify that EVERY piece of data in the destination exists somewhere in the source
- This is ONE-WAY validation: destination data must be found in source (not the reverse)
- Focus ONLY on the actual data values, not UI elements, navigation, or formatting

CRITICAL INSTRUCTIONS:
1. **ONE-WAY VALIDATION**: For each piece of data in the DESTINATION, verify it exists somewhere in the SOURCE
2. **IGNORE UI ELEMENTS**: Disregard field labels, buttons, form instructions, asterisks (*), navigation elements
3. **FIND SOURCE ORIGIN**: For every destination value, locate where it came from in the source
4. **FORMATTING FLEXIBILITY**: Same data can have different formatting:
   - "NJ" in source = "New Jersey" in destination ✅
   - "(555) 123-4567" in source = "5551234567" in destination ✅
   - "56 Broad St\nSTE 14033" in source = "56 Broad St STE 14033" in destination ✅
5. **COMBINATION RULE**: Multiple source lines can combine into one destination field:
   - Source: "56 Broad St" + "STE 14033" → Destination: "56 Broad St STE 14033" ✅
6. **ERROR DETECTION**: Flag data that appears in destination but NOT in source:
   - Source: "56 Broad St" → Destination: "65 Broad St" ❌ (typo)
   - Source: "Boston" → Destination: "Boston, MA 02109" ❌ (added data not in source)

EXAMPLES OF CORRECT DATA EQUIVALENCE:

**ADDRESS EXAMPLES:**
✅ Source: "56 Broad St STE 14033" ←→ Dest: "Address 1: 56 Broad St STE 14033, Address 2: (empty)" = PERFECT MATCH
✅ Source: "56 Broad St\nSTE 14033" ←→ Dest: "56 Broad St STE 14033" = PERFECT MATCH  
✅ Source: "* 56 Broad St\n* STE 14033" ←→ Dest: "Address 1: 56 Broad St STE 14033" = PERFECT MATCH (suite combines with street)
✅ Source: "111 Town Square Pl Ste 1238" ←→ Dest: "Street: 111 Town Square Pl, Unit: Ste 1238" = PERFECT MATCH
✅ Source: "Street: 123 Main St\nApt: 4B" ←→ Dest: "Address: 123 Main St Apt 4B" = PERFECT MATCH (apartment part of address)

**NAME EXAMPLES:**
✅ Source: "John A. Smith" ←→ Dest: "First: John, Middle: A, Last: Smith" = PERFECT MATCH
✅ Source: "ACME CORPORATION" ←→ Dest: "Company: ACME CORPORATION" = PERFECT MATCH

**FORMATTING EXAMPLES:**
✅ Source: "NJ" ←→ Dest: "New Jersey" = PERFECT MATCH (state abbreviation vs full name)
✅ Source: "(555) 123-4567" ←→ Dest: "5551234567" = PERFECT MATCH (phone formatting)
✅ Source: "07310" ←→ Dest: "ZIP: 07310" = PERFECT MATCH (same zip code)

**VALIDATION APPROACH:**
For each destination field, ask: "Can I find this data somewhere in the source?"
- Destination: "56 Broad St STE 14033" → Source contains: "56 Broad St" + "STE 14033" ✅ VALID
- Destination: "New Jersey" → Source contains: "NJ" ✅ VALID (state abbreviation)
- Destination: "Lightning Corp" → Source contains: "Lightening Corp" ❌ INVALID (spelling changed)

**ERRORS TO CATCH:**
❌ Destination data NOT found in source (typos, additions, changes)
❌ Source: "LIGHTENING" → Dest: "LIGHTNING" = SPELLING CHANGED
❌ Source: "56 Broad St" → Dest: "65 Broad St" = NUMBER CHANGED  
❌ Source: "Boston" → Dest: "Boston Springs" = LOCATION CHANGED

SOURCE TEXT (what should be copied FROM):
{source_text}

DESTINATION TEXT (what was copied TO):
{destination_text}

Analyze the data transfer and respond with a JSON object in this exact format:
{{
    "accuracy_score": 95,
    "is_successful_transfer": true,
    "summary": "Excellent data transfer. All key information correctly transferred with proper formatting.",
    "matched_data": [
        {{"field": "Organization Name", "source_value": "LIGHTENING TRUCKING L.L.C.", "dest_value": "LIGHTENING TRUCKING L.L.C.", "match": "exact", "confidence": 100}},
        {{"field": "Street Address", "source_value": "111 Town Square Pl Ste 1238", "dest_value": "111 Town Square Pl Ste 1238", "match": "exact", "confidence": 100}},
        {{"field": "City", "source_value": "Jersey City", "dest_value": "Jersey City", "match": "exact", "confidence": 100}},
        {{"field": "State", "source_value": "NJ", "dest_value": "New Jersey", "match": "equivalent", "confidence": 100}},
        {{"field": "Postal Code", "source_value": "07310", "dest_value": "07310", "match": "exact", "confidence": 100}}
    ],
    "missing_data": [],
    "incorrect_data": [],
    "recommendations": [
        "Data transfer appears to be accurate and complete"
    ],
    "confidence": 98,
    "total_fields_identified": 5,
    "fields_transferred_correctly": 5
}}

SCORING GUIDELINES:
- 95-100%: Perfect or near-perfect transfer
- 85-94%: Very good transfer with minor formatting differences
- 70-84%: Good transfer with some issues
- 50-69%: Moderate transfer with several problems
- Below 50%: Poor transfer with major issues

Remember: Focus on DATA ACCURACY, not UI presentation. Be generous with equivalent formats (NJ = New Jersey, etc.)."""

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,  # Low temperature for consistent analysis
                "topK": 1,
                "topP": 1,
                "maxOutputTokens": 2048
            }
        }
        
        try:
            logger.info("Sending data validation request to Gemini API")
            
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Gemini validation API responded successfully")
                
                # Extract and parse the response
                validation_result = self._parse_validation_response(result)
                
                if validation_result:
                    logger.info(f"Validation completed with accuracy: {validation_result.get('accuracy_score', 0)}%")
                    return True, validation_result
                else:
                    logger.error("Failed to parse Gemini validation response")
                    return False, {"error": "Failed to parse validation response"}
                    
            else:
                error_msg = f"Gemini API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, {"error": error_msg}
                
        except requests.exceptions.Timeout:
            error_msg = "Gemini API request timeout"
            logger.error(error_msg)
            return False, {"error": error_msg}
            
        except Exception as e:
            error_msg = f"Gemini validation error: {str(e)}"
            logger.error(error_msg)
            return False, {"error": error_msg}
    
    def _parse_validation_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gemini API response to extract validation result"""
        try:
            if 'candidates' in response and len(response['candidates']) > 0:
                candidate = response['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    if len(parts) > 0 and 'text' in parts[0]:
                        response_text = parts[0]['text'].strip()
                        
                        # Try to extract JSON from the response
                        # Look for JSON block in the response
                        json_start = response_text.find('{')
                        json_end = response_text.rfind('}') + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            json_str = response_text[json_start:json_end]
                            try:
                                parsed_result = json.loads(json_str)
                                
                                # Validate required fields
                                required_fields = ['accuracy_score', 'is_successful_transfer', 'summary']
                                if all(field in parsed_result for field in required_fields):
                                    # Add metadata
                                    parsed_result['processed_at'] = datetime.utcnow().isoformat()
                                    parsed_result['raw_response'] = response_text
                                    return parsed_result
                                else:
                                    logger.warning("Gemini response missing required fields")
                                    
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse JSON from Gemini response: {e}")
                        
                        # Fallback: create a basic result from the text response
                        logger.warning("Could not parse structured JSON, creating fallback result")
                        return self._create_fallback_result(response_text)
            
            logger.error("Unexpected Gemini response structure")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing Gemini validation response: {str(e)}")
            return None
    
    def _create_fallback_result(self, response_text: str) -> Dict[str, Any]:
        """Create a fallback result when JSON parsing fails"""
        
        # Try to extract a score from the text
        score_match = re.search(r'(\d+)%', response_text)
        accuracy_score = int(score_match.group(1)) if score_match else 50
        
        return {
            "accuracy_score": accuracy_score,
            "is_successful_transfer": accuracy_score >= 70,
            "summary": "Validation completed, but detailed analysis not available",
            "matched_data": [],
            "missing_data": [],
            "incorrect_data": [],
            "recommendations": ["Please review the transfer manually for accuracy"],
            "confidence": 60,
            "processed_at": datetime.utcnow().isoformat(),
            "raw_response": response_text,
            "fallback_result": True
        }

# Global instance
gemini_validator = GeminiValidator()