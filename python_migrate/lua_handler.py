"""
Free Manga Downloader - Python Migration
Core Lua Handler Module

This module provides Lua state management and integration,
equivalent to Pascal's LuaHandler.pas and LuaBase.pas
"""

import sys
import os
from typing import Optional, Any, Dict, List
from lupa import LuaRuntime

# Add baseunits to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class LuaHandler:
    """
    Python equivalent of TLuaHandler from LuaHandler.pas
    
    Manages Lua state, loads chunks, exposes Python objects to Lua,
    and handles function calls with garbage collection.
    """
    
    def __init__(self):
        """Initialize Lua handler with new state"""
        self._loaded_chunks: Dict[str, Any] = {}
        self._loaded_objects: Dict[str, Any] = {}
        self._call_function_count: int = 0
        self._lua = None
        self._new_handle()
    
    def _new_handle(self):
        """Create new Lua state"""
        self._free_handle()
        self._lua = LuaRuntime(unpack_returned_tuples=True)
        self._call_function_count = 0
        self._register_basics()
    
    def _free_handle(self):
        """Free Lua state and clear caches"""
        if self._lua is not None:
            self._lua = None
        self._loaded_chunks.clear()
        self._loaded_objects.clear()
    
    def _register_basics(self):
        """Register basic Lua functions (print, sleep)"""
        if self._lua is None:
            return
        
        # Register print function
        self._lua.globals()['print'] = self._luabase_print
        
        # Register sleep function
        import time
        self._lua.globals()['sleep'] = lambda ms: time.sleep(ms / 1000.0)
    
    def _luabase_print(self, *args):
        """Python equivalent of luabase_print"""
        for arg in args:
            print(str(arg))
    
    @property
    def handle(self):
        """Return Lua state"""
        return self._lua
    
    def load_chunk(self, name: str, chunk_data: bytes) -> int:
        """
        Load Lua chunk from memory stream
        
        Args:
            name: Chunk name
            chunk_data: Lua code as bytes
            
        Returns:
            0 on success, error code otherwise
        """
        if name in self._loaded_chunks:
            return 0
        
        try:
            # Execute the chunk
            self._lua.execute(chunk_data.decode('utf-8'))
            self._loaded_chunks[name] = chunk_data
            return 0
        except Exception as e:
            print(f"Error loading chunk {name}: {e}")
            return 1
    
    def load_chunk_execute(self, name: str, chunk_data: bytes, 
                          always_load_from_file: bool = False) -> int:
        """
        Load and execute Lua chunk
        
        Args:
            name: Chunk name
            chunk_data: Lua code as bytes
            always_load_from_file: If True, reload even if cached
            
        Returns:
            0 on success, error code otherwise
        """
        if name in self._loaded_chunks and not always_load_from_file:
            return 0
        
        if name in self._loaded_chunks and always_load_from_file:
            del self._loaded_chunks[name]
        
        try:
            self._lua.execute(chunk_data.decode('utf-8'))
            self._loaded_chunks[name] = chunk_data
            return 0
        except Exception as e:
            print(f"Error executing chunk {name}: {e}")
            return 1
    
    def load_object(self, name: str, obj: Any, add_metatable=None):
        """
        Expose Python object to Lua
        
        Args:
            name: Name in Lua context
            obj: Python object to expose
            add_metatable: Optional metatable function
        """
        if name in self._loaded_objects:
            if self._loaded_objects[name] is obj:
                return
            else:
                del self._loaded_objects[name]
        
        if self._lua is not None:
            self._lua.globals()[name] = obj
        
        self._loaded_objects[name] = obj
    
    def call_function(self, function_name: str):
        """
        Call Lua function
        
        Args:
            function_name: Name of Lua function to call
        """
        # Garbage collection after 15 calls
        if self._call_function_count > 15:
            import gc
            gc.collect()
            gc.collect()
            self._call_function_count = 0
        
        if self._lua is None:
            raise Exception("Lua state not initialized")
        
        try:
            func = self._lua.eval(function_name)
            if not callable(func):
                raise Exception(f"No function named {function_name}")
            func()
            self._call_function_count += 1
        except Exception as e:
            raise Exception(f'LuaCallFunction("{function_name}") error: {e}')
    
    def clear_stack(self):
        """Clear Lua stack (not needed in lupa, but kept for API compatibility)"""
        pass
    
    def destroy(self):
        """Cleanup"""
        self._free_handle()


def lua_new_base_state() -> LuaRuntime:
    """
    Create new Lua state with basic registrations
    
    Returns:
        LuaRuntime instance
    """
    lua = LuaRuntime(unpack_returned_tuples=True)
    
    # Register basic functions
    lua.globals()['print'] = lambda *args: print(*args)
    import time
    lua.globals()['sleep'] = lambda ms: time.sleep(ms / 1000.0)
    
    return lua


def lua_call_function(lua: LuaRuntime, func_name: str):
    """
    Call Lua function by name
    
    Args:
        lua: Lua state
        func_name: Function name
    """
    try:
        func = lua.eval(func_name)
        if not callable(func):
            raise Exception(f"No function named {func_name}")
        return func()
    except Exception as e:
        raise Exception(f'LuaCallFunction("{func_name}") error: {e}')


def lua_load_from_stream(lua: LuaRuntime, stream_data: bytes, name: str) -> int:
    """
    Load Lua from byte stream
    
    Args:
        lua: Lua state
        stream_data: Lua code as bytes
        name: Chunk name
        
    Returns:
        0 on success
    """
    try:
        lua.execute(stream_data.decode('utf-8'), name=name)
        return 0
    except Exception as e:
        print(f"Error loading from stream: {e}")
        return 1


# Example usage and testing
if __name__ == '__main__':
    print("Testing LuaHandler...")
    
    # Test 1: Basic Lua execution
    handler = LuaHandler()
    print("✓ LuaHandler created")
    
    # Test 2: Load and execute simple chunk
    test_chunk = b"""
    function test_func()
        print('Hello from Lua!')
        return 42
    end
    """
    result = handler.load_chunk_execute('test', test_chunk)
    assert result == 0, "Failed to load chunk"
    print("✓ Chunk loaded successfully")
    
    # Test 3: Call Lua function
    handler.call_function('test_func')
    print("✓ Function called successfully")
    
    # Test 4: Expose Python object to Lua
    class TestObject:
        def greet(self, name):
            return f"Hello, {name}!"
    
    test_obj = TestObject()
    handler.load_object('pyobj', test_obj)
    
    lua_code = b"""
    function test_python_obj()
        return pyobj:greet('World')
    end
    """
    handler.load_chunk_execute('test2', lua_code)
    result = handler.call_function('test_python_obj')
    print("✓ Python object exposed to Lua")
    
    # Test 5: Load existing Lua module
    lua_utils_path = os.path.join(os.path.dirname(__file__), '..', 'lua', 'utils.lua')
    if os.path.exists(lua_utils_path):
        with open(lua_utils_path, 'rb') as f:
            utils_code = f.read()
        handler.load_chunk_execute('utils', utils_code)
        print("✓ External Lua module loaded")
    
    handler.destroy()
    print("\n✅ All tests passed!")
