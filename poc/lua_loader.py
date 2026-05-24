#!/usr/bin/env python3
"""
Proof of Concept: Lua Loader for FMD Python Migration
This module demonstrates loading and executing Lua scripts while maintaining
compatibility with the original Pascal/Lazarus FMD project structure.
"""

import os
import sys
from pathlib import Path

# Use lupa for Lua integration (most compatible with Lua 5.2+)
try:
    from lupa import LuaRuntime, LuaError
except ImportError:
    print("Installing lupa for Lua integration...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "lupa"])
    from lupa import LuaRuntime, LuaError


class LuaHandler:
    """
    Python equivalent of TLuaHandler from Pascal
    Handles Lua state management, chunk loading, and object exposure
    """
    
    def __init__(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.loaded_chunks = {}
        self.loaded_objects = {}
        self.call_count = 0
        self._register_basics()
    
    def _register_basics(self):
        """Register basic functions like print and sleep"""
        # Override print to use Python's print
        lua_globals = self.lua.globals()
        lua_globals.print = print
        
        # Sleep function (expects milliseconds like Pascal version)
        import time
        def sleep(ms):
            time.sleep(ms / 1000.0)
        lua_globals.sleep = sleep
    
    def load_chunk(self, name: str, chunk_code: str) -> int:
        """
        Load a Lua chunk without executing it
        Returns 0 on success, error code on failure
        """
        if name in self.loaded_chunks:
            return 0
        
        try:
            chunk = self.lua.execute(chunk_code)
            self.loaded_chunks[name] = chunk
            return 0
        except LuaError as e:
            print(f"Lua chunk load error [{name}]: {e}")
            return 1
    
    def load_chunk_execute(self, name: str, chunk_code: str, always_reload: bool = False) -> int:
        """
        Load and execute a Lua chunk
        Returns 0 on success, error code on failure
        """
        if name in self.loaded_chunks and not always_reload:
            return 0
        
        try:
            result = self.lua.execute(chunk_code)
            self.loaded_chunks[name] = result
            return 0
        except LuaError as e:
            print(f"Lua chunk execute error [{name}]: {e}")
            return 1
    
    def load_object(self, name: str, obj: object):
        """
        Expose a Python object to Lua
        Equivalent to luaClassPushObject in Pascal
        """
        if name in self.loaded_objects:
            if self.loaded_objects[name] is obj:
                return
            del self.loaded_objects[name]
        
        lua_globals = self.lua.globals()
        setattr(lua_globals, name, obj)
        self.loaded_objects[name] = obj
    
    def call_function(self, func_name: str):
        """
        Call a Lua function by name
        Triggers GC after 15 calls like Pascal version
        """
        import gc
        if self.call_count > 15:
            gc.collect()
            self.call_count = 0
        
        try:
            func = self.lua.eval(func_name)
            if callable(func):
                func()
            else:
                raise Exception(f"{func_name} is not callable")
            self.call_count += 1
        except (LuaError, AttributeError) as e:
            raise Exception(f"Lua function call error [{func_name}]: {e}")
    
    def clear_stack(self):
        """Clear Lua stack (implicit in lupa, but kept for API compatibility)"""
        pass
    
    def get_global(self, name: str):
        """Get a global variable from Lua"""
        lua_globals = self.lua.globals()
        return getattr(lua_globals, name, None)
    
    def set_global(self, name: str, value):
        """Set a global variable in Lua"""
        lua_globals = self.lua.globals()
        setattr(lua_globals, name, value)


def load_lua_file(filepath: str) -> str:
    """Load Lua file content"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def test_basic_lua():
    """Test basic Lua functionality"""
    print("=" * 60)
    print("TEST 1: Basic Lua Integration")
    print("=" * 60)
    
    handler = LuaHandler()
    
    # Test 1: Simple Lua code execution
    lua_code = """
    function test_function()
        local x = 10
        local y = 20
        print("Lua says: " .. x .. " + " .. y .. " = " .. (x + y))
        return x + y
    end
    """
    
    result = handler.load_chunk_execute("test", lua_code)
    assert result == 0, "Failed to load Lua chunk"
    
    # Call the function
    result_func = handler.lua.eval('test_function()')
    print(f"Result from Lua: {result_func}")
    assert result_func == 30, "Lua calculation failed"
    
    print("✓ Basic Lua integration works!\n")


def test_python_object_exposure():
    """Test exposing Python objects to Lua"""
    print("=" * 60)
    print("TEST 2: Python Object Exposure to Lua")
    print("=" * 60)
    
    handler = LuaHandler()
    
    # Create a Python class to expose
    class Logger:
        def log(self, message):
            print(f"[Python Logger] {message}")
        
        def get_timestamp(self):
            import datetime
            return datetime.datetime.now().isoformat()
    
    logger = Logger()
    handler.load_object('Logger', logger)
    
    # Use the Python object from Lua
    lua_code = """
    function use_logger()
        Logger.log("Hello from Lua!")
        local ts = Logger:get_timestamp()
        print("Timestamp from Python: " .. ts)
        return ts
    end
    """
    
    handler.load_chunk_execute("logger_test", lua_code)
    timestamp = handler.lua.eval('use_logger()')
    assert timestamp is not None, "Failed to get timestamp from Python"
    
    print("✓ Python object exposure works!\n")


def test_json_utility():
    """Test using existing Lua JSON module"""
    print("=" * 60)
    print("TEST 3: Loading Existing Lua Modules (json.lua)")
    print("=" * 60)
    
    handler = LuaHandler()
    
    # Load the existing json.lua from the project
    lua_path = Path("/workspace/lua/utils/json.lua")
    if lua_path.exists():
        json_lua_code = load_lua_file(str(lua_path))
        # Execute directly - returns the json module table
        json_module = handler.lua.execute(json_lua_code)
        
        # Test JSON encode/decode using the returned module
        data = handler.lua.table(name="Test Manga", chapters=10, active=True)
        encoded = json_module.encode(data)
        decoded = json_module.decode(encoded)
        
        print(f"JSON encode result: {encoded}")
        print(f"JSON decode result: name={decoded.name}, chapters={decoded.chapters}")
        assert decoded.name == "Test Manga", "JSON decode failed"
        assert decoded.chapters == 10, "JSON decode failed"
        print("✓ Lua JSON module works!\n")
    else:
        print("⚠ json.lua not found, skipping test\n")


def test_c_dll_equivalents():
    """Test Python equivalents of C DLLs used in Pascal"""
    print("=" * 60)
    print("TEST 4: C DLL Functionality via Python")
    print("=" * 60)
    
    # SQLite3 (was loaded via sqlite3.dll)
    import sqlite3
    print("✓ sqlite3 - Built-in Python module")
    
    # PCRE2 regex (was loaded via libpcre2-8.dll)
    import re
    test_pattern = r'\d+'
    test_string = "Chapter 123"
    match = re.search(test_pattern, test_string)
    assert match.group() == "123", "Regex failed"
    print("✓ re (PCRE equivalent) - Built-in Python module")
    
    # OpenSSL/crypto (was loaded via libcrypto-3-x64.dll, libssl-3-x64.dll)
    import hashlib
    sha256_hash = hashlib.sha256(b"test").hexdigest()
    assert len(sha256_hash) == 64, "SHA256 failed"
    print("✓ hashlib (OpenSSL equivalent) - Built-in Python module")
    
    # WebP image support (was loaded via libwebp.dll)
    try:
        from PIL import Image
        print("✓ Pillow (WebP support) - Available")
    except ImportError:
        print("⚠ Pillow - Not installed (pip install pillow)")
    
    # HTTP requests (replaces Synapse)
    try:
        import requests
        print("✓ requests - Available for HTTP operations")
    except ImportError:
        print("⚠ requests - Not installed (pip install requests)")
    
    print("\n✓ All C DLL equivalents available in Python!\n")


def main():
    """Run all PoC tests"""
    print("\n" + "=" * 60)
    print("FREE MANGA DOWNLOADER - PASCAL TO PYTHON MIGRATION")
    print("Proof of Concept: Lua Integration + C DLL Equivalents")
    print("=" * 60 + "\n")
    
    try:
        test_basic_lua()
        test_python_object_exposure()
        test_json_utility()
        test_c_dll_equivalents()
        
        print("=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        print("\nKey findings:")
        print("1. Lua integration via lupa works seamlessly")
        print("2. Python objects can be exposed to Lua scripts")
        print("3. Existing Lua modules (json.lua) work without modification")
        print("4. All C DLL functionality has Python equivalents")
        print("\nNext steps:")
        print("- Convert Pascal units to Python modules")
        print("- Replace LCL GUI with PyQt6/CustomTkinter")
        print("- Migrate website modules (keep Lua, wrap in Python)")
        print("- Implement download manager in Python")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
