import os
import requests
from typing import Dict, Any, Tuple
import logging
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)

class GeminiValidator:
    """Enhanced Gemini service for human-like data transfer validation with perfect address recognition"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.timeout = 30
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
    
    def validate_data_transfer(self, source_text: str, destination_text: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Use Gemini to intelligently validate if data was transferred correctly with perfect address recognition
        
        Args:
            source_text: Text extracted from the source image
            destination_text: Text extracted from the destination image
            
        Returns:
            Tuple of (success: bool, result: dict)
        """
        
        # Enhanced prompt with perfect address recognition
        prompt = f"""You are an expert business data validation specialist with precise address recognition capabilities. Your task is to validate whether data from business documents was correctly transferred into destination systems.

**VALIDATION MISSION:**
Analyze if a user correctly copied data from a source business document into a destination form/system. Focus on catching REAL ERRORS while being contextually intelligent about perfect equivalencies and field decomposition.

**CRITICAL VALIDATION RULES:**

**1. PERFECT EQUIVALENCIES (Always 100% Match - Treat as EXACT):**
These are NOT formatting differences - these are PERFECT EQUIVALENTS that must score 100%:

**A. State Abbreviations ↔ Full Names (100% Perfect Match):**
✅ "CA" = "CALIFORNIA" = 100% EXACT EQUIVALENT (NEVER 98% or 95%)
✅ "NJ" = "NEW JERSEY" = 100% EXACT EQUIVALENT
✅ "NY" = "NEW YORK" = 100% EXACT EQUIVALENT  
✅ "TX" = "TEXAS" = 100% EXACT EQUIVALENT
✅ "FL" = "FLORIDA" = 100% EXACT EQUIVALENT
✅ "MA" = "MASSACHUSETTS" = 100% EXACT EQUIVALENT
✅ All 50 US state abbreviations = their full names = 100% EXACT EQUIVALENT

**B. Address Component Decomposition (100% Perfect Match):**
✅ Source: "85 2nd Street, Suite 710, San Francisco, CA 94105"
✅ Destination: "Address 1: 85 2nd Street Suite 710, City: San Francisco, State: CALIFORNIA, ZIP: 94105"
✅ **RESULT: 100% PERFECT MATCH** (comma removal + field separation + CA=CALIFORNIA all perfect)

✅ Source: "111 Town Square Pl\nSte 1238\nJersey City, NJ 07310"  
✅ Destination: "Street: 111 Town Square Pl Ste 1238, City: Jersey City, State: NEW JERSEY, ZIP: 07310"
✅ **RESULT: 100% PERFECT MATCH** (line combination + NJ=NEW JERSEY perfect)

**C. Standard Business Formatting (100% Perfect Match):**
✅ "L.L.C." = "LLC" = 100% EXACT (standard business abbreviation)
✅ "(555) 123-4567" = "5551234567" = 100% EXACT (phone formatting)
✅ "St." = "Street", "Ave" = "Avenue", "Ste" = "Suite" = 100% EXACT

**2. ADDRESS VALIDATION INTELLIGENCE:**

**Complete Address Reconstruction Rule:**
If destination address components can be perfectly reconstructed from source data using field decomposition and perfect equivalencies, score = 100%

**Example Analysis Process:**
Source: "85 2nd Street, Suite 710, San Francisco, CA 94105"
Destination Analysis:
- "85 2nd Street Suite 710" ← "85 2nd Street, Suite 710" ✅ 100% (comma removal)
- "San Francisco" ← "San Francisco" ✅ 100% (exact)  
- "CALIFORNIA" ← "CA" ✅ 100% (perfect state equivalent)
- "94105" ← "94105" ✅ 100% (exact)
**FINAL ADDRESS SCORE: 100% PERFECT MATCH**

**3. ERROR DETECTION (Real Problems Only):**
❌ **Spelling Changes**: "LIGHTNING" ≠ "LIGHTENING" = ERROR
❌ **Number Changes**: "85 2nd Street" ≠ "86 2nd Street" = ERROR  
❌ **Missing Data**: Source has "Suite 710" but destination missing = ERROR
❌ **Added Data**: Destination has data not in source = ERROR

**4. COMPREHENSIVE STATE EQUIVALENCIES (All 100% Perfect):**
CA=CALIFORNIA, TX=TEXAS, NY=NEW YORK, FL=FLORIDA, IL=ILLINOIS, PA=PENNSYLVANIA, 
OH=OHIO, GA=GEORGIA, NC=NORTH CAROLINA, MI=MICHIGAN, NJ=NEW JERSEY, VA=VIRGINIA,
WA=WASHINGTON, AZ=ARIZONA, MA=MASSACHUSETTS, TN=TENNESSEE, IN=INDIANA, MO=MISSOURI,
MD=MARYLAND, WI=WISCONSIN, CO=COLORADO, MN=MINNESOTA, SC=SOUTH CAROLINA, AL=ALABAMA,
LA=LOUISIANA, KY=KENTUCKY, OR=OREGON, OK=OKLAHOMA, CT=CONNECTICUT, IA=IOWA,
MS=MISSISSIPPI, AR=ARKANSAS, KS=KANSAS, UT=UTAH, NV=NEVADA, NM=NEW MEXICO,
WV=WEST VIRGINIA, NE=NEBRASKA, ID=IDAHO, HI=HAWAII, NH=NEW HAMPSHIRE, ME=MAINE,
RI=RHODE ISLAND, MT=MONTANA, DE=DELAWARE, SD=SOUTH DAKOTA, ND=NORTH DAKOTA,
AK=ALASKA, VT=VERMONT, WY=WYOMING

**5. VALIDATION APPROACH:**

**Forward Validation (Destination → Source):**
For every piece of data in destination, verify it can be found/reconstructed from source using:
1. Exact matches
2. Perfect equivalencies (state abbreviations, business formatting)
3. Field decomposition (splitting combined fields)
4. Punctuation normalization

**Critical Business Data Priority:**
- Company names: Must be exact (after punctuation normalization)
- Contact info: Must be exact (after formatting normalization)
- Addresses: Must be perfectly reconstructable (using equivalencies)

**SCORING GUIDELINES:**
- **100%**: All destination data perfectly reconstructable from source (including perfect equivalencies)
- **95-99%**: Near-perfect with very minor cosmetic differences
- **85-94%**: Good transfer with some formatting variations
- **70-84%**: Adequate transfer with some missing/incorrect data
- **Below 70%**: Significant problems requiring review

**CRITICAL INSTRUCTION:**
When you see state abbreviations matched with full names (CA=CALIFORNIA), field decomposition (comma-separated address split into fields), or standard business formatting differences, these are 100% PERFECT MATCHES, not 95-98% matches.

**YOUR VALIDATION TASK:**

SOURCE TEXT (Business Document):
{source_text}

DESTINATION TEXT (User Input):
{destination_text}

Analyze the data transfer and respond with a JSON object in this exact format:
{{
    "accuracy_score": 100,
    "is_successful_transfer": true,
    "summary": "Perfect data transfer. All address components correctly transferred with perfect equivalencies recognized.",
    "matched_data": [
        {{"field": "Organization Name", "source_value": "Middesk, Inc.", "dest_value": "Middesk, Inc.", "match": "exact", "confidence": 100}},
        {{"field": "Complete Address", "source_value": "85 2nd Street, Suite 710, San Francisco, CA 94105", "dest_value": "85 2nd Street Suite 710 + San Francisco + CALIFORNIA + 94105", "match": "exact", "confidence": 100}},
        {{"field": "Email", "source_value": "fulfillment@middesk.com", "dest_value": "fulfillment@middesk.com", "match": "exact", "confidence": 100}},
        {{"field": "Phone", "source_value": "4422182550", "dest_value": "4422182550", "match": "exact", "confidence": 100}}
    ],
    "missing_data": [],
    "incorrect_data": [],
    "recommendations": [
        "Perfect data transfer with all address components correctly identified",
        "State abbreviation to full name conversion recognized as perfect equivalency",
        "Address field decomposition completed successfully",
        "All business-critical information transferred accurately"
    ],
    "confidence": 100,
    "validation_flags": [
        "perfect_address_reconstruction",
        "state_abbreviation_perfect_equivalent",
        "field_decomposition_successful",
        "all_business_data_complete"
    ],
    "total_fields_identified": 4,
    "fields_transferred_correctly": 4,
    "critical_errors": 0,
    "contextual_omissions": 0
}}

**FINAL CRITICAL REMINDER:**
- CA = CALIFORNIA is 100% EXACT, never score below 100%
- Address decomposition is 100% EXACT if all components found
- Comma/punctuation removal is 100% EXACT, never a penalty
- Perfect equivalencies must be recognized as EXACT matches, not equivalent matches"""

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
            logger.info("Sending request to Gemini API for enhanced address validation")
            
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
            
            # Add enhanced metadata
            validation_result['validation_approach'] = 'perfect_address_recognition'
            validation_result['validator_version'] = '3.0_address_enhanced'
            
            logger.info(f"Enhanced address validation completed with {validation_result.get('accuracy_score', 0)}% accuracy")
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
                        json_start = response_text.find('{')
                        json_end = response_text.rfind('}') + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            json_str = response_text[json_start:json_end]
                            try:
                                parsed_result = json.loads(json_str)
                                
                                # Validate required fields
                                required_fields = ['accuracy_score', 'is_successful_transfer', 'summary']
                                if all(field in parsed_result for field in required_fields):
                                    # Add enhanced metadata
                                    parsed_result['processed_at'] = datetime.utcnow().isoformat()
                                    parsed_result['raw_response'] = response_text
                                    
                                    # Ensure all expected fields exist with defaults
                                    defaults = {
                                        'matched_data': [],
                                        'missing_data': [],
                                        'incorrect_data': [],
                                        'recommendations': [],
                                        'confidence': parsed_result.get('accuracy_score', 50),
                                        'validation_flags': [],
                                        'total_fields_identified': 0,
                                        'fields_transferred_correctly': 0,
                                        'critical_errors': 0,
                                        'contextual_omissions': 0
                                    }
                                    
                                    for key, default_value in defaults.items():
                                        if key not in parsed_result:
                                            parsed_result[key] = default_value
                                    
                                    return parsed_result
                                else:
                                    logger.warning("Gemini response missing required fields")
                                    
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse JSON from Gemini response: {e}")
                        
                        # Fallback: create a basic result from the text response
                        logger.warning("Could not parse structured JSON, creating enhanced fallback result")
                        return self._create_enhanced_fallback_result(response_text)
            
            logger.error("Unexpected Gemini response structure")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing Gemini validation response: {str(e)}")
            return None

    def _create_enhanced_fallback_result(self, response_text: str) -> Dict[str, Any]:
        """Create an enhanced fallback result when JSON parsing fails"""
        
        # Try to extract a score from the text
        score_match = re.search(r'(\d+)%', response_text)
        accuracy_score = int(score_match.group(1)) if score_match else 60
        
        # Look for success indicators in the text
        success_indicators = ['successful', 'correct', 'accurate', 'good', 'excellent', 'perfect']
        error_indicators = ['error', 'incorrect', 'missing', 'failed', 'wrong']
        
        success_count = sum(1 for indicator in success_indicators if indicator.lower() in response_text.lower())
        error_count = sum(1 for indicator in error_indicators if indicator.lower() in response_text.lower())
        
        # Check for address-specific success indicators
        address_perfect_indicators = ['perfect address', 'address perfect', 'state abbreviation', 'CALIFORNIA', 'perfect match']
        address_perfect_count = sum(1 for indicator in address_perfect_indicators if indicator in response_text)
        
        # If we see address perfection indicators, boost the score
        if address_perfect_count > 0 and accuracy_score < 100:
            accuracy_score = min(100, accuracy_score + 10)
        
        is_successful = success_count > error_count or accuracy_score >= 90
        
        return {
            "accuracy_score": accuracy_score,
            "is_successful_transfer": is_successful,
            "summary": "Enhanced address validation completed. Perfect equivalencies should be recognized as 100% matches.",
            "matched_data": [],
            "missing_data": [],
            "incorrect_data": [],
            "recommendations": [
                "Enhanced validation processed with improved address recognition",
                "State abbreviations should be treated as perfect equivalents (100%)",
                "Address field decomposition should score 100% when all components found",
                "Consider manual review if validation results seem inconsistent"
            ],
            "confidence": max(accuracy_score - 5, 50),
            "validation_flags": ["enhanced_address_logic", "perfect_equivalency_enabled", "manual_review_recommended"],
            "total_fields_identified": 0,
            "fields_transferred_correctly": 0,
            "critical_errors": error_count,
            "contextual_omissions": 0,
            "processed_at": datetime.utcnow().isoformat(),
            "raw_response": response_text,
            "fallback_result": True,
            "validation_approach": "enhanced_address_fallback",
            "validator_version": "3.0_address_perfect"
        }

# Global instance
gemini_validator = GeminiValidator()