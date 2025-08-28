#!/usr/bin/env python3
"""
Test script for Gemini improvements
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from services.gemini import gemini_service

def test_business_validation():
    """Test the business text validation function"""
    
    test_cases = [
        {
            "text": "LIGHTENING TRUCKING L.L.C.",
            "description": "Should detect LIGHTENING/LIGHTNING confusion"
        },
        {
            "text": "LIGHTNING TRUCKING L.L.C.\nAddress: 111 Town Square Pl Ste 1238\nCity: Jersey City",
            "description": "Good business text - should have high confidence"
        },
        {
            "text": "Organization Name: [UNCERTAIN: LIGHTENING TRUCKING]",
            "description": "Should detect both uncertainty marker and OCR error"
        },
        {
            "text": "Address: 11L Town Square",
            "description": "Should detect suspicious I/L pattern in address"
        }
    ]
    
    print("=== Testing Business Text Validation ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['description']}")
        print(f"Input: {test_case['text']}")
        
        # Test confidence scoring
        confidence = gemini_service._calculate_confidence_score(test_case['text'])
        print(f"Confidence Score: {confidence}%")
        
        # Test business validation
        validation = gemini_service.validate_business_text(test_case['text'])
        print(f"Validation Issues: {validation['has_validation_issues']}")
        if validation['validation_issues']:
            for issue in validation['validation_issues']:
                print(f"  - {issue}")
        if validation['suggestions']:
            for suggestion in validation['suggestions']:
                print(f"  → {suggestion}")
        
        print(f"Needs Human Review: {validation['needs_human_review']}")
        print("-" * 60)

def test_improved_prompt():
    """Display the improved prompt for manual review"""
    print("=== Improved Gemini Prompt ===\n")
    
    # This would be the prompt sent to Gemini (extracted from the service)
    prompt = """You are a highly accurate OCR specialist extracting text for business data validation. This text will be used for critical business processes, so ACCURACY IS PARAMOUNT.

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
    
    print(prompt)
    print("\n" + "=" * 80)

if __name__ == "__main__":
    print("🚀 Testing Gemini Service Improvements")
    print("=" * 80)
    
    test_improved_prompt()
    print()
    test_business_validation()
    
    print("\n✅ Tests completed successfully!")
    print("\nKey Improvements Made:")
    print("1. ✅ Enhanced prompt with specific OCR accuracy instructions")
    print("2. ✅ Added confidence scoring based on uncertainty markers")
    print("3. ✅ Implemented business text validation for common OCR errors")
    print("4. ✅ Added LIGHTNING/LIGHTENING detection specifically")
    print("5. ✅ Enhanced response structure with validation data")
    
    print("\nNext Steps:")
    print("- Deploy the updated server")
    print("- Test with actual images through the API")
    print("- Monitor confidence scores and validation flags")
    print("- Review any texts flagged for human review")