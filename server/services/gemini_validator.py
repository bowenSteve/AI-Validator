import os
import requests
from typing import Dict, Any, Tuple
import logging
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)

class GeminiValidator:
    """Enhanced Gemini service for human-like data transfer validation"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.timeout = 30
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
    
    def validate_data_transfer(self, source_text: str, destination_text: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Use Gemini to intelligently validate if data was transferred correctly with human-like reasoning
        
        Args:
            source_text: Text extracted from the source image
            destination_text: Text extracted from the destination image
            
        Returns:
            Tuple of (success: bool, result: dict)
        """
        
        # Enhanced prompt for human-like business document validation
        prompt = f"""You are an expert business data validation specialist with human-like reasoning capabilities. Your task is to validate whether data from business documents was correctly transferred into destination systems.

**VALIDATION MISSION:**
Analyze if a user correctly copied data from a source business document into a destination form/system. Focus on catching REAL ERRORS while being contextually intelligent about reasonable formatting differences and partial transfers.

**CRITICAL VALIDATION RULES:**

**1. STRICT ACCURACY REQUIREMENTS (Zero Tolerance):**
- **Company Names**: Must be character-perfect, including punctuation and spacing
  ❌ "ACME CORP" ≠ "ACME CORPORATION" = ERROR (missing letters)
  ❌ "LIGHTNING" ≠ "LIGHTENING" = ERROR (spelling difference)
  ❌ "XYZ L.L.C." ≠ "XYZ LLC" = ERROR (punctuation matters)
  
- **Reference Numbers/IDs**: No truncation allowed, format changes OK
  ❌ "123456789" ≠ "123456" = ERROR (truncated)
  ✅ "123-456-789" = "123456789" = OK (format change only)
  ❌ "ACC-2024-001" ≠ "ACC-2024" = ERROR (incomplete)
  
- **Wrong Information**: Any destination data not found in source
  ❌ Source: "Boston" → Dest: "Boston Springs" = ERROR (added data)
  ❌ Source: "56 Main St" → Dest: "65 Main St" = ERROR (typo)

**2. FLEXIBLE ACCURACY (Context-Aware):**
- **Address Components**: Perfect matches despite formatting differences
  ✅ Source: "85 2nd Street, Suite 710, San Francisco, CA 94105" → Dest: "Address: 85 2nd Street Suite 710, City: San Francisco, State: CALIFORNIA, ZIP: 94105" = PERFECT MATCH (comma differences + CA=CALIFORNIA)
  ✅ Source: "111 Town Square Pl\nSte 1238 885815" → Dest: "111 Town Square Pl Ste 1238 885815" = PERFECT MATCH (formatting difference)
  ❌ Source: "85 2nd Street Suite 710" → Dest: "85 2nd Street" = ERROR (missing suite info from limited source)
  
- **Geographic Data**: State abbreviations are PERFECT equivalents (100% match)
  ✅ "CA" = "CALIFORNIA" = PERFECT MATCH (100% confidence)
  ✅ "NJ" = "NEW JERSEY" = PERFECT MATCH (100% confidence) 
  ✅ "NY" = "NEW YORK" = PERFECT MATCH (100% confidence)
  ✅ "TX" = "TEXAS" = PERFECT MATCH (100% confidence)
  ✅ "FL" = "FLORIDA" = PERFECT MATCH (100% confidence)
  ✅ "St." = "Street" = PERFECT MATCH (standard abbreviations)
  ✅ "Ave" = "Avenue" = PERFECT MATCH
  
- **Phone Numbers**: Format variations acceptable
  ✅ "(555) 123-4567" = "5551234567" = OK (formatting only)
  ✅ "+1-555-123-4567" = "(555) 123-4567" = OK

**3. INTELLIGENT CONTEXT ANALYSIS:**

**Partial Transfer Logic:**
- If source contains comprehensive data (full address with city/state), destination can contain partial data (just street) = ACCEPTABLE
- If source contains limited data, destination must include all available data = REQUIRED
- Business documents often have addresses split across form fields = NORMAL

**Content Priority:**
- **CRITICAL**: Company names, business IDs, account numbers, unique identifiers
- **IMPORTANT**: Complete contact information, reference numbers
- **FLEXIBLE**: Address formatting, phone number formatting, geographic abbreviations
- **IGNORABLE**: Form labels, UI elements, navigation items, field placeholders

**Error Detection Patterns:**
- **Truncation**: "LIGHTNING TRUCKING" → "LIGHTNING TRUCK" = ERROR (word cut off)
- **Spelling Changes**: "LIGHTENING" → "LIGHTNING" = ERROR (different word)
- **Number Errors**: "885815" → "88581" = ERROR (digit missing)
- **Format Only**: "L.L.C." → "LLC" = OK vs "L.L.C." → "L.L" = ERROR (incomplete)

**CRITICAL STATE ABBREVIATION EQUIVALENCIES (Always 100% Match):**
- AL=ALABAMA, AK=ALASKA, AZ=ARIZONA, AR=ARKANSAS, CA=CALIFORNIA, CO=COLORADO
- CT=CONNECTICUT, DE=DELAWARE, FL=FLORIDA, GA=GEORGIA, HI=HAWAII, ID=IDAHO
- IL=ILLINOIS, IN=INDIANA, IA=IOWA, KS=KANSAS, KY=KENTUCKY, LA=LOUISIANA
- ME=MAINE, MD=MARYLAND, MA=MASSACHUSETTS, MI=MICHIGAN, MN=MINNESOTA, MS=MISSISSIPPI
- MO=MISSOURI, MT=MONTANA, NE=NEBRASKA, NV=NEVADA, NH=NEW HAMPSHIRE, NJ=NEW JERSEY
- NM=NEW MEXICO, NY=NEW YORK, NC=NORTH CAROLINA, ND=NORTH DAKOTA, OH=OHIO, OK=OKLAHOMA  
- OR=OREGON, PA=PENNSYLVANIA, RI=RHODE ISLAND, SC=SOUTH CAROLINA, SD=SOUTH DAKOTA, TN=TENNESSEE
- TX=TEXAS, UT=UTAH, VT=VERMONT, VA=VIRGINIA, WA=WASHINGTON, WV=WEST VIRGINIA, WI=WISCONSIN, WY=WYOMING

**4. BIDIRECTIONAL VALIDATION APPROACH:**

**Forward Check (Destination → Source):**
For every piece of data in destination, verify it exists somewhere in source:
- Destination: "ACME CORPORATION" → Must find "ACME CORPORATION" in source ✅
- Destination: "New Jersey" → Can find "NJ" in source ✅
- Destination: "Boston Springs" → Cannot find in source that only shows "Boston" ❌

**Contextual Backward Check (Source → Destination):**
For critical business data in source, check if it appears in destination:
- Company names must appear (exact spelling)
- Important reference numbers should appear
- Address components can be partial if contextually reasonable
- Contact info should appear unless clearly separate fields

**EXAMPLES OF CORRECT VALIDATION:**

**SCENARIO 1 - Perfect Match with State Equivalence:**
Source: "ACME TRUCKING L.L.C.\n123 Main St Suite 500\nBoston, MA 02101"
Destination: "Company: ACME TRUCKING L.L.C., Address: 123 Main St Suite 500, City: Boston, State: MASSACHUSETTS, ZIP: 02101"
= PERFECT MATCH (100% - MA=MASSACHUSETTS is perfect equivalence)

**SCENARIO 2 - Reasonable Partial:**
Source: "LIGHTNING CORP\n456 Oak Ave, Building B, New York, NY 10001"
Destination: "456 Oak Ave Building B"
= ACCEPTABLE (street address complete, city/state likely in separate fields)

**SCENARIO 3 - Critical Error:**
Source: "LIGHTNING TRUCKING L.L.C."
Destination: "LIGHTNING TRUCKING"
= ERROR (company name incomplete, missing legal designation)

**SCENARIO 4 - Perfect Formatting Flexibility:**
Source: "Phone: (555) 123-4567\nCA\n94105"
Destination: "Phone: 5551234567, State: CALIFORNIA, ZIP: 94105"
= PERFECT MATCH (100% - phone formatting + CA=CALIFORNIA perfect equivalence)

**YOUR VALIDATION TASK:**

SOURCE TEXT (Business Document):
{source_text}

DESTINATION TEXT (User Input):
{destination_text}

**ANALYSIS INSTRUCTIONS:**
1. Identify all business data in both source and destination
2. Check every destination value has source origin
3. Verify critical business data (company names, IDs) transferred completely
4. Allow contextually reasonable partial transfers for addresses
5. Flag any data that appears changed, truncated, or added

Respond with a JSON object in this exact format:
{{
    "accuracy_score": 92,
    "is_successful_transfer": true,
    "summary": "Excellent data transfer. Company name and address components correctly transferred with proper formatting flexibility.",
    "matched_data": [
        {{"field": "Company Name", "source_value": "LIGHTNING TRUCKING L.L.C.", "dest_value": "LIGHTNING TRUCKING L.L.C.", "match": "exact", "confidence": 100}},
        {{"field": "Street Address", "source_value": "111 Town Square Pl Ste 1238", "dest_value": "111 Town Square Pl Ste 1238", "match": "exact", "confidence": 100}},
        {{"field": "State", "source_value": "NJ", "dest_value": "New Jersey", "match": "equivalent", "confidence": 100}},
        {{"field": "Phone", "source_value": "(555) 123-4567", "dest_value": "5551234567", "match": "equivalent", "confidence": 100}}
    ],
    "missing_data": [
        {{"field": "ZIP Code", "source_value": "07310", "issue": "Present in source but not found in destination", "severity": "moderate"}}
    ],
    "incorrect_data": [
        {{"field": "Company Name", "source_value": "LIGHTNING TRUCKING L.L.C.", "dest_value": "LIGHTNING TRUCKING", "issue": "Company name incomplete - missing '.L.L.C.' legal designation", "severity": "critical"}}
    ],
    "recommendations": [
        "Verify complete company legal name including all punctuation",
        "Consider adding ZIP code if available in separate field",
        "Data transfer shows good attention to core business information"
    ],
    "confidence": 92,
    "validation_flags": [
        "company_name_critical_check_passed",
        "address_contextually_complete",
        "contact_info_properly_formatted"
    ],
    "total_fields_identified": 6,
    "fields_transferred_correctly": 5,
    "critical_errors": 0,
    "contextual_omissions": 1
}}

**SCORING GUIDELINES:**
- **100%**: Perfect transfer - all data matches exactly OR with perfect equivalencies (CA=CALIFORNIA, phone formatting, etc.)
- **95-99%**: Near-perfect transfer, all critical data intact with minor cosmetic differences
- **85-94%**: Excellent transfer, minor contextual omissions acceptable  
- **70-84%**: Good transfer, some missing data but core information preserved
- **50-69%**: Moderate issues, missing important business information
- **Below 50%**: Significant problems, critical data missing or incorrect

**REMEMBER:**
- Be strict with company names and reference numbers (character-perfect required)
- Be flexible with addresses and formatting (context-aware partial transfers OK)
- Focus on real errors that impact business processes, not cosmetic differences
- Consider the business document context when evaluating completeness
- Flag genuine mistakes while accepting reasonable partial transfers"""

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
            logger.info("Sending request to Gemini API for enhanced data validation")
            
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
            validation_result['validation_approach'] = 'human_like_business_context'
            validation_result['validator_version'] = '2.0_enhanced'
            
            logger.info(f"Enhanced Gemini validation completed with {validation_result.get('accuracy_score', 0)}% accuracy")
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
        success_indicators = ['successful', 'correct', 'accurate', 'good', 'excellent']
        error_indicators = ['error', 'incorrect', 'missing', 'failed', 'wrong']
        
        success_count = sum(1 for indicator in success_indicators if indicator.lower() in response_text.lower())
        error_count = sum(1 for indicator in error_indicators if indicator.lower() in response_text.lower())
        
        is_successful = success_count > error_count or accuracy_score >= 70
        
        return {
            "accuracy_score": accuracy_score,
            "is_successful_transfer": is_successful,
            "summary": "Enhanced validation completed. Manual review recommended for detailed analysis.",
            "matched_data": [],
            "missing_data": [],
            "incorrect_data": [],
            "recommendations": [
                "Enhanced validation processed but detailed breakdown unavailable",
                "Please review the transfer manually for business-critical accuracy",
                "Consider re-processing if validation results seem inconsistent"
            ],
            "confidence": max(accuracy_score - 10, 40),  # Lower confidence for fallback
            "validation_flags": ["fallback_parsing", "manual_review_recommended"],
            "total_fields_identified": 0,
            "fields_transferred_correctly": 0,
            "critical_errors": error_count,
            "contextual_omissions": 0,
            "processed_at": datetime.utcnow().isoformat(),
            "raw_response": response_text,
            "fallback_result": True,
            "validation_approach": "enhanced_fallback",
            "validator_version": "2.0_enhanced"
        }

# Global instance
gemini_validator = GeminiValidator()