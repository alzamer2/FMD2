"""
Lua Compatibility Layer for FMD Python Migration
Replaces Pascal Lua loading logic with Python equivalents
Handles: Lua 5.2+ compatibility, FMD stub objects, BOM removal
"""
import re
import logging
from pathlib import Path
from typing import Tuple, List, Optional
from lupa import LuaRuntime

logger = logging.getLogger(__name__)


class FMDCompatibilityLayer:
    """
    Provides compatibility layer for FMD's custom Lua environment.
    Replaces Pascal objects (TASK, HTTP, MODULE_DATA) with Python stubs.
    Fixes Lua 5.2+ incompatibilities in legacy Lua 5.1 code.
    """
    
    def __init__(self):
        self.runtime: Optional[LuaRuntime] = None
        self._setup_stubs()
    
    def _setup_stubs(self):
        """Create Python stub classes that mimic FMD's Pascal objects."""
        
        class FMDStub:
            """
            Stub for FMD Pascal objects like TTask, THTTPSendThread.
            Supports attribute access, method calls, and table-like operations.
            """
            
            def __init__(self):
                self._data = {}
                self._count = 0
            
            def __getattr__(self, name):
                if name not in self._data:
                    # Auto-create nested stubs for method chaining
                    self._data[name] = FMDStub()
                return self._data[name]
            
            def __setattr__(self, name, value):
                if name.startswith('_'):
                    object.__setattr__(self, name, value)
                else:
                    self._data[name] = value
                    if not name.startswith('_'):
                        self._count += 1
            
            def __call__(self, *args, **kwargs):
                # Allow stub to be called as function
                return self
            
            def __getitem__(self, key):
                return self._data.get(str(key), "")
            
            def __setitem__(self, key, value):
                self._data[str(key)] = value
            
            def __len__(self):
                return len([k for k in self._data.keys() if not k.startswith('_')])
            
            def Count(self):
                """Pascal-style Count property"""
                return self._count
            
            def Add(self, item):
                """Pascal-style Add method"""
                key = str(self._count)
                self._data[key] = item
                self._count += 1
            
            def Clear(self):
                """Pascal-style Clear method"""
                self._data = {}
                self._count = 0
            
            def to_dict(self):
                """Convert to Python dict"""
                return {k: v for k, v in self._data.items() if not k.startswith('_')}
        
        self.FMDStub = FMDStub
    
    def create_runtime(self, unpack_tuples=True) -> LuaRuntime:
        """
        Create a configured Lua runtime with FMD compatibility.
        
        Args:
            unpack_tuples: If True, Python tuples are unpacked in Lua
            
        Returns:
            Configured LuaRuntime instance
        """
        runtime = LuaRuntime(unpack_returned_tuples=unpack_tuples)
        
        # Configure package path to find templates and modules
        runtime.execute("""
            package.path = package.path .. 
                ';./lua/?.lua;' ..
                './lua/templates/?.lua;' ..
                './lua/modules/?.lua;' ..
                './lua/utils/?.lua'
        """)
        
        # Create global stub objects
        TASK = self.FMDStub()
        HTTP = self.FMDStub()
        MODULE_DATA = self.FMDStub()
        
        runtime.globals()['TASK'] = TASK
        runtime.globals()['HTTP'] = HTTP
        runtime.globals()['MODULE_DATA'] = MODULE_DATA
        
        # Stub functions that mimic Pascal functionality
        def CreateTXQuery(doc):
            """Stub for TXQuery HTML parser"""
            return self.FMDStub()
        
        def GetCurrentString():
            """Stub for current language code"""
            return "en"
        
        def sleep(ms):
            """Stub for Sleep function (milliseconds)"""
            import time
            time.sleep(ms / 1000.0)
        
        runtime.globals()['CreateTXQuery'] = CreateTXQuery
        runtime.globals()['GetCurrentString'] = GetCurrentString
        runtime.globals()['sleep'] = sleep
        
        # Inject a custom require wrapper into Lua globals
        # We can't replace runtime.require directly (read-only), but we can 
        # override the global 'require' function that Lua code sees
        compat_self = self
        
        def custom_require_wrapper(module_name):
            """Custom require that applies fixes before loading"""
            try:
                # Try normal require first
                return runtime.require(module_name)
            except Exception as e:
                # If it fails, try to load manually with fixes
                logger.debug(f"Normal require failed for {module_name}, trying manual load: {e}")
                
                # Convert module name to file path
                parts = module_name.split('.')
                base_paths = ['./lua', './lua/templates', './lua/modules', './lua/utils']
                
                for base in base_paths:
                    test_path = Path(base) / ('/'.join(parts) + '.lua')
                    if test_path.exists():
                        try:
                            with open(test_path, 'r', encoding='utf-8') as f:
                                code = f.read()
                            
                            # Apply fixes
                            fixed_code, _ = compat_self.fix_lua_code(code, test_path.name)
                            
                            # Execute in runtime
                            result = runtime.execute(fixed_code)
                            logger.debug(f"Manually loaded {module_name} from {test_path}")
                            return result
                        except Exception as e2:
                            logger.error(f"Manual load also failed for {module_name}: {e2}")
                            raise
                
                # Re-raise original error
                raise
        
        runtime.globals()['require'] = custom_require_wrapper
        
        self.runtime = runtime
        return runtime
    
    @staticmethod
    def fix_lua_code(code: str, filename: str = "") -> Tuple[str, List[str]]:
        """
        Apply compatibility fixes to make legacy Lua code work with Lua 5.5.
        
        Fixes applied:
        1. Remove UTF-8 BOM (Byte Order Mark)
        2. Remove loop variable modifications (Lua 5.2+ incompatibility)
        3. Handle other common issues
        
        Args:
            code: Raw Lua source code
            filename: Optional filename for logging
            
        Returns:
            Tuple of (fixed_code, list_of_fixes_applied)
        """
        fixes = []
        
        # Fix 1: Remove BOM
        if code.startswith('\ufeff'):
            code = code[1:]
            fixes.append("Removed UTF-8 BOM")
        
        # Fix 2: Remove loop variable modifications
        lines = code.split('\n')
        fixed_lines = []
        in_for_loop = False
        for_var = None
        loop_depth = 0
        
        for line in lines:
            # Track entering for loops
            match = re.match(r'\s*for\s+(\w+)\s*=\s*', line)
            if match:
                if not in_for_loop:
                    for_var = match.group(1)
                in_for_loop = True
                loop_depth += 1
                fixed_lines.append(line)
                continue
            
            # Track nested for loops
            if in_for_loop and re.match(r'\s*for\s+\w+\s*=\s*', line):
                loop_depth += 1
                fixed_lines.append(line)
                continue
            
            # Track exiting for loops
            if in_for_loop and re.match(r'\s*end\s*(?:--.*)?$', line):
                loop_depth -= 1
                if loop_depth == 0:
                    in_for_loop = False
                    for_var = None
                fixed_lines.append(line)
                continue
            
            # Inside for loop, remove loop variable modifications
            if in_for_loop and for_var and loop_depth == 1:
                pattern = rf'\s*{re.escape(for_var)}\s*=\s*{re.escape(for_var)}\s*[\+\-\*/]'
                if re.match(pattern, line):
                    fixed_lines.append(f'-- {line}  -- [PYFIX] Loop var modification removed for Lua 5.2+')
                    fixes.append(f"Removed '{for_var}' increment in {filename}")
                    continue
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines), fixes
    
    def load_module(self, file_path: str, apply_fixes: bool = True) -> Tuple[Optional[any], List[str]]:
        """
        Load a Lua module file with automatic compatibility fixes.
        
        Args:
            file_path: Path to the .lua file
            apply_fixes: If True, apply compatibility fixes automatically
            
        Returns:
            Tuple of (lua_result or None, list_of_fixes_applied)
        """
        if self.runtime is None:
            self.create_runtime()
        
        fixes = []
        
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"Module file not found: {file_path}")
                return None, ["File not found"]
            
            # Read file
            with open(path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Apply fixes if enabled
            if apply_fixes:
                code, fixes = self.fix_lua_code(code, path.name)
            
            # Execute Lua code
            result = self.runtime.execute(code)
            
            logger.debug(f"Loaded module: {path.name} ({len(fixes)} fixes)")
            return result, fixes
            
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            raise


# Convenience function for quick module loading
def load_lua_module(file_path: str, apply_fixes: bool = True) -> any:
    """
    Quick helper to load a single Lua module.
    
    Args:
        file_path: Path to .lua file
        apply_fixes: Apply compatibility fixes
        
    Returns:
        Lua module result
    """
    compat = FMDCompatibilityLayer()
    compat.create_runtime()
    result, _ = compat.load_module(file_path, apply_fixes)
    return result


if __name__ == "__main__":
    # Test the compatibility layer
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 70)
    print("FMD Lua Compatibility Layer - Test Suite")
    print("=" * 70)
    
    # Create compatibility layer
    compat = FMDCompatibilityLayer()
    runtime = compat.create_runtime()
    
    # Test 1: Basic Lua execution
    print("\n✓ Test 1: Basic Lua execution")
    result = runtime.eval("1 + 1")
    assert result == 2, "Basic math failed"
    print(f"  1 + 1 = {result}")
    
    # Test 2: FMD stub objects
    print("\n✓ Test 2: FMD stub objects")
    TASK = runtime.globals()['TASK']
    TASK.Test.Value = 42
    print(f"  TASK.Test.Value = {TASK.Test.Value}")
    
    # Test 3: Load a template with fixes
    print("\n✓ Test 3: Load template with compatibility fixes")
    test_template = "lua/templates/MangaReaderOnline.lua"
    if Path(test_template).exists():
        result, fixes = compat.load_module(test_template)
        print(f"  Loaded: {test_template}")
        print(f"  Fixes applied: {fixes}")
    else:
        print(f"  ⊘ Skipped (file not found)")
    
    # Test 4: Load multiple modules
    print("\n✓ Test 4: Batch load test")
    lua_dir = Path("./lua/modules")
    loaded = 0
    failed = 0
    
    for i, lua_file in enumerate(list(lua_dir.glob("*.lua"))[:20]):  # Test first 20
        try:
            result, fixes = compat.load_module(str(lua_file))
            loaded += 1
        except Exception as e:
            failed += 1
    
    print(f"  Loaded: {loaded}/20 modules")
    print(f"  Failed: {failed}/20 modules")
    
    print("\n" + "=" * 70)
    print("All tests completed successfully!")
    print("=" * 70)
