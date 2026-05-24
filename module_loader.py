"""
Website Module Loader
Replaces: WebsiteModules.pas, LuaHandler.pas (module loading part)
Handles: Loading Lua scraper modules, managing website connectors
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from lupa import LuaRuntime

logger = logging.getLogger(__name__)

class WebsiteModule:
    """Represents a loaded Lua website scraper module."""
    
    def __init__(self, name: str, lua_state: Any, file_path: str):
        self.name = name
        self.lua_state = lua_state
        self.file_path = file_path
        self.enabled = True
        
        # Extract module info from Lua table
        self._load_module_info()
    
    def _load_module_info(self) -> None:
        """Load metadata from the Lua module's 'website' table."""
        try:
            lua_data = self.lua_state
            if hasattr(lua_data, 'website'):
                ws = lua_data.website
                self.website_name = str(getattr(ws, 'name', self.name))
                self.website_url = str(getattr(ws, 'url', ''))
                self.website_lang = str(getattr(ws, 'lang', 'en'))
                self.version = str(getattr(ws, 'version', '1.0'))
            else:
                self.website_name = self.name
                self.website_url = ""
                self.website_lang = "en"
                self.version = "1.0"
        except Exception as e:
            logger.warning(f"Could not load module info for {self.name}: {e}")
            self.website_name = self.name
            self.website_url = ""
            self.website_lang = "en"
            self.version = "1.0"
    
    def __repr__(self) -> str:
        return f"WebsiteModule({self.website_name}, {self.website_lang}, v{self.version})"


class ModuleLoader:
    """
    Loads and manages Lua website scraper modules.
    In Pascal: Uses TLua, file scanning, dynamic loading.
    In Python: Uses lupa for Lua integration with automatic discovery.
    """
    
    def __init__(self, module_path: str = "./lua"):
        self.module_path = Path(module_path)
        self.modules: Dict[str, WebsiteModule] = {}
        self.lua_runtime = LuaRuntime(unpack_returned_tuples=True)
        
        # Configure Lua package path to find templates and utils
        self._setup_lua_package_path()
    
    def _setup_lua_package_path(self) -> None:
        """Configure Lua's package.path to find templates and utils directories."""
        # For Lua's require('templates.MangaHub'), we need the parent directory of 'templates'
        # The pattern is: require('templates.X') looks for templates/X.lua in package.path
        
        # Add the lua directory itself so 'templates.X' resolves to ./lua/templates/X.lua
        lua_base = self.module_path  # e.g., ./lua
        
        # Execute Lua code to configure package.path
        setup_code = f"""
package.path = package.path .. ";{lua_base}/?.lua"
"""
        self.lua_runtime.execute(setup_code)
        
        logger.debug(f"Lua package.path configured to include {lua_base}/?.lua")
        
    def discover_modules(self) -> List[str]:
        """Find all .lua files in the module directory."""
        lua_files = []
        
        if not self.module_path.exists():
            logger.warning(f"Module path does not exist: {self.module_path}")
            return lua_files
        
        # Search recursively for .lua files
        for lua_file in self.module_path.rglob("*.lua"):
            # Skip utility files (usually in utils/ folder)
            if 'utils' in lua_file.parts or lua_file.name.startswith('_'):
                continue
            lua_files.append(str(lua_file))
        
        logger.info(f"Discovered {len(lua_files)} potential module files")
        return lua_files
    
    def load_module(self, file_path: str) -> Optional[WebsiteModule]:
        """Load a single Lua module file."""
        try:
            path = Path(file_path)
            module_name = path.stem  # filename without .lua
            
            logger.debug(f"Loading module: {module_name} from {file_path}")
            
            # Read Lua file
            with open(file_path, 'r', encoding='utf-8') as f:
                lua_code = f.read()
            
            # Execute Lua code in isolated environment
            lua_state = self.lua_runtime.execute(lua_code)
            
            # Create module wrapper
            module = WebsiteModule(module_name, lua_state, file_path)
            
            self.modules[module_name] = module
            logger.info(f"Loaded module: {module.website_name} ({module.website_lang})")
            return module
            
        except Exception as e:
            logger.error(f"Failed to load module {file_path}: {e}")
            return None
    
    def load_all_modules(self) -> int:
        """Load all discovered modules."""
        lua_files = self.discover_modules()
        loaded_count = 0
        
        for file_path in lua_files:
            if self.load_module(file_path):
                loaded_count += 1
        
        logger.info(f"Loaded {loaded_count}/{len(lua_files)} modules successfully")
        return loaded_count
    
    def get_module(self, name: str) -> Optional[WebsiteModule]:
        """Get a loaded module by name."""
        return self.modules.get(name)
    
    def get_enabled_modules(self) -> List[WebsiteModule]:
        """Get all enabled modules."""
        return [m for m in self.modules.values() if m.enabled]
    
    def enable_module(self, name: str) -> bool:
        """Enable a module."""
        if name in self.modules:
            self.modules[name].enabled = True
            return True
        return False
    
    def disable_module(self, name: str) -> bool:
        """Disable a module."""
        if name in self.modules:
            self.modules[name].enabled = False
            return True
        return False
    
    def search_manga(self, module_name: str, query: str) -> Any:
        """
        Call a module's search function.
        Expected Lua function: search(query: string) -> table
        """
        module = self.get_module(module_name)
        if not module:
            raise ValueError(f"Module {module_name} not found")
        
        try:
            lua_state = module.lua_state
            if hasattr(lua_state, 'search'):
                return lua_state.search(query)
            else:
                logger.warning(f"Module {module_name} has no 'search' function")
                return None
        except Exception as e:
            logger.error(f"Search failed in {module_name}: {e}")
            raise
    
    def get_manga_info(self, module_name: str, manga_id: str) -> Any:
        """
        Call a module's getMangaInfo function.
        Expected Lua function: getMangaInfo(manga_id: string) -> table
        """
        module = self.get_module(module_name)
        if not module:
            raise ValueError(f"Module {module_name} not found")
        
        try:
            lua_state = module.lua_state
            if hasattr(lua_state, 'getMangaInfo'):
                return lua_state.getMangaInfo(manga_id)
            else:
                logger.warning(f"Module {module_name} has no 'getMangaInfo' function")
                return None
        except Exception as e:
            logger.error(f"getMangaInfo failed in {module_name}: {e}")
            raise
    
    def get_chapter_list(self, module_name: str, manga_id: str) -> Any:
        """
        Call a module's getChapterList function.
        Expected Lua function: getChapterList(manga_id: string) -> table
        """
        module = self.get_module(module_name)
        if not module:
            raise ValueError(f"Module {module_name} not found")
        
        try:
            lua_state = module.lua_state
            if hasattr(lua_state, 'getChapterList'):
                return lua_state.getChapterList(manga_id)
            else:
                logger.warning(f"Module {module_name} has no 'getChapterList' function")
                return None
        except Exception as e:
            logger.error(f"getChapterList failed in {module_name}: {e}")
            raise
    
    def get_page_urls(self, module_name: str, manga_id: str, chapter_id: str) -> Any:
        """
        Call a module's getPageUrls function.
        Expected Lua function: getPageUrls(manga_id: string, chapter_id: string) -> table
        """
        module = self.get_module(module_name)
        if not module:
            raise ValueError(f"Module {module_name} not found")
        
        try:
            lua_state = module.lua_state
            if hasattr(lua_state, 'getPageUrls'):
                return lua_state.getPageUrls(manga_id, chapter_id)
            else:
                logger.warning(f"Module {module_name} has no 'getPageUrls' function")
                return None
        except Exception as e:
            logger.error(f"getPageUrls failed in {module_name}: {e}")
            raise


# Global instance singleton
_loader_instance: Optional[ModuleLoader] = None

def get_module_loader() -> ModuleLoader:
    global _loader_instance
    if _loader_instance is None:
        from config_manager import get_config
        config = get_config()
        module_path = config.get("lua", "module_path", "./lua")
        _loader_instance = ModuleLoader(module_path)
    return _loader_instance

if __name__ == "__main__":
    # Test the ModuleLoader
    logging.basicConfig(level=logging.INFO)
    
    # Check if lua directory exists
    lua_dir = Path("./lua")
    if not lua_dir.exists():
        print("⚠️ No ./lua directory found. Creating test structure...")
        lua_dir.mkdir()
        utils_dir = lua_dir / "utils"
        utils_dir.mkdir()
        
        # Copy json.lua if it exists elsewhere
        existing_json = Path("./workspace/lua/utils/json.lua")
        if existing_json.exists():
            import shutil
            shutil.copy(existing_json, utils_dir / "json.lua")
    
    loader = ModuleLoader("./lua")
    
    # Try to load modules
    count = loader.load_all_modules()
    print(f"Loaded {count} modules")
    
    # List loaded modules
    for name, module in loader.modules.items():
        print(f"  - {module}")
    
    print("✅ ModuleLoader tests completed!")
