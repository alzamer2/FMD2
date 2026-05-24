"""
String Utilities Module
Equivalent to: uBaseUnit.pas, uStringUtil.pas
Provides common string manipulation functions for Python and Lua.
"""

import os
import re
from html import unescape
from urllib.parse import quote, unquote, urlparse, parse_qs


def pos(sub: str, main_str: str, start: int = 1) -> int:
    """
    Returns the position of a substring (1-based index).
    Equivalent to Pascal Pos() function.
    """
    if not sub or not main_str:
        return 0
    # Adjust for 1-based indexing
    idx = main_str.find(sub, start - 1)
    return idx + 1 if idx != -1 else 0


def copy_str(s: str, start: int, count: int) -> str:
    """
    Returns a substring (1-based start index).
    Equivalent to Pascal Copy() function.
    """
    if start < 1:
        start = 1
    end = start + count - 1
    return s[start - 1:end]


def trim(s: str) -> str:
    """Removes leading and trailing whitespace."""
    return s.strip() if s else ""


def trim_left(s: str) -> str:
    """Removes leading whitespace."""
    return s.lstrip() if s else ""


def trim_right(s: str) -> str:
    """Removes trailing whitespace."""
    return s.rstrip() if s else ""


def lower_case(s: str) -> str:
    """Converts string to lowercase."""
    return s.lower() if s else ""


def upper_case(s: str) -> str:
    """Converts string to uppercase."""
    return s.upper() if s else ""


def extract_filename(path: str) -> str:
    """Extracts filename from path."""
    return os.path.basename(path) if path else ""


def extract_file_ext(path: str) -> str:
    """Extracts file extension from path."""
    _, ext = os.path.splitext(path)
    return ext.lstrip('.') if ext else ""


def extract_filepath(path: str) -> str:
    """Extracts directory path from full path."""
    return os.path.dirname(path) if path else ""


def change_file_ext(path: str, new_ext: str) -> str:
    """Changes file extension."""
    root, _ = os.path.splitext(path)
    if new_ext and not new_ext.startswith('.'):
        new_ext = '.' + new_ext
    return root + new_ext


def string_replace(s: str, old: str, new: str) -> str:
    """Replaces all occurrences of old with new."""
    return s.replace(old, new) if s else ""


def string_contains(s: str, sub: str) -> bool:
    """Checks if string contains substring (case-sensitive)."""
    return sub in s if s else False


def string_starts_with(s: str, prefix: str) -> bool:
    """Checks if string starts with prefix."""
    return s.startswith(prefix) if s else False


def string_ends_with(s: str, suffix: str) -> bool:
    """Checks if string ends with suffix."""
    return s.endswith(suffix) if s else False


def html_decode(s: str) -> str:
    """Decodes HTML entities."""
    return unescape(s) if s else ""


def url_encode(s: str) -> str:
    """URL encodes a string."""
    return quote(s, safe='') if s else ""


def url_decode(s: str) -> str:
    """URL decodes a string."""
    return unquote(s) if s else ""


def get_url_param(url: str, param: str) -> str:
    """Extracts a parameter value from URL query string."""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        values = params.get(param, [])
        return values[0] if values else ""
    except:
        return ""


def between(s: str, start_delim: str, end_delim: str) -> str:
    """
    Extracts text between two delimiters.
    Returns empty string if delimiters not found.
    """
    if not s or not start_delim or not end_delim:
        return ""
    
    start_pos = pos(start_delim, s)
    if start_pos == 0:
        return ""
    
    # Start after the delimiter
    search_start = start_pos + len(start_delim) - 1
    remaining = s[search_start:]
    
    end_pos = pos(end_delim, remaining)
    if end_pos == 0:
        return ""
    
    return copy_str(remaining, 1, end_pos - 1)


def regex_match(pattern: str, text: str) -> list:
    """
    Returns all matches for a regex pattern.
    Returns list of matched strings or groups.
    """
    try:
        matches = re.findall(pattern, text)
        # Flatten if groups are returned
        if matches and isinstance(matches[0], tuple):
            return [m[0] if m else "" for m in matches]
        return matches if matches else []
    except:
        return []


def regex_first(pattern: str, text: str, group: int = 0) -> str:
    """
    Returns first match of regex pattern.
    Optionally returns specific capture group.
    """
    try:
        match = re.search(pattern, text)
        if match:
            if group == 0:
                return match.group(0)
            elif group <= len(match.groups()):
                return match.group(group)
        return ""
    except:
        return ""


class StringUtils:
    """Wrapper class to expose string utilities to Lua."""
    
    @staticmethod
    def pos(sub: str, main_str: str, start: int = 1) -> int:
        return pos(sub, main_str, start)
    
    @staticmethod
    def copy(s: str, start: int, count: int) -> str:
        return copy_str(s, start, count)
    
    @staticmethod
    def trim(s: str) -> str:
        return trim(s)
    
    @staticmethod
    def trim_left(s: str) -> str:
        return trim_left(s)
    
    @staticmethod
    def trim_right(s: str) -> str:
        return trim_right(s)
    
    @staticmethod
    def lower(s: str) -> str:
        return lower_case(s)
    
    @staticmethod
    def upper(s: str) -> str:
        return upper_case(s)
    
    @staticmethod
    def extract_filename(path: str) -> str:
        return extract_filename(path)
    
    @staticmethod
    def extract_file_ext(path: str) -> str:
        return extract_file_ext(path)
    
    @staticmethod
    def extract_filepath(path: str) -> str:
        return extract_filepath(path)
    
    @staticmethod
    def change_file_ext(path: str, new_ext: str) -> str:
        return change_file_ext(path, new_ext)
    
    @staticmethod
    def replace(s: str, old: str, new: str) -> str:
        return string_replace(s, old, new)
    
    @staticmethod
    def contains(s: str, sub: str) -> bool:
        return string_contains(s, sub)
    
    @staticmethod
    def starts_with(s: str, prefix: str) -> bool:
        return string_starts_with(s, prefix)
    
    @staticmethod
    def ends_with(s: str, suffix: str) -> bool:
        return string_ends_with(s, suffix)
    
    @staticmethod
    def html_decode(s: str) -> str:
        return html_decode(s)
    
    @staticmethod
    def url_encode(s: str) -> str:
        return url_encode(s)
    
    @staticmethod
    def url_decode(s: str) -> str:
        return url_decode(s)
    
    @staticmethod
    def get_url_param(url: str, param: str) -> str:
        return get_url_param(url, param)
    
    @staticmethod
    def between(s: str, start: str, end: str) -> str:
        return between(s, start, end)
    
    @staticmethod
    def regex_match(pattern: str, text: str) -> list:
        return regex_match(pattern, text)
    
    @staticmethod
    def regex_first(pattern: str, text: str, group: int = 0) -> str:
        return regex_first(pattern, text, group)


# Register module for Lua
def register(lua_state):
    """Registers string utilities in Lua state."""
    # Create fmd table if it doesn't exist
    lua_state.execute("""
        if not fmd then
            fmd = {}
        end
    """)
    
    # Get globals and set strings table
    lua_globals = lua_state.globals()
    lua_globals.fmd.strings = StringUtils()


if __name__ == "__main__":
    print("Testing String Utilities...")
    
    # Test basic functions
    assert pos("world", "hello world") == 7
    assert copy_str("hello world", 1, 5) == "hello"
    assert trim("  hello  ") == "hello"
    assert lower_case("HELLO") == "hello"
    assert upper_case("hello") == "HELLO"
    
    # Test path functions
    assert extract_filename("/path/to/file.txt") == "file.txt"
    assert extract_file_ext("/path/to/file.txt") == "txt"
    assert extract_filepath("/path/to/file.txt") == "/path/to"
    assert change_file_ext("file.txt", "jpg") == "file.jpg"
    
    # Test string manipulation
    assert string_replace("hello world", "world", "python") == "hello python"
    assert string_contains("hello world", "world") == True
    assert string_starts_with("hello world", "hello") == True
    assert string_ends_with("hello world", "world") == True
    
    # Test HTML/URL
    assert html_decode("&lt;div&gt;") == "<div>"
    assert url_encode("hello world") == "hello%20world"
    assert url_decode("hello%20world") == "hello world"
    
    # Test between
    assert between("<title>My Title</title>", "<title>", "</title>") == "My Title"
    
    # Test regex
    matches = regex_match(r'\d+', "abc123def456")
    assert matches == ["123", "456"]
    assert regex_first(r'(\w+)@(\w+\.\w+)', "email: test@example.com", 1) == "test"
    
    print("✅ All string utility tests passed!")
    print(f"   Tested: pos, copy, trim, case conversion, path ops, replace, html/url encoding, between, regex")
