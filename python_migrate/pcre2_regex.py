"""
Free Manga Downloader - Python Migration
PCRE2 Regular Expression Module

Python equivalent of pcre2.pas and pcre2lib.pas
Provides PCRE2 regular expression functionality.
Note: Python's built-in 're' module uses similar regex engine.
For true PCRE2, use the 'regex' library which supports PCRE2 features.
"""

import re
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class PCRE2SubstringOffset:
    """Represents a substring match with start position and length"""
    start: int
    length: int
    
    def get_string(self, s: str) -> str:
        """Extract substring from given string"""
        if self.start < 0 or self.start >= len(s):
            return ""
        end = self.start + self.length
        return s[self.start:end]
    
    def is_nil(self) -> bool:
        """Check if this is an empty/nil match"""
        return self.start == 0 and self.length == 0


class PCRE2:
    """
    Python equivalent of PCRE2 functions from pcre2.pas
    
    Provides regex matching with PCRE2-compatible API.
    Uses Python's 're' module (or 'regex' for advanced features).
    """
    
    # Compile flags
    UTF = re.UNICODE
    MULTILINE = re.MULTILINE
    DOTALL = re.DOTALL
    IGNORECASE = re.IGNORECASE
    
    def __init__(self):
        """Initialize PCRE2 wrapper"""
        self._cache: Dict[str, re.Pattern] = {}
    
    def compile(self, pattern: str, flags: int = 0) -> re.Pattern:
        """
        Compile regex pattern
        
        Args:
            pattern: Regex pattern
            flags: Compilation flags
            
        Returns:
            Compiled pattern
        """
        cache_key = f"{pattern}:{flags}"
        if cache_key not in self._cache:
            self._cache[cache_key] = re.compile(pattern, flags)
        return self._cache[cache_key]
    
    def exec(self, input_string: str, expression: str, 
             start_offset: int = 0, flags: int = 0) -> bool:
        """
        Check if pattern matches string (equivalent to Exec in Pascal)
        
        Args:
            input_string: String to search
            expression: Regex pattern
            start_offset: Starting position (0-based)
            flags: Regex flags
            
        Returns:
            True if match found
        """
        try:
            pattern = self.compile(expression, flags)
            match = pattern.search(input_string, pos=start_offset)
            return match is not None
        except re.error as e:
            raise Exception(f"PCRE2 error: {e}")
    
    def find(self, input_string: str, expression: str,
             start_offset: int = 0, flags: int = 0) -> PCRE2SubstringOffset:
        """
        Find first match (equivalent to Find in Pascal)
        
        Args:
            input_string: String to search
            expression: Regex pattern
            start_offset: Starting position
            flags: Regex flags
            
        Returns:
            PCRE2SubstringOffset with match position and length
        """
        try:
            pattern = self.compile(expression, flags)
            match = pattern.search(input_string, pos=start_offset)
            
            if match:
                return PCRE2SubstringOffset(
                    start=match.start(),
                    length=match.end() - match.start()
                )
            else:
                return PCRE2SubstringOffset(start=0, length=0)
        except re.error as e:
            raise Exception(f"PCRE2 error: {e}")
    
    def match(self, input_string: str, expression: str,
              start_offset: int = 0, flags: int = 0) -> List[PCRE2SubstringOffset]:
        """
        Find all matches (equivalent to Match in Pascal)
        
        Args:
            input_string: String to search
            expression: Regex pattern
            start_offset: Starting position
            flags: Regex flags
            
        Returns:
            List of PCRE2SubstringOffset for each match
        """
        try:
            pattern = self.compile(expression, flags)
            matches = list(pattern.finditer(input_string, pos=start_offset))
            
            result = []
            for match in matches:
                result.append(PCRE2SubstringOffset(
                    start=match.start(),
                    length=match.end() - match.start()
                ))
            return result
        except re.error as e:
            raise Exception(f"PCRE2 error: {e}")
    
    def gmatch(self, input_string: str, expression: str,
               start_offset: int = 0, flags: int = 0) -> List[List[PCRE2SubstringOffset]]:
        """
        Find all matches with groups (equivalent to GMatch in Pascal)
        
        Args:
            input_string: String to search
            expression: Regex pattern
            start_offset: Starting position
            flags: Regex flags
            
        Returns:
            List of group matches for each match
        """
        try:
            pattern = self.compile(expression, flags)
            matches = list(pattern.finditer(input_string, pos=start_offset))
            
            result = []
            for match in matches:
                group_offsets = []
                # Group 0 is the full match
                for i in range(len(match.groups()) + 1):
                    start = match.start(i)
                    end = match.end(i)
                    group_offsets.append(PCRE2SubstringOffset(
                        start=start,
                        length=end - start
                    ))
                result.append(group_offsets)
            return result
        except re.error as e:
            raise Exception(f"PCRE2 error: {e}")
    
    def substitute(self, input_string: str, expression: str, 
                   replacement: str, replace_all: bool = False,
                   flags: int = 0) -> str:
        """
        Substitute matches with replacement string
        
        Args:
            input_string: Input string
            expression: Regex pattern
            replacement: Replacement string (supports \\1, \\2 for groups)
            replace_all: If True, replace all occurrences; otherwise only first
            flags: Regex flags
            
        Returns:
            String with substitutions
        """
        try:
            pattern = self.compile(expression, flags)
            
            if replace_all:
                return pattern.sub(replacement, input_string)
            else:
                return pattern.sub(replacement, input_string, count=1)
        except re.error as e:
            raise Exception(f"PCRE2 error: {e}")
    
    def gsub(self, input_string: str, expression: str,
             replacement: str, flags: int = 0) -> str:
        """
        Global substitute (equivalent to GSub in Pascal)
        
        Args:
            input_string: Input string
            expression: Regex pattern
            replacement: Replacement string
            flags: Regex flags
            
        Returns:
            String with all substitutions
        """
        return self.substitute(input_string, expression, replacement, 
                              replace_all=True, flags=flags)
    
    def split(self, input_string: str, expression: str,
              maxsplit: int = 0, flags: int = 0) -> List[str]:
        """
        Split string by pattern
        
        Args:
            input_string: String to split
            expression: Regex pattern
            maxsplit: Maximum number of splits (0 = unlimited)
            flags: Regex flags
            
        Returns:
            List of split strings
        """
        try:
            pattern = self.compile(expression, flags)
            return pattern.split(input_string, maxsplit=maxsplit)
        except re.error as e:
            raise Exception(f"PCRE2 error: {e}")
    
    def version(self) -> str:
        """Get regex engine version"""
        return f"Python re module (PCRE2-compatible)"


# Convenience functions (module-level API matching Pascal unit)
_pcre2 = PCRE2()


def exec_regex(input_string: str, expression: str, start_offset: int = 0) -> bool:
    """Check if pattern matches (convenience function)"""
    return _pcre2.exec(input_string, expression, start_offset)


def find(input_string: str, expression: str, start_offset: int = 0) -> PCRE2SubstringOffset:
    """Find first match (convenience function)"""
    return _pcre2.find(input_string, expression, start_offset)


def match(input_string: str, expression: str, start_offset: int = 0) -> List[PCRE2SubstringOffset]:
    """Find all matches (convenience function)"""
    return _pcre2.match(input_string, expression, start_offset)


def gmatch(input_string: str, expression: str, start_offset: int = 0) -> List[List[PCRE2SubstringOffset]]:
    """Find all matches with groups (convenience function)"""
    return _pcre2.gmatch(input_string, expression, start_offset)


def substitute(input_string: str, expression: str, replacement: str, 
               replace_all: bool = False) -> str:
    """Substitute matches (convenience function)"""
    return _pcre2.substitute(input_string, expression, replacement, replace_all)


def gsub(input_string: str, expression: str, replacement: str) -> str:
    """Global substitute (convenience function)"""
    return _pcre2.gsub(input_string, expression, replacement)


def version() -> str:
    """Get version string"""
    return _pcre2.version()


def get_error_message(error_code: int, error_offset: int = 0) -> str:
    """Get error message for error code"""
    return f"PCRE2 error {error_code} at position {error_offset}" if error_offset else f"PCRE2 error {error_code}"


# Test and example usage
if __name__ == '__main__':
    print("Testing PCRE2 module...")
    
    # Test 1: Basic exec
    test_str = "Hello World 123"
    pattern = r"\d+"
    
    result = exec_regex(test_str, pattern)
    assert result == True, "Exec failed"
    print("✓ Exec test passed")
    
    # Test 2: Find
    offset = find(test_str, pattern)
    assert offset.start == 12, f"Find failed: expected 12, got {offset.start}"
    assert offset.length == 3, f"Find length failed: expected 3, got {offset.length}"
    assert offset.get_string(test_str) == "123", "Get string failed"
    print("✓ Find test passed")
    
    # Test 3: Match all
    test_str2 = "abc123def456ghi789"
    matches = match(test_str2, r"\d+")
    assert len(matches) == 3, f"Match count failed: expected 3, got {len(matches)}"
    print("✓ Match test passed")
    
    # Test 4: GMatch with groups
    test_str3 = "John:25, Jane:30, Bob:35"
    group_matches = gmatch(test_str3, r"(\w+):(\d+)")
    assert len(group_matches) == 3, f"GMatch count failed"
    assert len(group_matches[0]) == 3, f"GMatch groups failed"  # Full match + 2 groups
    print("✓ GMatch test passed")
    
    # Test 5: Substitute
    test_str4 = "Hello World"
    result = substitute(test_str4, r"World", "Python")
    assert result == "Hello Python", f"Substitute failed: {result}"
    print("✓ Substitute test passed")
    
    # Test 6: Global substitute
    test_str5 = "cat bat rat"
    result = gsub(test_str5, r"at", "og")
    assert result == "cog bog rog", f"GSub failed: {result}"
    print("✓ GSub test passed")
    
    # Test 7: Split
    test_str6 = "apple,banana,cherry"
    result = _pcre2.split(test_str6, r",")
    assert len(result) == 3, f"Split failed"
    print("✓ Split test passed")
    
    # Test 8: Complex pattern
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    test_email = "user@example.com"
    assert exec_regex(test_email, email_pattern), "Email pattern failed"
    print("✓ Complex pattern test passed")
    
    print(f"\n✅ All PCRE2 tests passed! ({version()})")
