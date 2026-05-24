"""
Module Loader - Discovers and loads Lua website scraper modules
Equivalent to: WebsiteModules.pas, uLuaHandler.pas
"""

import sys
import os
import glob
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lua_handler import LuaHandler
from fmd_crypto import register_with_lua as register_crypto
from string_utils import register as register_strings


class ModuleLoader:
    """Discovers and loads Lua website scraper modules."""
    
    def __init__(self):
        self.lua = LuaHandler()
        self.modules = {}
        self.failed_modules = []
        
        # Register all FMD libraries
        register_crypto(self.lua.lua)
        register_strings(self.lua.lua)
        
        # Setup require wrapper for utils.* and templates.*
        self._setup_require_wrapper()
    
    def _setup_require_wrapper(self):
        """Setup custom require to handle utils.* and templates.* paths."""
        lua = self.lua.lua
        
        # Store original require
        lua.execute("local original_require = require")
        
        # Create wrapper that handles fmd.*, utils.*, templates.*
        wrapper_code = """
local original_require = require
local function custom_require(module_name)
    -- Handle fmd.crypto (already registered via Python)
    if module_name == 'fmd.crypto' then
        return original_require('fmd_crypto')
    end
    
    -- Handle fmd.imagepuzzle
    if module_name == 'fmd.imagepuzzle' then
        return original_require('fmd_imagepuzzle')
    end
    
    -- Handle fmd.duktape
    if module_name == 'fmd.duktape' then
        return original_require('fmd_duktape')
    end
    
    -- Handle utils.* -> just the module name (e.g., 'utils.json' -> 'json')
    if module_name:match('^utils%.') then
        local actual_name = module_name:gsub('^utils%.', '')
        return original_require(actual_name)
    end
    
    -- Handle templates.* -> just the template name
    if module_name:match('^templates%.') then
        local template_name = module_name:gsub('^templates%.', '')
        return original_require(template_name)
    end
    
    -- Try loading from package.preload first (for dynamically loaded templates)
    if package.preload[module_name] then
        return package.preload[module_name]()
    end
    
    -- Default: use original require
    return original_require(module_name)
end

require = custom_require
"""
        lua.execute(wrapper_code)
    
    def discover_modules(self, lua_dir: str) -> tuple:
        """
        Discovers all .lua files in the given directory.
        Returns tuple: (template_files, module_files)
        Templates must be loaded first before modules that depend on them.
        """
        lua_path = Path(lua_dir)
        if not lua_path.exists():
            print(f"Error: Lua directory not found: {lua_dir}")
            return [], []
        
        template_files = []
        module_files = []
        
        for lua_file in lua_path.rglob("*.lua"):
            # Skip utils directory
            if 'utils' in lua_file.parts:
                continue
            
            file_str = str(lua_file)
            # Check if it's a template
            if 'templates' in lua_file.parts:
                template_files.append(file_str)
            else:
                module_files.append(file_str)
        
        return sorted(template_files), sorted(module_files)
    
    def load_module(self, lua_file: str) -> bool:
        """
        Loads a single Lua module file.
        Returns True if successful, False otherwise.
        """
        try:
            # Read the file content
            with open(lua_file, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            
            # Fix common Lua compatibility issues
            content = self._fix_lua_content(content)
            
            # Load the chunk
            chunk_name = os.path.basename(lua_file).replace('.lua', '')
            
            # For templates, load and execute them to register in package.preload
            if 'templates' in lua_file:
                # Load template
                success = self.lua.load_chunk(chunk_name, content) == 0
                if success:
                    # Execute the template (it will register itself in package.preload)
                    success = self.lua.load_chunk_execute(chunk_name, content) == 0
                
                if success:
                    self.modules[lua_file] = {'path': lua_file, 'name': chunk_name, 'loaded': True, 'type': 'template'}
                    return True
                else:
                    self.failed_modules.append((lua_file, "Template execution failed"))
                    return False
            else:
                # Regular module - load and execute
                success = self.lua.load_chunk(chunk_name, content) == 0
                
                if success:
                    # Execute the module
                    success = self.lua.load_chunk_execute(chunk_name, content) == 0
                
                if success:
                    # Extract module info if available
                    module_info = self._extract_module_info(lua_file)
                    self.modules[lua_file] = module_info
                    return True
                else:
                    self.failed_modules.append((lua_file, "Execution failed"))
                    return False
                
        except Exception as e:
            self.failed_modules.append((lua_file, str(e)))
            return False
    
    def _fix_lua_content(self, content: str) -> str:
        """
        Fixes common Lua compatibility issues.
        - Removes BOM markers
        - Fixes const variable declarations (Lua 5.2+ syntax)
        - Adds missing require wrappers
        """
        # Remove UTF-8 BOM if present
        if content.startswith('\ufeff'):
            content = content[1:]
        
        # Fix const declarations (Lua 5.2+ feature that may not be supported)
        # Replace: local const VAR = value
        # With:    local VAR = value
        import re
        content = re.sub(r'\blocal\s+const\s+', 'local ', content)
        
        return content
    
    def _extract_module_info(self, lua_file: str) -> dict:
        """Extracts basic information about a module."""
        info = {
            'path': lua_file,
            'name': os.path.basename(lua_file).replace('.lua', ''),
            'loaded': True
        }
        
        # Try to get module name from globals if available
        try:
            # Check if module registered itself
            pass
        except:
            pass
        
        return info
    
    def load_all_modules(self, lua_dir: str) -> dict:
        """
        Discovers and loads all Lua modules from directory.
        Returns dict with total, loaded, failed counts
        """
        print(f"Discovering modules in: {lua_dir}")
        
        templates, modules = self.discover_modules(lua_dir)
        all_files = templates + modules
        total = len(all_files)
        print(f"Found {total} potential modules ({len(templates)} templates, {len(modules)} modules)")
        
        success_count = 0
        for i, module_path in enumerate(all_files, 1):
            status = "✓" if self.load_module(module_path) else "✗"
            module_name = os.path.basename(module_path)
            print(f"[{i}/{total}] {status} {module_name}")
            if status == "✓":
                success_count += 1
        
        return {
            'total': total,
            'loaded': success_count,
            'failed': len(self.failed_modules),
            'failed_list': self.failed_modules[:10]  # First 10 failures
        }


def main():
    """Test module loading."""
    loader = ModuleLoader()
    
    # Test with actual FMD lua directory
    lua_dirs = [
        '/workspace/lua',
        '../lua',
        '../../lua'
    ]
    
    lua_dir = None
    for dir_path in lua_dirs:
        if os.path.exists(dir_path):
            lua_dir = dir_path
            break
    
    if not lua_dir:
        print("No Lua directory found. Testing with basic functionality...")
        # Create a simple test
        test_code = """
        -- Test module
        local TestModule = {}
        TestModule.Name = "Test"
        TestModule.Version = "1.0"
        
        function TestModule.Initialize()
            return true
        end
        
        return TestModule
        """
        
        success = loader.lua.load_string(test_code, "test_module")
        if success:
            success = loader.lua.execute_chunk("test_module")
        
        if success:
            print("✅ Basic module loading works!")
        else:
            print("❌ Module loading failed")
        return
    
    print(f"\nLoading modules from: {lua_dir}\n")
    stats = loader.load_all_modules(lua_dir)
    
    print(f"\n{'='*60}")
    print(f"Results: {stats['loaded']}/{stats['total']} modules loaded successfully ({stats['loaded']/stats['total']*100:.1f}%)")
    
    if stats['failed'] > 0:
        print(f"\nFailed modules ({stats['failed']}):")
        for path, error in stats.get('failed_list', [])[:10]:  # Show first 10 failures
            print(f"  - {os.path.basename(path)}: {error}")
        if stats['failed'] > 10:
            print(f"  ... and {stats['failed'] - 10} more")
    
    print(f"\n✅ Module loader test complete!")


if __name__ == "__main__":
    main()
