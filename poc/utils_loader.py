"""
Utility Module Loader - Loads FMD utility Lua modules (json, lzstring, etc.)
Equivalent to: Loading utils/*.lua files in Pascal version
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lua_handler import LuaHandler


class UtilsLoader:
    """Loads utility Lua modules and makes them available via require()."""
    
    def __init__(self, lua_handler: LuaHandler):
        self.lua = lua_handler
        self.utils_dir = None
    
    def discover_utils(self, lua_base_dir: str) -> list:
        """Finds all utility .lua files."""
        utils_path = Path(lua_base_dir) / "utils"
        if not utils_path.exists():
            return []
        
        return sorted([str(f) for f in utils_path.glob("*.lua")])
    
    def load_utils(self, lua_base_dir: str) -> int:
        """
        Loads all utility modules.
        Returns count of successfully loaded utilities.
        """
        utils_path = Path(lua_base_dir) / "utils"
        if not utils_path.exists():
            print(f"Utils directory not found: {utils_path}")
            return 0
        
        self.utils_dir = str(utils_path)
        loaded_count = 0
        loaded_modules = []
        
        # First setup package.path
        self._setup_package_path(str(utils_path))
        
        # Load each utility file
        for util_file in utils_path.glob("*.lua"):
            try:
                with open(util_file, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                
                # Fix BOM and const issues
                if content.startswith('\ufeff'):
                    content = content[1:]
                content = content.replace('local const ', 'local ')
                
                # Create module name (e.g., "utils.json")
                module_name = f"utils.{util_file.stem}"
                
                # Load the chunk
                success = self.lua.load_chunk(module_name, content) == 0
                
                if success:
                    print(f"✓ Loaded {module_name}")
                    loaded_count += 1
                    loaded_modules.append(module_name)
                else:
                    print(f"✗ Failed to load {module_name}")
                    
            except Exception as e:
                print(f"✗ Error loading {util_file.name}: {e}")
        
        # Register loaded modules in package.preload
        self._register_in_preload(loaded_modules)
        
        return loaded_count
    
    def _register_in_preload(self, module_names: list):
        """Register loaded modules in package.preload for require() to find them."""
        for module_name in module_names:
            try:
                self.lua.lua.execute(f"""
                    if package.loaded['{module_name}'] then
                        package.preload['{module_name}'] = function() 
                            return package.loaded['{module_name}'] 
                        end
                    end
                """)
            except:
                pass
    
    def _setup_package_path(self, utils_path: str):
        """Configures Lua's package.path to find utility modules."""
        # Add utils directory to package.path for require()
        self.lua.lua.execute(f"""
            local utils_dir = "{utils_path}"
            -- Add to package.path for ?.lua pattern (not utils.?.lua)
            if not string.find(package.path, utils_dir, 1, true) then
                package.path = utils_dir .. "/?.lua;" .. 
                               utils_dir .. "/?/init.lua;" .. package.path
            end
            print("Utils path configured: " .. utils_dir)
        """)


def main():
    """Test utility loading."""
    print("Testing Utility Module Loader...\n")
    
    lua = LuaHandler()
    loader = UtilsLoader(lua)
    
    # Find lua directory
    lua_dirs = ['/workspace/lua', '../lua', '../../lua']
    lua_dir = None
    for d in lua_dirs:
        if os.path.exists(d):
            lua_dir = d
            break
    
    if not lua_dir:
        print("No Lua directory found!")
        return
    
    print(f"Loading utilities from: {lua_dir}/utils\n")
    count = loader.load_utils(lua_dir)
    
    print(f"\n✅ Loaded {count} utility modules")
    
    # Test if json can be required
    print("\nTesting require('utils.json')...")
    try:
        lua.lua.execute("""
            local json = require('utils.json')
            if json then
                print("✓ utils.json loaded successfully via require()")
            else
                print("✗ utils.json returned nil")
            end
        """)
    except Exception as e:
        print(f"✗ Error requiring utils.json: {e}")


if __name__ == "__main__":
    main()
