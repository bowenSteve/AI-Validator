import re
import difflib
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class TextMatch:
    """Represents a matched text segment between source and destination"""
    source_text: str
    dest_text: str
    match_score: float
    match_type: str  # 'exact', 'similar', 'missing', 'extra'
    line_number: int
    issues: List[str]

@dataclass
class TextValidationResult:
    """Complete text validation result"""
    overall_similarity: float
    total_lines: int
    matched_lines: int
    missing_lines: int
    extra_lines: int
    text_matches: List[TextMatch]
    recommendations: List[str]
    character_accuracy: float
    word_accuracy: float

class SimpleTextComparison:
    """Simple but effective text comparison service"""
    
    def __init__(self):
        self.similarity_threshold = 0.6  # 60% similarity considered a match
        
    def compare_texts(self, source_text: str, dest_text: str) -> TextValidationResult:
        """Compare two text blocks and return detailed results"""
        
        # Clean and normalize texts
        source_clean = self._normalize_text(source_text)
        dest_clean = self._normalize_text(dest_text)
        
        # Split into lines for line-by-line comparison
        source_lines = [line.strip() for line in source_clean.split('\n') if line.strip()]
        dest_lines = [line.strip() for line in dest_clean.split('\n') if line.strip()]
        
        logger.info(f"Comparing {len(source_lines)} source lines with {len(dest_lines)} destination lines")
        
        # Perform line-by-line matching
        text_matches = self._match_lines(source_lines, dest_lines)
        
        # Calculate overall metrics
        matched_lines = len([tm for tm in text_matches if tm.match_score >= self.similarity_threshold])
        missing_lines = len([tm for tm in text_matches if tm.match_type == 'missing'])
        extra_lines = len([tm for tm in text_matches if tm.match_type == 'extra'])
        
        # Calculate overall similarity
        if len(source_lines) == 0 and len(dest_lines) == 0:
            overall_similarity = 100.0
        elif len(source_lines) == 0 or len(dest_lines) == 0:
            overall_similarity = 0.0
        else:
            # Use sequence matcher for overall similarity
            seq_matcher = difflib.SequenceMatcher(None, source_clean, dest_clean)
            overall_similarity = seq_matcher.ratio() * 100
        
        # Calculate character and word accuracy
        char_accuracy = self._calculate_character_accuracy(source_clean, dest_clean)
        word_accuracy = self._calculate_word_accuracy(source_clean, dest_clean)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(text_matches, overall_similarity)
        
        return TextValidationResult(
            overall_similarity=overall_similarity,
            total_lines=max(len(source_lines), len(dest_lines)),
            matched_lines=matched_lines,
            missing_lines=missing_lines,
            extra_lines=extra_lines,
            text_matches=text_matches,
            recommendations=recommendations,
            character_accuracy=char_accuracy,
            word_accuracy=word_accuracy
        )
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better comparison"""
        if not text:
            return ""
        
        # Convert to lowercase for comparison
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common punctuation that might vary
        text = re.sub(r'[,;:!?"]', '', text)
        
        return text.strip()
    
    def _match_lines(self, source_lines: List[str], dest_lines: List[str]) -> List[TextMatch]:
        """Match lines between source and destination"""
        matches = []
        used_dest_indices = set()
        
        # First pass: Find exact and similar matches
        for i, source_line in enumerate(source_lines):
            best_match_idx = -1
            best_score = 0
            
            for j, dest_line in enumerate(dest_lines):
                if j in used_dest_indices:
                    continue
                
                # Calculate similarity
                similarity = self._calculate_line_similarity(source_line, dest_line)
                
                if similarity > best_score and similarity >= self.similarity_threshold:
                    best_score = similarity
                    best_match_idx = j
            
            if best_match_idx >= 0:
                # Found a match
                used_dest_indices.add(best_match_idx)
                match_type = 'exact' if best_score >= 0.95 else 'similar'
                issues = self._identify_line_issues(source_line, dest_lines[best_match_idx])
                
                matches.append(TextMatch(
                    source_text=source_lines[i],
                    dest_text=dest_lines[best_match_idx],
                    match_score=best_score * 100,
                    match_type=match_type,
                    line_number=i + 1,
                    issues=issues
                ))
            else:
                # No match found - missing in destination
                matches.append(TextMatch(
                    source_text=source_lines[i],
                    dest_text="",
                    match_score=0,
                    match_type='missing',
                    line_number=i + 1,
                    issues=["Line missing in destination"]
                ))
        
        # Second pass: Find extra lines in destination
        for j, dest_line in enumerate(dest_lines):
            if j not in used_dest_indices:
                matches.append(TextMatch(
                    source_text="",
                    dest_text=dest_line,
                    match_score=0,
                    match_type='extra',
                    line_number=len(source_lines) + 1,
                    issues=["Extra line not in source"]
                ))
        
        return matches
    
    def _calculate_line_similarity(self, line1: str, line2: str) -> float:
        """Calculate similarity between two lines"""
        if not line1 and not line2:
            return 1.0
        if not line1 or not line2:
            return 0.0
        
        # Use difflib's sequence matcher
        matcher = difflib.SequenceMatcher(None, line1, line2)
        return matcher.ratio()
    
    def _identify_line_issues(self, source_line: str, dest_line: str) -> List[str]:
        """Identify specific issues between two lines"""
        issues = []
        
        # Check for length differences
        if abs(len(source_line) - len(dest_line)) > 10:
            issues.append(f"Length difference: source has {len(source_line)} chars, destination has {len(dest_line)} chars")
        
        # Check for common issues
        source_words = set(source_line.split())
        dest_words = set(dest_line.split())
        
        missing_words = source_words - dest_words
        extra_words = dest_words - source_words
        
        if missing_words:
            issues.append(f"Missing words: {', '.join(list(missing_words)[:3])}")
        
        if extra_words:
            issues.append(f"Extra words: {', '.join(list(extra_words)[:3])}")
        
        return issues
    
    def _calculate_character_accuracy(self, source: str, dest: str) -> float:
        """Calculate character-level accuracy"""
        if not source and not dest:
            return 100.0
        if not source or not dest:
            return 0.0
        
        matcher = difflib.SequenceMatcher(None, source, dest)
        return matcher.ratio() * 100
    
    def _calculate_word_accuracy(self, source: str, dest: str) -> float:
        """Calculate word-level accuracy"""
        source_words = source.split()
        dest_words = dest.split()
        
        if not source_words and not dest_words:
            return 100.0
        if not source_words or not dest_words:
            return 0.0
        
        matcher = difflib.SequenceMatcher(None, source_words, dest_words)
        return matcher.ratio() * 100
    
    def _generate_recommendations(self, matches: List[TextMatch], overall_similarity: float) -> List[str]:
        """Generate helpful recommendations"""
        recommendations = []
        
        missing_count = len([m for m in matches if m.match_type == 'missing'])
        extra_count = len([m for m in matches if m.match_type == 'extra'])
        similar_count = len([m for m in matches if m.match_type == 'similar'])
        
        if overall_similarity >= 95:
            recommendations.append("Excellent! Data transfer appears to be nearly perfect.")
        elif overall_similarity >= 80:
            recommendations.append("Good data transfer with minor differences.")
        elif overall_similarity >= 60:
            recommendations.append("Moderate accuracy - please review the highlighted differences.")
        else:
            recommendations.append("Low accuracy detected - significant differences found.")
        
        if missing_count > 0:
            recommendations.append(f"Review {missing_count} missing line(s) that weren't transferred.")
        
        if extra_count > 0:
            recommendations.append(f"Check {extra_count} extra line(s) that weren't in the original.")
        
        if similar_count > 0:
            recommendations.append(f"Verify {similar_count} line(s) with minor differences for accuracy.")
        
        return recommendations

# Global instance
simple_text_comparison = SimpleTextComparison()