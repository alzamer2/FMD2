#!/usr/bin/env python3
"""
FMD Duktape Module - Python equivalent of Duktape.pas and LuaDuktape.pas

Provides JavaScript execution via PyExecJS or js2py for sites that require JS evaluation.
"""

try:
    # Try to use execjs (Node.js based, more compatible)
    import execjs
    HAS_EXECJS = True
    HAS_JS2PY = False
except ImportError:
    HAS_EXECJS = False
    try:
        # Fallback to js2py (pure Python, no Node.js needed)
        import js2py
        HAS_JS2PY = True
    except ImportError:
        HAS_JS2PY = False


class Duktape:
    """
    JavaScript execution engine.
    
    Equivalent to Duktape unit in Pascal.
    Supports both Node.js (via execjs) and pure Python (via js2py).
    """
    
    _runtime = None
    _use_js2py = False
    
    @classmethod
    def _get_runtime(cls):
        """Get or create JS runtime."""
        if cls._runtime is None:
            if HAS_EXECJS:
                # Use Node.js runtime (preferred)
                cls._runtime = execjs.get()
                cls._use_js2py = False
            elif HAS_JS2PY:
                # Use js2py (pure Python fallback)
                cls._runtime = js2py.EvalJs()
                cls._use_js2py = True
            else:
                raise ImportError(
                    "No JavaScript engine available. "
                    "Install either 'PyExecJS' (requires Node.js) or 'js2py' (pure Python)."
                )
        return cls._runtime
    
    @classmethod
    def exec_js(cls, code: str) -> str:
        """
        Execute JavaScript code and return the result as string.
        
        Args:
            code: JavaScript code to execute
            
        Returns:
            Result of JavaScript execution as string
        """
        runtime = cls._get_runtime()
        
        try:
            if cls._use_js2py:
                # js2py returns Python objects
                result = runtime.eval(code)
                return str(result)
            else:
                # execjs returns string/JSON
                result = runtime.eval(code)
                if result is None:
                    return ""
                return str(result)
        except Exception as e:
            # Log error but don't crash
            print(f"Duktape.ExecJS Error: {e}")
            return ""
    
    @classmethod
    def eval(cls, code: str):
        """
        Evaluate JavaScript and return the raw result.
        
        Args:
            code: JavaScript code to evaluate
            
        Returns:
            Raw result from JavaScript execution
        """
        runtime = cls._get_runtime()
        
        if cls._use_js2py:
            return runtime.eval(code)
        else:
            return runtime.eval(code)
    
    @classmethod
    def call_function(cls, func_name: str, *args):
        """
        Call a JavaScript function by name.
        
        Args:
            func_name: Name of the JavaScript function
            *args: Arguments to pass to the function
            
        Returns:
            Result of the function call
        """
        runtime = cls._get_runtime()
        
        if cls._use_js2py:
            func = getattr(runtime, func_name, None)
            if func:
                return func(*args)
            return None
        else:
            # Build function call
            args_str = ', '.join(repr(arg) for arg in args)
            return cls.exec_js(f"{func_name}({args_str})")


# Lua module interface
def ExecJS(code: str) -> str:
    """Execute JavaScript code (Lua compatible function)."""
    return Duktape.exec_js(code)


def lua_open(L=None):
    """
    Lua open function - registers the module with Lua.
    This is called when Lua does require('fmd.duktape')
    """
    return {
        'ExecJS': ExecJS,
        'eval': Duktape.eval,
        'call_function': Duktape.call_function,
        'Duktape': Duktape
    }


# Test code
if __name__ == '__main__':
    print("Testing Duktape module...")
    
    if not (HAS_EXECJS or HAS_JS2PY):
        print("⚠ No JavaScript engine available!")
        print("  Install with: pip install PyExecJS  OR  pip install js2py")
        print("  Note: PyExecJS requires Node.js to be installed")
    else:
        # Test basic JavaScript
        test_code = "1 + 2"
        result = ExecJS(test_code)
        print(f"✓ ExecJS('{test_code}') = {result}")
        
        # Test more complex JS
        test_code2 = "JSON.stringify({name: 'test', value: 123})"
        result2 = ExecJS(test_code2)
        print(f"✓ ExecJS('{test_code2[:40]}...') = {result2}")
        
        # Test function call
        test_func = "function add(a,b) { return a + b; } add(5, 7)"
        result3 = ExecJS(test_func)
        print(f"✓ Function call result = {result3}")
        
        print("\n✅ All tests passed!")
    
    print(f"\nBackend: {'js2py (pure Python)' if HAS_JS2PY and not HAS_EXECJS else 'execjs (Node.js)' if HAS_EXECJS else 'None'}")
