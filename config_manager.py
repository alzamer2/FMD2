"""
Configuration Manager
Replaces: FMDOptions.pas, IniFiles unit
Handles: Loading/Saving settings, Global state
"""
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages application configuration.
    In Pascal: Uses TIniFile. 
    In Python: Uses JSON for better readability and nested support.
    """
    
    DEFAULT_CONFIG = {
        "general": {
            "max_threads": 5,
            "save_to": "./downloads",
            "create_folder_per_chapter": True,
            "language": "en",
            "dark_mode": False
        },
        "network": {
            "timeout": 30,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "proxy": "",
            "retry_count": 3
        },
        "lua": {
            "module_path": "./lua",
            "enabled_modules": []
        },
        "database": {
            "path": "./data/fmd.db"
        }
    }

    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from disk or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
                
                # Merge with defaults to ensure new keys exist if version changed
                self._merge_defaults()
            except Exception as e:
                logger.error(f"Failed to load config: {e}. Using defaults.")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            logger.info("Config file not found. Creating default.")
            self.config = self.DEFAULT_CONFIG.copy()
            self.save()

    def _merge_defaults(self) -> None:
        """Recursively merge current config with defaults."""
        for section, values in self.DEFAULT_CONFIG.items():
            if section not in self.config:
                self.config[section] = values
            elif isinstance(values, dict):
                for key, val in values.items():
                    if key not in self.config[section]:
                        self.config[section][key] = val

    def save(self) -> None:
        """Save current configuration to disk."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a value from config."""
        try:
            return self.config.get(section, {}).get(key, default)
        except Exception:
            return default

    def set(self, section: str, key: str, value: Any) -> None:
        """Set a value in config and save."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save()

    @property
    def save_directory(self) -> Path:
        return Path(self.get("general", "save_to", "./downloads"))

    @property
    def lua_module_path(self) -> Path:
        return Path(self.get("lua", "module_path", "./lua"))

# Global instance singleton
_config_instance: Optional[ConfigManager] = None

def get_config() -> ConfigManager:
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance

if __name__ == "__main__":
    # Test the ConfigManager
    logging.basicConfig(level=logging.INFO)
    
    cfg = ConfigManager("test_config.json")
    
    # Test reading
    threads = cfg.get("general", "max_threads")
    print(f"Max Threads: {threads}")
    
    # Test writing
    cfg.set("general", "max_threads", 10)
    cfg.set("network", "user_agent", "CustomBot/1.0")
    
    # Verify persistence
    cfg2 = ConfigManager("test_config.json")
    assert cfg2.get("general", "max_threads") == 10
    assert cfg2.get("network", "user_agent") == "CustomBot/1.0"
    
    print("✅ ConfigManager tests passed!")
    
    # Cleanup
    os.remove("test_config.json")
