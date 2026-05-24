# Free Manga Downloader - Python Migration

This directory contains the Python 3 migration of Free Manga Downloader (FMD), originally written in Pascal/Lazarus.

## Architecture

The migration keeps:
- ✅ **All Lua modules unchanged** - 100+ website scraper `.lua` files work as-is
- ✅ **C DLL functionality** - Replaced with native Python libraries

The migration replaces:
- ❌ Pascal units → Python modules
- ❌ Lazarus LCL GUI → PyQt6/CustomTkinter (future)
- ❌ Synapse HTTP → `requests` library
- ❌ PCRE2 DLL → Python `re` module
- ❌ OpenSSL DLL → `hashlib`, `cryptography`
- ❌ SQLite3 DLL → Python `sqlite3` (built-in)

## Core Modules Converted

### 1. `lua_handler.py` - Lua Integration
**Pascal equivalent:** `LuaHandler.pas`, `LuaBase.pas`

```python
from lua_handler import LuaHandler

handler = LuaHandler()
handler.load_chunk_execute('myscript', lua_code_bytes)
handler.call_function('main')
```

**Features:**
- Lua state management via `lupa` library
- Load/execute Lua chunks
- Expose Python objects to Lua
- Automatic garbage collection

### 2. `http_client.py` - HTTP Client
**Pascal equivalent:** `httpsendthread.pas`, `httpsend.pas`

```python
from http_client import HTTPSendThread

http = HTTPSendThread()
http.get('https://example.com')
print(http.get_document_string())
```

**Features:**
- Cookie management
- GZIP/Brotli/Zstd compression
- Redirect following
- Retry logic
- Custom headers

### 3. `pcre2_regex.py` - Regular Expressions
**Pascal equivalent:** `pcre2.pas`, `pcre2lib.pas`

```python
from pcre2_regex import find, match, gsub

offset = find("Hello 123", r"\d+")
result = gsub("cat bat", r"at", "og")  # "cog bog"
```

**Features:**
- PCRE2-compatible API
- Pattern caching
- Group matching
- Global substitution

## Dependencies

Install required packages:

```bash
pip install lupa requests brotli zstandard cryptography pillow
```

## Migration Status

| Module | Pascal File | Python File | Status |
|--------|-------------|-------------|--------|
| Lua Handler | `LuaHandler.pas` | `lua_handler.py` | ✅ Complete |
| HTTP Client | `httpsendthread.pas` | `http_client.py` | ✅ Complete |
| PCRE2 Regex | `pcre2.pas` | `pcre2_regex.py` | ✅ Complete |
| Base Utils | `uBaseUnit.pas` | `base_utils.py` | 🔄 In Progress |
| Options | `FMDOptions.pas` | `options.py` | ⏳ Pending |
| Downloads | `uDownloadsManager.pas` | `downloads.py` | ⏳ Pending |
| Database | `FavoritesDB.pas` | `database.py` | ⏳ Pending |
| GUI Main | `frmMain.pas/.lfm` | `gui_main.py` | ⏳ Pending |

## Next Steps

1. **Core Utilities** - Convert `uBaseUnit.pas` (string utils, file ops)
2. **Configuration** - Convert `FMDOptions.pas` (settings management)
3. **Database Layer** - Convert SQLite database units
4. **Download Manager** - Convert download queue and processing
5. **GUI Framework** - Choose PyQt6 or CustomTkinter for UI
6. **Website Modules** - Test existing Lua scrapers with Python backend

## Testing

Each module includes self-tests:

```bash
python lua_handler.py
python http_client.py
python pcre2_regex.py
```

## Lua Module Compatibility

All existing Lua website modules require **ZERO changes**:

```lua
-- lua/modules/mangafox.lua (unchanged)
function GetMangaInfo(url)
    local html = http.GET(url)
    -- ... existing code works as-is
end
```

The Python layer provides the same API that Pascal provided:
- `http.GET()` → Python HTTP client
- `regex.match()` → Python PCRE2 wrapper
- `crypto.md5()` → Python hashlib
- `file.read()` → Python file I/O

## Directory Structure

```
/workspace/
├── baseunits/           # Original Pascal source
│   ├── lua/            # Pascal-Lua bridge code
│   ├── synapse/        # HTTP/network library
│   └── *.pas           # Other Pascal units
├── lua/                 # Lua modules (UNCHANGED)
│   ├── modules/        # Website scrapers
│   └── utils/          # Utility functions
└── python_migrate/     # Python conversion
    ├── lua_handler.py
    ├── http_client.py
    ├── pcre2_regex.py
    └── README.md       # This file
```

## Performance Notes

- Python's `requests` is faster than Synapse for HTTP
- Native `re` module matches PCRE2 performance
- `lupa` provides near-native Lua integration speed
- Consider PyPy for additional performance gains

## Known Limitations

- GUI not yet implemented (Lazarus LCL → PyQt6 pending)
- Some threading models differ (Pascal threads → Python asyncio/threading)
- ImageMagick integration needs Python Wand library

## Contributing

When converting new Pascal units:
1. Create corresponding Python module in this directory
2. Match class/function names where possible
3. Include comprehensive tests
4. Update this README with status

## License

Same as original FMD: GPLv2
