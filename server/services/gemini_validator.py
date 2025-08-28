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
        
        # Enhanced prompt specifically designed for catching partial data extraction
        prompt = f"""You are an expert data validation specialist with deep expertise in OCR analysis and data transfer verification. Your task is to validate whether data was correctly and COMPLETELY transferred from a source document to a destination system.

    VALIDATION CONTEXT:
    - Human taskers extract data from source documents and input it into destination forms
    - Multiple OCR extractions of the same source may yield different results due to image quality, processing variations, or partial reads
    - Your job: Ensure EVERY character of destination data exists in the source AND flag any incomplete/partial extractions
    - This is CRITICAL business validation - accuracy and completeness are paramount

    CORE VALIDATION PRINCIPLES:

    1. **COMPLETE DATA REQUIREMENT**: Every character, number, and word in destination MUST have a complete match in source
    - ❌ Source: "Ste 1238 885815" → Destination: "Ste 1238 88" = PARTIAL EXTRACTION (incomplete)
    - ✅ Source: "Ste 1238 885815" → Destination: "Ste 1238 885815" = COMPLETE MATCH
    - ❌ Source: "LIGHTNING TRUCKING" → Destination: "LIGHTNING TRUCK" = TRUNCATED (incomplete)

    2. **PARTIAL EXTRACTION DETECTION**: Flag when destination appears to be an incomplete version of source data
    - Look for numeric sequences that seem cut off (88 vs 885815)
    - Check for words that appear shortened (TRUCK vs TRUCKING)
    - Identify data that stops mid-sequence or mid-word

    3. **OCR INCONSISTENCY ANALYSIS**: When comparing two extractions of the same source:
    - One extraction may be more complete than the other
    - Flag significant length differences in corresponding fields
    - Prioritize the more complete extraction as the "correct" version

    4. **BUSINESS-CRITICAL FIELD SCRUTINY**: Apply extra validation for:
    - Company/Organization names (every character matters)
    - Addresses with suite/unit numbers (complete sequences required)
    - ID numbers, account numbers, reference numbers
    - Legal entity indicators (L.L.C., Inc., Corp, etc.)

    VALIDATION METHODOLOGY:

    **STEP 1: FIELD-BY-FIELD ANALYSIS**
    For each data field in both source and destination:
    1. Extract the actual data values (ignore labels, UI elements)
    2. Compare character length and completeness
    3. Check if destination field appears truncated compared to source
    4. Verify every character in destination exists in source

    **STEP 2: COMPLETENESS CHECK**
    - Are any destination values suspiciously shorter than their source counterparts?
    - Do numeric sequences end abruptly (88 instead of 885815)?
    - Are company names or addresses missing characters?

    **STEP 3: ERROR CATEGORIZATION**
    - **EXACT**: Perfect character-for-character match
    - **EQUIVALENT**: Same data, different format (NJ = New Jersey)
    - **PARTIAL**: Destination contains incomplete version of source data
    - **INCORRECT**: Destination data doesn't match source (typos, wrong data)
    - **MISSING**: Source data not found in destination at all

    **EXAMPLES OF VALIDATION SCENARIOS:**

    **PARTIAL EXTRACTION (Flag as ERROR):**
    ❌ Source: "111 Town Square Pl Ste 1238 885815" → Dest: "111 Town Square Pl Ste 1238 88"
    Analysis: Suite number "885815" truncated to "88" - PARTIAL EXTRACTION

    ❌ Source: "LIGHTNING TRUCKING L.L.C." → Dest: "LIGHTNING TRUCKING L.L"
    Analysis: Company name cut off - missing ".C." - PARTIAL EXTRACTION

    ❌ Source: "Jersey City" → Dest: "Jersey"
    Analysis: City name incomplete - PARTIAL EXTRACTION

    **COMPLETE MATCHES (Mark as SUCCESS):**
    ✅ Source: "NJ" → Dest: "New Jersey" = EQUIVALENT (state abbreviation)
    ✅ Source: "LIGHTNING TRUCKING L.L.C." → Dest: "LIGHTNING TRUCKING L.L.C." = EXACT
    ✅ Source: "111 Town Square Pl\nSte 1238 885815" → Dest: "111 Town Square Pl Ste 1238 885815" = EXACT (formatting differs but complete)

    **CRITICAL DETECTION PATTERNS:**
    - Numbers that end abruptly: "88" when source shows "885815"
    - Words cut mid-sequence: "TRUCK" when source shows "TRUCKING" 
    - Addresses missing unit numbers or suite details
    - Company names missing legal indicators (L.L.C., Inc., etc.)

    **CONFIDENCE SCORING:**
    - 100%: Perfect matches, all data complete and verified
    - 90-99%: Equivalent formats, all data present with minor formatting differences
    - 70-89%: Minor discrepancies but core data intact
    - 50-69%: Partial extraction detected - some data incomplete
    - Below 50%: Significant data loss or errors

    SOURCE TEXT (Reference document - what tasker should copy FROM):
    {source_text}

    DESTINATION TEXT (Form input - what tasker actually entered):
    {destination_text}

    VALIDATION TASK: 
    Analyze if the destination contains ALL the data from the source. Pay special attention to:
    1. Complete numeric sequences (don't accept partial numbers)
    2. Full company names (don't accept truncated names)
    3. Complete addresses (all components must be present)

    Respond with a JSON object in this exact format:
    {{
        "accuracy_score": 85,
        "is_successful_transfer": true,
        "summary": "Data transfer validation complete. Found 1 partial extraction requiring review.",
        "matched_data": [
            {{"field": "Organization Name", "source_value": "LIGHTNING TRUCKING L.L.C.", "dest_value": "LIGHTNING TRUCKING L.L.C.", "match": "exact", "confidence": 100}},
            {{"field": "Address", "source_value": "111 Town Square Pl Ste 1238 885815", "dest_value": "111 Town Square Pl Ste 1238 88", "match": "partial", "confidence": 60}}
        ],
        "missing_data": [],
        "incorrect_data": [
            {{"field": "Address", "source_value": "111 Town Square Pl Ste 1238 885815", "dest_value": "111 Town Square Pl Ste 1238 88", "issue": "PARTIAL EXTRACTION: Suite number '885815' truncated to '88' - incomplete data entry"}}
        ],
        "recommendations": [
            "Review address field - suite number appears incomplete (88 vs 885815)",
            "Verify complete data extraction for all numeric sequences",
            "Consider re-processing source image for better OCR accuracy"
        ],
        "confidence": 85,
        "validation_flags": [
            "partial_extraction_detected",
            "numeric_sequence_incomplete", 
            "address_component_truncated"
        ]
    }}

    IMPORTANT: 
    - Flag ANY case where destination data appears incomplete compared to source
    - Don't be lenient with partial data - business validation requires completeness
    - When in doubt, flag for human review rather than approving incomplete data
    - Focus on data COMPLETENESS over formatting differences"""

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
            logger.info("Sending request to Gemini API for data validation")
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Make the API request
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                error_msg = f"Gemini API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, {"error": error_msg}
            
            # Parse the response
            api_response = response.json()
            validation_result = self._parse_validation_response(api_response)
            
            if validation_result is None:
                return False, {"error": "Failed to parse Gemini response"}
            
            logger.info("Gemini validation completed successfully")
            return True, validation_result
            
        except requests.exceptions.Timeout:
            error_msg = "Gemini API request timed out"
            logger.error(error_msg)
            return False, {"error": error_msg}
        except requests.exceptions.RequestException as e:
            error_msg = f"Gemini API request failed: {str(e)}"
            logger.error(error_msg)
            return False, {"error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during Gemini validation: {str(e)}"
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