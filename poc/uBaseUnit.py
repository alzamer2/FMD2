"""
Base Utilities Module - Python equivalent of uBaseUnit.pas

This module provides core utility functions for Free Manga Downloader,
including string manipulation, URL handling, HTML decoding, file operations,
and data structures.

License: GPLv2
"""

import os
import re
import sys
import html
import base64
import hashlib
import random
import string
import datetime
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from urllib.parse import urlparse, urljoin, quote, unquote
from collections import OrderedDict

# Import local modules
from string_utils import (
    pos, copy_str, trim, trim_left, trim_right,
    lower_case as lowercase, upper_case as uppercase, 
    string_replace, string_contains
)

# Helper functions not in string_utils
def int_to_str(n: int) -> str:
    """Convert integer to string."""
    return str(n)

def str_to_int(s: str, default: int = 0) -> int:
    """Convert string to integer with default."""
    try:
        return int(s)
    except (ValueError, TypeError):
        return default

def is_integer(s: str) -> bool:
    """Check if string is an integer."""
    try:
        int(s)
        return True
    except (ValueError, TypeError):
        return False


# ============================================================================
# CONSTANTS
# ============================================================================

UTF8_BOM = '\ufeff'

DATA_PARAM_LINK = 0
DATA_PARAM_TITLE = 1
DATA_PARAM_ALTTITLES = 2
DATA_PARAM_AUTHORS = 3
DATA_PARAM_ARTISTS = 4
DATA_PARAM_GENRES = 5
DATA_PARAM_STATUS = 6
DATA_PARAM_SUMMARY = 7
DATA_PARAM_NUMCHAPTER = 8
DATA_PARAM_JDN = 9

FILTER_HIDE = 0
FILTER_SHOW = 1

DEFAULT_GENRES = [
    'Action', 'Adult', 'Adventure', 'Comedy', 'Doujinshi', 'Drama', 'Ecchi',
    'Fantasy', 'Gender Bender', 'Harem', 'Hentai', 'Historical', 'Horror',
    'Josei', 'Lolicon', 'Martial Arts', 'Mature', 'Mecha', 'Musical',
    'Mystery', 'Psychological', 'Romance', 'School Life', 'Sci-fi', 'Seinen',
    'Shotacon', 'Shoujo', 'Shoujo Ai', 'Shounen', 'Shounen Ai', 'Slice of Life',
    'Smut', 'Sports', 'Supernatural', 'Tragedy', 'Yaoi', 'Yuri', 'Webtoons'
]

INVALID_FILENAME_CHARS = set('\\/:*?"<>|\t;')

HTML_ENTITIES_CHAR = [
    ['&#171;', '«'], ['&#176;', '°'], ['&Agrave;', 'À'], ['&#192;', 'À'],
    ['&Aacute;', 'Á'], ['&#193;', 'Á'], ['&Acirc;', 'Â'], ['&Atilde;', 'Ã'],
    ['&ccedil;', 'ç'], ['&Egrave;', 'È'], ['&Eacute;', 'É'], ['&Ecirc;', 'Ê'],
    ['&#202;', 'Ê'], ['&Etilde;', 'Ẽ'], ['&Igrave;', 'Ì'], ['&Iacute;', 'Í'],
    ['&Itilde;', 'Ĩ'], ['&ETH;', 'Đ'], ['&Ograve;', 'Ò'], ['&Oacute;', 'Ó'],
    ['&Ocirc;', 'Ô'], ['&#212;', 'Ô'], ['&Otilde;', 'Õ'], ['&Ugrave;', 'Ù'],
    ['&Uacute;', 'Ú'], ['&Yacute;', 'Ý'], ['&#221;', 'Ý'], ['&agrave;', 'à'],
    ['&#224;', 'à'], ['&aacute;', 'á'], ['&#225;', 'á'], ['&acirc;', 'â'],
    ['&#226;', 'â'], ['&atilde;', 'ã'], ['&#227;', 'ã'], ['&#231;', 'ç'],
    ['&egrave;', 'è'], ['&#232;', 'è'], ['&eacute;', 'é'], ['&#233;', 'é'],
    ['&etilde;', 'ẽ'], ['&ecirc;', 'ê'], ['&#234;', 'ê'], ['&igrave;', 'ì'],
    ['&#236;', 'ì'], ['&iacute;', 'í'], ['&#237;', 'í'], ['&itilde;', 'ĩ'],
    ['&#238;', 'î'], ['&eth;', 'đ'], ['&ograve;', 'ò'], ['&#242;', 'ò'],
    ['&oacute;', 'ó'], ['&#243;', 'ó'], ['&ocirc;', 'ô'], ['&#244;', 'ô'],
    ['&otilde;', 'õ'], ['&#245;', 'õ'], ['&ugrave;', 'ù'], ['&#249;', 'ù'],
    ['&uacute;', 'ú'], ['&#250;', 'ú'], ['&yacute;', 'ý'], ['&#253;', 'ý'],
    ['&#8217;', "'"], ['&#8220;', '"'], ['&#8221;', '"'], ['&#8230;', '...'],
    ['&Auml;', 'Ä'], ['&auml;', 'ä'], ['&Ouml;', 'Ö'], ['&ouml;', 'ö'],
    ['&Uuml;', 'Ü'], ['&uuml;', 'ü'], ['&szlig;', 'ß'], ['&mu;', 'μ'],
    ['&#956;', 'μ'], ['&raquo;', '»'], ['&laquo;', '«'], ['&#8216;', '‘'],
    ['&ndash;', '-'], ['&gamma;', 'γ']
]

STRING_FILTER_CHAR = [
    ['\n', '\\n'], ['\r', '\\r'], ['&#x27;', "'"], ['&#33;', '!'],
    ['&#36;', '$'], ['&#37;', '%'], ['&#38;', '&'], ['&#39;', "'"],
    ['&#033;', '!'], ['&#036;', '$'], ['&#037;', '%'], ['&#038;', '&'],
    ['&#039;', "'"], ['&#8211;', '-'], ['&gt;', '>'], ['&lt;', '<'],
    ['&amp;', '&'], ['&ldquo;', '"'], ['&rdquo;', '"'], ['&quot;', '"'],
    ['&lsquo;', "'"], ['&rsquo;', "'"], ['&nbsp;', ' '], ['&cent;', '¢'],
    ['&pound;', '£'], ['&yen;', '¥'], ['&euro;', '©'], ['&copy;', '€'],
    ['&reg;', '®'], ['［', '['], ['］', ']'], ['（', '('], ['）', ')'],
    ['&frac12;', '½'], ['&deg;', '°'], ['&sup2;', '²']
]

ALPHA_LIST = '#abcdefghijklmnopqrstuvwxyz'
ALPHA_LIST_UP = '#ABCDEFGHIJKLMNOPQRSTUVWXYZ'

MANGA_INFO_STATUS_COMPLETED = '0'
MANGA_INFO_STATUS_ONGOING = '1'
MANGA_INFO_STATUS_HIATUS = '2'
MANGA_INFO_STATUS_CANCELLED = '3'

FMD_SUPPORTED_PACKED_OUTPUT_EXT = ['.zip', '.cbz', '.pdf', '.epub']

# Windows-specific constants (for compatibility)
MAX_PATHDIR = 247
FMD_MAX_IMAGE_FILE_PATH = 255

# Custom rename placeholders
CR_NUMBERING = '%NUMBERING%'
CR_CHAPTER = '%CHAPTER%'
CR_WEBSITE = '%WEBSITE%'
CR_MANGA = '%MANGA%'
CR_AUTHOR = '%AUTHOR%'
CR_ARTIST = '%ARTIST%'
CR_FILENAME = '%FILENAME%'

# Common regex for host/url splitting
REGEX_HOST = r'(?i)^(\w+://)?([^/]*\.\w+)?(:\d+)?(/?.*)$'


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class MangaListItem:
    """Represents a manga list item with text and Julian Day Number."""
    def __init__(self, text: str = '', jdn: int = 0):
        self.text = text
        self.jdn = jdn


class SingleItem:
    """Simple item with text."""
    def __init__(self, text: str = ''):
        self.text = text


class NamePointerItem:
    """Item with name and pointer reference."""
    def __init__(self, name: str = '', p: Any = None):
        self.name = name
        self.p = p


class ChapterStateItem:
    """Chapter state information."""
    def __init__(self, index: int = 0, title: str = '', link: str = '', downloaded: bool = False):
        self.index = index
        self.title = title
        self.link = link
        self.downloaded = downloaded


class BaseMangaInfo:
    """Basic manga information structure."""
    def __init__(self):
        self.title = ''
        self.alttitles = ''
        self.authors = ''
        self.artists = ''
        self.genres = ''
        self.status = ''
        self.summary = ''
        self.num_chapter = 0


class MangaInfo:
    """Complete manga information class."""
    def __init__(self):
        self.url = ''
        self.title = ''
        self.alt_titles = ''
        self.link = ''
        self.cover_link = ''
        self.authors = ''
        self.artists = ''
        self.genres = ''
        self.status = ''
        self.summary = ''
        self.num_chapter = 0
        self.chapter_names: List[str] = []
        self.chapter_links: List[str] = []
        self.module = None  # Pointer to module
    
    def module_id(self) -> str:
        """Get module ID from module."""
        if self.module and hasattr(self.module, 'id'):
            return str(self.module.id)
        return ''
    
    def website(self) -> str:
        """Get website name from module."""
        if self.module and hasattr(self.module, 'name'):
            return str(self.module.name)
        return ''
    
    def full_link(self) -> str:
        """Get full URL by combining host and link."""
        return fill_host('', self.link)
    
    def clear(self):
        """Clear all fields."""
        self.url = ''
        self.title = ''
        self.alt_titles = ''
        self.link = ''
        self.cover_link = ''
        self.authors = ''
        self.artists = ''
        self.genres = ''
        self.status = ''
        self.summary = ''
        self.num_chapter = 0
        self.chapter_names.clear()
        self.chapter_links.clear()
        self.module = None
    
    def clone(self) -> 'MangaInfo':
        """Create a deep copy of this MangaInfo."""
        clone = MangaInfo()
        clone.url = self.url
        clone.title = self.title
        clone.alt_titles = self.alt_titles
        clone.link = self.link
        clone.cover_link = self.cover_link
        clone.authors = self.authors
        clone.artists = self.artists
        clone.genres = self.genres
        clone.status = self.status
        clone.summary = self.summary
        clone.num_chapter = self.num_chapter
        clone.chapter_names = self.chapter_names.copy()
        clone.chapter_links = self.chapter_links.copy()
        clone.module = self.module
        return clone


class MangaCheck:
    """Manga check information for monitoring updates."""
    def __init__(self):
        self.manga_url = ''
        self.manga_title = ''
        self.chapter_url = ''
        self.chapter_title = ''
        self.chapter_url_prefix = ''
        self.test_to_check = 0
        self.manga_url_add_root_host = False
        self.chapter_url_add_root_host = False
        self.module = None
    
    def module_id(self) -> str:
        if self.module and hasattr(self.module, 'id'):
            return str(self.module.id)
        return ''
    
    def module_name(self) -> str:
        if self.module and hasattr(self.module, 'name'):
            return str(self.module.name)
        return ''
    
    def module_filename(self) -> str:
        if self.module and hasattr(self.module, 'filename'):
            return str(self.module.filename)
        return ''
    
    def clear(self):
        """Clear all fields."""
        self.manga_url = ''
        self.manga_title = ''
        self.chapter_url = ''
        self.chapter_title = ''
        self.chapter_url_prefix = ''
        self.test_to_check = 0
        self.manga_url_add_root_host = False
        self.chapter_url_add_root_host = False
        self.module = None
    
    def clone(self) -> 'MangaCheck':
        """Create a deep copy."""
        clone = MangaCheck()
        clone.manga_url = self.manga_url
        clone.manga_title = self.manga_title
        clone.chapter_url = self.chapter_url
        clone.chapter_title = self.chapter_title
        clone.chapter_url_prefix = self.chapter_url_prefix
        clone.test_to_check = self.test_to_check
        clone.manga_url_add_root_host = self.manga_url_add_root_host
        clone.chapter_url_add_root_host = self.chapter_url_add_root_host
        clone.module = self.module
        return clone


class DownloadInfo:
    """Download task information."""
    def __init__(self):
        self.link = ''
        self.title = ''
        self.save_to = ''
        self.status = ''
        self.progress = ''
        self.transfer_rate = ''
        self.date_added = datetime.datetime.now()
        self.date_last_downloaded = datetime.datetime.now()
        self.i_progress = 0
        self.manga_ptr = None
        self._module = None
        self._module_id = ''
    
    @property
    def module(self):
        return self._module
    
    @module.setter
    def module(self, value):
        self._module = value
        if value and hasattr(value, 'id'):
            self._module_id = str(value.id)
    
    @property
    def module_id(self):
        return self._module_id
    
    @module_id.setter
    def module_id(self, value):
        self._module_id = value
    
    def website(self) -> str:
        """Get website name from module."""
        if self._module and hasattr(self._module, 'name'):
            return str(self._module.name)
        return ''


class FavoriteInfo:
    """Favorite manga information."""
    def __init__(self):
        self.manga_url = ''
        self.manga_title = ''
        self.root_url = ''
        self.last_chapter = ''
        self.current_chapter = ''
        self.chapter_list: List[str] = []
        self.status = ''
        self.date_added = datetime.datetime.now()
        self.date_last_checked = datetime.datetime.now()
        self.check_interval = 0
        self.enabled = True
        self._module = None
        self._module_id = ''
    
    @property
    def module(self):
        return self._module
    
    @module.setter
    def module(self, value):
        self._module = value
        if value and hasattr(value, 'id'):
            self._module_id = str(value.id)
    
    @property
    def module_id(self):
        return self._module_id
    
    @module_id.setter
    def module_id(self, value):
        self._module_id = value
    
    def website(self) -> str:
        if self._module and hasattr(self._module, 'name'):
            return str(self._module.name)
        return ''


class HTMLForm:
    """HTML form data handler."""
    def __init__(self):
        self.data: Dict[str, str] = {}
    
    def put(self, name: str, value: str):
        """Add or update form field."""
        self.data[name] = value
    
    def remove(self, name: str):
        """Remove form field."""
        if name in self.data:
            del self.data[name]
    
    def get_data(self) -> str:
        """Get form data as URL-encoded string."""
        return '&'.join(f'{quote(k)}={quote(v)}' for k, v in self.data.items())
    
    def clear(self):
        """Clear all form fields."""
        self.data.clear()


# ============================================================================
# STRING MANIPULATION FUNCTIONS
# ============================================================================

def replace_unicode_char(s: str, replace_str: str = '_') -> str:
    """Replace non-ASCII characters with a replacement string."""
    return ''.join(c if ord(c) < 128 else replace_str for c in s)


def correct_file_path(path: str) -> str:
    """Correct invalid characters in file path."""
    result = path
    for char in INVALID_FILENAME_CHARS:
        result = result.replace(char, '_')
    # Remove control characters
    result = ''.join(c for c in result if ord(c) >= 32)
    return result.strip()


def correct_url(url: str) -> str:
    """Correct URL encoding issues."""
    # Decode then re-encode properly
    try:
        decoded = unquote(url)
        return quote(decoded, safe=':/?&=#')
    except:
        return url


def check_path(path: str):
    """Ensure directory exists, create if not."""
    os.makedirs(path, exist_ok=True)


def fill_url_protocol(protocol: str, url: str) -> str:
    """Add protocol to URL if missing."""
    if not url:
        return url
    if not url.startswith('http://') and not url.startswith('https://'):
        if protocol and not protocol.endswith('://'):
            protocol += '://'
        return f'{protocol}{url}'
    return url


def fill_host(host: str, url: str) -> str:
    """Fill host into URL if URL is relative."""
    if not url:
        return url
    if url.startswith('http://') or url.startswith('https://'):
        return url
    if url.startswith('//'):
        return 'https:' + url
    return urljoin(host, url)


def fill_hosts(host: str, urls: List[str]) -> List[str]:
    """Fill host into multiple URLs."""
    return [fill_host(host, url) for url in urls]


def maybe_fill_host(host: str, url: str) -> str:
    """Fill host only if URL doesn't already have one."""
    if url.startswith('http://') or url.startswith('https://'):
        return url
    return fill_host(host, url)


def get_host_url(url: str) -> str:
    """Extract host from URL."""
    parsed = urlparse(url)
    return f'{parsed.scheme}://{parsed.netloc}'


def remove_host_from_url(url: str) -> str:
    """Remove host from URL, keeping path and query."""
    parsed = urlparse(url)
    return parsed.path + ('?' + parsed.query if parsed.query else '')


def encode_critical_url_elements(url: str) -> str:
    """Encode special characters in URL path segments."""
    parsed = urlparse(url)
    # Encode path segments but keep slashes
    encoded_path = '/'.join(quote(segment, safe='') for segment in parsed.path.split('/'))
    return parsed._replace(path=encoded_path).geturl()


# ============================================================================
# ENCODING/DECODING FUNCTIONS
# ============================================================================

def url_decode(s: str) -> str:
    """Decode URL-encoded string."""
    return unquote(s)


def html_decode(s: str) -> str:
    """Decode HTML entities."""
    if not s:
        return s
    # First handle custom entities
    result = s
    for entity, char in STRING_FILTER_CHAR:
        result = result.replace(entity, char)
    for entity, char in HTML_ENTITIES_CHAR:
        result = result.replace(entity, char)
    # Then use standard HTML decoder
    return html.unescape(result)


def string_filter(source: str) -> str:
    """Apply string filter replacements."""
    result = source
    for replacement, original in STRING_FILTER_CHAR:
        result = result.replace(original, replacement)
    return result


def html_entities_filter(source: str) -> str:
    """Replace HTML entities with characters."""
    result = source
    for entity, char in HTML_ENTITIES_CHAR:
        result = result.replace(entity, char)
    return html.unescape(result)


def common_string_filter(source: str) -> str:
    """Apply common string filtering."""
    return html_decode(source)


def string_breaks(source: str) -> str:
    """Convert line breaks to spaces."""
    return re.sub(r'[\r\n]+', ' ', source)


def breaks_string(source: str) -> str:
    """Convert spaces to line breaks."""
    return re.sub(r'\s+', '\n', source)


def remove_breaks(source: str) -> str:
    """Remove all line breaks."""
    return re.sub(r'[\r\n]+', '', source)


def remove_string_breaks(source: str) -> str:
    """Remove line breaks and trim."""
    return remove_breaks(source).strip()


def remove_double_space(source: str) -> str:
    """Replace multiple spaces with single space."""
    return re.sub(r'\s+', ' ', source).strip()


def trim_char(source: str, chars: str) -> str:
    """Trim specified characters from both ends."""
    return source.strip(chars)


def trim_left_char(source: str, chars: str) -> str:
    """Trim specified characters from left."""
    for i, c in enumerate(source):
        if c not in chars:
            return source[i:]
    return ''


def trim_right_char(source: str, chars: str) -> str:
    """Trim specified characters from right."""
    for i in range(len(source) - 1, -1, -1):
        if source[i] not in chars:
            return source[:i + 1]
    return ''


# ============================================================================
# PADDING AND FORMATTING
# ============================================================================

def pad_zero(s: str, total_width: int = 3, pad_all: bool = True, strip_zero: bool = False) -> str:
    """Pad string with leading zeros."""
    if not s:
        return '0' * total_width
    
    # Strip leading zeros if requested
    if strip_zero:
        s = s.lstrip('0') or '0'
    
    # Pad with zeros (default behavior is to always pad)
    result = s.zfill(total_width)
    
    return result


def inc_str(s: Union[str, int], n: int = 1) -> str:
    """Increment numeric string or integer."""
    if isinstance(s, int):
        return str(s + n)
    
    # Find numeric part at end
    match = re.search(r'(\d+)$', s)
    if match:
        num_str = match.group(1)
        num = int(num_str) + n
        return s[:match.start()] + str(num).zfill(len(num_str))
    return s + str(n)


# ============================================================================
# REGEX UTILITIES
# ============================================================================

def reg_expr_get_match(pattern: str, input_str: str, match_idx: int = 0) -> str:
    """Get regex match group."""
    try:
        matches = re.findall(pattern, input_str, re.IGNORECASE | re.DOTALL)
        if matches and match_idx < len(matches):
            match = matches[match_idx]
            if isinstance(match, tuple):
                return match[0] if match else ''
            return match if match else ''
    except:
        pass
    return ''


# ============================================================================
# STRING UTILITIES
# ============================================================================

def shorten_string(s: str, max_width: int, suffix: str = '...') -> str:
    """Shorten string to max width with suffix."""
    if len(s) <= max_width:
        return s
    return s[:max_width - len(suffix)] + suffix


def title_case(s: str) -> str:
    """Convert string to title case."""
    return s.title()


def string_replace_brackets(s: str, old_pattern: str, new_pattern: str, flags: int = 0) -> str:
    """Replace string with bracket support."""
    return s.replace(old_pattern, new_pattern)


def stream_to_string(stream) -> str:
    """Read stream to string."""
    pos = stream.tell()
    stream.seek(0)
    content = stream.read().decode('utf-8', errors='ignore')
    stream.seek(pos)
    return content


def string_to_stream(s: str, stream):
    """Write string to stream."""
    pos = stream.tell()
    stream.seek(0)
    stream.write(s.encode('utf-8'))
    stream.truncate()
    stream.seek(pos)


def get_right_value(name: str, s: str) -> str:
    """Get value after separator in string."""
    if '=' in s:
        parts = s.split('=', 1)
        if parts[0].strip() == name:
            return parts[1].strip() if len(parts) > 1 else ''
    return ''


def quoted_str(s: Union[str, int]) -> str:
    """Quote string."""
    return f'"{s}"'


def quoted_str_d(s: Union[str, int]) -> str:
    """Quote string with double quotes (same as quoted_str)."""
    return quoted_str(s)


def bracket_str(s: str) -> str:
    """Wrap string in brackets."""
    return f'[{s}]'


def random_string(length: int, include_numbers: bool = False, 
                  include_special: bool = False) -> str:
    """Generate random string."""
    chars = string.ascii_letters
    if include_numbers:
        chars += string.digits
    if include_special:
        chars += string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))


def get_valuesFromString(s: str, sep: str) -> str:
    """Get values from string separated by character."""
    return sep.join(s.split(sep))


def merge_case_insensitive(strs: Union[List[str], List[Any]]) -> str:
    """Merge strings case-insensitively, removing duplicates."""
    seen = set()
    result = []
    for s in strs:
        s_lower = str(s).lower()
        if s_lower not in seen:
            seen.add(s_lower)
            result.append(str(s))
    return ','.join(result)


# ============================================================================
# PATH AND FILE UTILITIES
# ============================================================================

def is_directory_empty(directory: str) -> bool:
    """Check if directory is empty."""
    if not os.path.exists(directory):
        return True
    return len(os.listdir(directory)) == 0


def remove_symbols(input_str: str) -> str:
    """Remove invalid filename symbols."""
    result = input_str
    for char in INVALID_FILENAME_CHARS:
        result = result.replace(char, '')
    return result


def correct_path_sys(path: str) -> str:
    """Correct path for current OS."""
    if sys.platform == 'win32':
        return path.replace('/', '\\')
    return path.replace('\\', '/')


def remove_path_delim(path: str) -> str:
    """Remove trailing path delimiter."""
    return path.rstrip(os.sep)


def fix_whitespace(s: str) -> str:
    """Fix whitespace in string."""
    return ' '.join(s.split())


def clean_string(s: str) -> str:
    """Clean string of special characters."""
    return remove_symbols(fix_whitespace(s)).strip()


def clean_multilined_string(s: str, max_line_ending: int = 1) -> str:
    """Clean multiline string, limiting consecutive line endings."""
    s = fix_whitespace(s)
    if max_line_ending == 0:
        return s.replace('\n', ' ').replace('\r', '')
    pattern = r'[\r\n]{' + str(max_line_ending + 1) + r',}'
    replacement = '\n' * max_line_ending
    return re.sub(pattern, replacement, s)


def clean_and_expand_url(url: str) -> str:
    """Clean and expand URL."""
    return fix_url(clean_string(url))


def clean_url(url: str) -> str:
    """Clean URL."""
    return url.strip()


def append_url_delim(url: str) -> str:
    """Append URL delimiter (/) if missing."""
    return url if url.endswith('/') else url + '/'


def append_url_delim_left(url: str) -> str:
    """Append URL delimiter (/) at start if missing."""
    return url if url.startswith('/') else '/' + url


def remove_url_delim(url: str) -> str:
    """Remove trailing URL delimiter."""
    return url.rstrip('/')


def remove_url_delim_left(url: str) -> str:
    """Remove leading URL delimiter."""
    return url.lstrip('/')


def fix_url(url: str) -> str:
    """Fix URL format."""
    url = clean_url(url)
    url = url.replace(' ', '%20')
    return url


def fix_path(path: str) -> str:
    """Fix path format."""
    path = clean_string(path)
    return correct_path_sys(path)


def get_last_dir(dir_path: str) -> str:
    """Get last directory name from path."""
    return os.path.basename(os.path.normpath(dir_path))


# ============================================================================
# DATE/TIME UTILITIES
# ============================================================================

def date_to_jdn(date: datetime.date) -> int:
    """Convert date to Julian Day Number."""
    a = (14 - date.month) // 12
    y = date.year + 4800 - a
    m = date.month + 12 * a - 3
    return date.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def jdn_to_date(jdn: int) -> datetime.date:
    """Convert Julian Day Number to date."""
    a = jdn + 32044
    b = (4 * a + 3) // 146097
    c = a - 146097 * b // 4
    d = (4 * c + 3) // 1461
    e = c - 1461 * d // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = 100 * b + d - 4800 + m // 10
    return datetime.date(year, month, day)


def get_current_jdn() -> int:
    """Get current Julian Day Number."""
    return date_to_jdn(datetime.date.today())


# ============================================================================
# MANGA INFO UTILITIES
# ============================================================================

def transfer_manga_info(dest: MangaInfo, source: MangaInfo):
    """Transfer manga info from source to dest."""
    dest.url = source.url
    dest.title = source.title
    dest.alt_titles = source.alt_titles
    dest.link = source.link
    dest.cover_link = source.cover_link
    dest.authors = source.authors
    dest.artists = source.artists
    dest.genres = source.genres
    dest.status = source.status
    dest.summary = source.summary
    dest.num_chapter = source.num_chapter
    dest.chapter_names = source.chapter_names.copy()
    dest.chapter_links = source.chapter_links.copy()
    dest.module = source.module


def manga_info_status_if_pos(search_str: str, ongoing_str: str,
                             completed_val: str = MANGA_INFO_STATUS_COMPLETED,
                             ongoing_val: str = MANGA_INFO_STATUS_ONGOING,
                             hiatus_val: str = MANGA_INFO_STATUS_HIATUS,
                             cancelled_val: str = MANGA_INFO_STATUS_CANCELLED) -> str:
    """Determine manga status based on search string."""
    search_lower = search_str.lower()
    ongoing_lower = ongoing_str.lower()
    
    if 'complete' in search_lower or 'finished' in search_lower:
        return completed_val
    elif 'hiatus' in search_lower or 'paused' in search_lower:
        return hiatus_val
    elif 'cancel' in search_lower:
        return cancelled_val
    elif ongoing_lower in search_lower or 'ongoing' in search_lower or 'updating' in search_lower:
        return ongoing_val
    return ongoing_val


def get_base_manga_info(m: MangaInfo) -> BaseMangaInfo:
    """Extract base manga info from full manga info."""
    base = BaseMangaInfo()
    base.title = m.title
    base.alttitles = m.alt_titles
    base.authors = m.authors
    base.artists = m.artists
    base.genres = m.genres
    base.status = m.status
    base.summary = m.summary
    base.num_chapter = m.num_chapter
    return base


def fill_base_manga_info(m: MangaInfo, base: BaseMangaInfo):
    """Fill base manga info from full manga info."""
    base.title = m.title
    base.alttitles = m.alt_titles
    base.authors = m.authors
    base.artists = m.artists
    base.genres = m.genres
    base.status = m.status
    base.summary = m.summary
    base.num_chapter = m.num_chapter


# ============================================================================
# CUSTOM RENAME
# ============================================================================

def custom_rename(a_string: str, website: str, manga_name: str, author: str,
                  artist: str, chapter: str, numbering: str, filename: str) -> str:
    """Apply custom rename pattern."""
    result = a_string
    result = result.replace(CR_NUMBERING, numbering)
    result = result.replace(CR_CHAPTER, chapter)
    result = result.replace(CR_WEBSITE, website)
    result = result.replace(CR_MANGA, manga_name)
    result = result.replace(CR_AUTHOR, author)
    result = result.replace(CR_ARTIST, artist)
    result = result.replace(CR_FILENAME, filename)
    return result


# ============================================================================
# LIST UTILITIES
# ============================================================================

def find_in_list(s: str, lst: List[str]) -> Tuple[bool, int]:
    """Find string in list, return (found, index)."""
    try:
        idx = lst.index(s)
        return True, idx
    except ValueError:
        return False, -1


def find_str_quick(s: str, lst: List[str]) -> bool:
    """Quick string search in sorted list."""
    low, high = 0, len(lst) - 1
    while low <= high:
        mid = (low + high) // 2
        if lst[mid] == s:
            return True
        elif lst[mid] < s:
            low = mid + 1
        else:
            high = mid - 1
    return False


def trim_strings(strings: List[str]):
    """Trim all strings in list."""
    for i in range(len(strings)):
        strings[i] = strings[i].strip()


def remove_duplicate_strings(*lists: List[str], rem_index: int = 0):
    """Remove duplicate strings across multiple lists."""
    if not lists:
        return
    seen = set()
    main_list = lists[rem_index]
    for i in range(len(main_list) - 1, -1, -1):
        val = main_list[i].lower()
        if val in seen:
            for lst in lists:
                if i < len(lst):
                    lst.pop(i)
        else:
            seen.add(val)


# ============================================================================
# SORTING UTILITIES
# ============================================================================

def natural_compare_str(str1: str, str2: str) -> int:
    """Natural string comparison."""
    converter = lambda t: int(t) if t.isdigit() else t.lower()
    tokens1 = [converter(c) for c in re.split(r'(\d+)', str1)]
    tokens2 = [converter(c) for c in re.split(r'(\d+)', str2)]
    
    for token1, token2 in zip(tokens1, tokens2):
        if token1 < token2:
            return -1
        elif token1 > token2:
            return 1
    return 0


def natural_custom_sort(lst: List[str], index1: int, index2: int) -> int:
    """Natural sort comparator for two indices."""
    return natural_compare_str(lst[index1], lst[index2])


def quick_sort_natural_part(lst: List[str], separator: str, start: int = 0, end: int = -1):
    """Quick sort with natural comparison on string parts."""
    if end == -1:
        end = len(lst) - 1
    
    if start < end:
        pivot = partition_natural(lst, separator, start, end)
        quick_sort_natural_part(lst, separator, start, pivot - 1)
        quick_sort_natural_part(lst, separator, pivot + 1, end)


def partition_natural(lst: List[str], separator: str, start: int, end: int) -> int:
    """Partition for natural sort."""
    pivot = lst[end]
    i = start - 1
    
    for j in range(start, end):
        if natural_compare_str(get_string_part(lst[j], separator, 0), 
                               get_string_part(pivot, separator, 0)) <= 0:
            i += 1
            lst[i], lst[j] = lst[j], lst[i]
    
    lst[i + 1], lst[end] = lst[end], lst[i + 1]
    return i + 1


def get_string_part(s: str, sep: str, part_index: int) -> str:
    """Get part of string separated by delimiter."""
    parts = s.split(sep)
    if 0 <= part_index < len(parts):
        return parts[part_index]
    return ''


# ============================================================================
# MISCELLANEOUS UTILITIES
# ============================================================================

def string_of_string(c: str, length: int) -> str:
    """Repeat character/string N times."""
    return c * length


def parse_json_array(s: str, path: str) -> List[str]:
    """Parse JSON array at specified path."""
    try:
        data = json.loads(s)
        for key in path.split('.'):
            if isinstance(data, dict):
                data = data.get(key, {})
            elif isinstance(data, list):
                idx = int(key)
                data = data[idx] if idx < len(data) else {}
        
        if isinstance(data, list):
            return [str(item) for item in data]
    except:
        pass
    return []


def convert_charset_to_utf8(s: Union[str, List[str]]) -> Union[str, List[str]]:
    """Convert string/list to UTF-8."""
    if isinstance(s, str):
        return s.encode('latin-1').decode('utf-8', errors='ignore')
    return [convert_charset_to_utf8(item) for item in s]


def serialize_and_maintain_names(data: List[str]) -> List[str]:
    """Serialize data maintaining names."""
    # Simplified implementation
    return data


def google_result_url(url: str) -> str:
    """Extract actual URL from Google search result."""
    if 'google.com' in url and '/url?' in url:
        match = re.search(r'[?&]url=([^&]+)', url)
        if match:
            return unquote(match.group(1))
    return url


def google_result_urls(urls: List[str]):
    """Extract actual URLs from Google search results."""
    for i in range(len(urls)):
        urls[i] = google_result_url(urls[i])


def create_fqdn_name(filename: str) -> str:
    """Create fully qualified domain name from filename."""
    return re.sub(r'[^\w.-]', '_', filename)


def create_fqdn_folder(current_dir: str, filename: str) -> str:
    """Create FQDN folder path."""
    fqdn = create_fqdn_name(filename)
    return os.path.join(current_dir, fqdn)


def create_fqdn_list(filename: str) -> str:
    """Create FQDN list entry."""
    return create_fqdn_name(filename)


# ============================================================================
# SYSTEM UTILITIES
# ============================================================================

def fmd_get_temp_path() -> str:
    """Get temporary directory path."""
    import tempfile
    return tempfile.gettempdir()


def fmd_power_off():
    """Power off system (requires admin/root)."""
    if sys.platform == 'win32':
        os.system('shutdown /s /t 0')
    else:
        os.system('sudo poweroff')


def fmd_hibernate():
    """Hibernate system (requires admin/root)."""
    if sys.platform == 'win32':
        os.system('shutdown /h')
    else:
        os.system('sudo systemctl hibernate')


# ============================================================================
# LOGGING UTILITIES
# ============================================================================

class Logger:
    """Simple logger class."""
    
    @staticmethod
    def send_exception(text: str):
        """Send exception log."""
        print(f'[EXCEPTION] {text}', file=sys.stderr)
    
    @staticmethod
    def send_log(text: str, value: Any = None):
        """Send log message."""
        if value is not None:
            print(f'[LOG] {text}: {value}')
        else:
            print(f'[LOG] {text}')
    
    @staticmethod
    def send_error(text: str):
        """Send error log."""
        print(f'[ERROR] {text}', file=sys.stderr)
    
    @staticmethod
    def send_warning(text: str):
        """Send warning log."""
        print(f'[WARNING] {text}', file=sys.stderr)
    
    @staticmethod
    def send_exception_log(text: str, exception: Exception):
        """Send exception with details."""
        print(f'[EXCEPTION] {text}: {exception}', file=sys.stderr)


def send_log(text: str, value: Any = None):
    """Send log message."""
    Logger.send_log(text, value)


def send_log_error(text: str):
    """Send error log."""
    Logger.send_error(text)


def send_log_warning(text: str):
    """Send warning log."""
    Logger.send_warning(text)


def send_log_exception(text: str, exception: Exception):
    """Send exception log."""
    Logger.send_exception_log(text, exception)


# ============================================================================
# HEADER UTILITIES
# ============================================================================

def header_by_name(headers: Union[List[str], Dict[str, str]], header_name: str) -> str:
    """Get header value by name."""
    if isinstance(headers, dict):
        return headers.get(header_name, '')
    
    header_lower = header_name.lower()
    for header in headers:
        if ':' in header:
            name, value = header.split(':', 1)
            if name.strip().lower() == header_lower:
                return value.strip()
    return ''


def get_header_value(headers: Union[List[str], Dict[str, str]], header_name: str) -> str:
    """Get header value (alias for header_by_name)."""
    return header_by_name(headers, header_name)


# ============================================================================
# TEST SUITE
# ============================================================================

def run_tests():
    """Run test suite."""
    print("Running uBaseUnit tests...\n")
    
    # Test string utilities
    assert html_decode('&lt;test&gt;') == '<test>', "HTML decode failed"
    assert html_decode('&amp;') == '&', "HTML entity decode failed"
    assert url_decode('%20hello') == ' hello', "URL decode failed"
    
    # Test padding
    assert pad_zero('5', 3) == '005', "Pad zero failed"
    assert pad_zero('123', 3) == '123', "Pad zero same failed"
    
    # Test increment
    assert inc_str('chapter001') == 'chapter002', "Inc str failed"
    assert inc_str(100) == '101', "Inc int failed"
    
    # Test path utilities
    assert correct_file_path('test/file:name') == 'test_file_name', "Correct filepath failed"
    assert remove_path_delim('/path/to/dir/') == '/path/to/dir', "Remove path delim failed"
    
    # Test URL utilities
    assert fill_host('https://example.com', '/page') == 'https://example.com/page', "Fill host failed"
    assert get_host_url('https://example.com/page?q=1') == 'https://example.com', "Get host failed"
    
    # Test date utilities
    today = datetime.date.today()
    jdn = date_to_jdn(today)
    back_date = jdn_to_date(jdn)
    assert back_date == today, "JDN conversion failed"
    
    # Test manga info
    manga = MangaInfo()
    manga.title = 'Test Manga'
    manga.url = 'https://example.com/manga'
    clone = manga.clone()
    assert clone.title == 'Test Manga', "Manga clone failed"
    
    # Test custom rename
    result = custom_rename(
        CR_MANGA + ' - ' + CR_CHAPTER,
        'TestSite', 'TestManga', 'Author', 'Artist', 'Ch.1', '001', 'file'
    )
    assert result == 'TestManga - Ch.1', "Custom rename failed"
    
    # Test natural sort
    assert natural_compare_str('chapter2', 'chapter10') < 0, "Natural sort failed"
    
    # Test random string
    rand = random_string(10, include_numbers=True)
    assert len(rand) == 10, "Random string length failed"
    
    print("✅ All tests passed!")


if __name__ == '__main__':
    run_tests()
