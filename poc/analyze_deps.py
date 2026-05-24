#!/usr/bin/env python3
"""Analyze missing Lua dependencies to prioritize conversion."""

import os
import re
from lua_handler import LuaHandler

def analyze_missing_deps():
    missing_deps = {}
    
    lua_dir = '/workspace/lua/modules'
    total_files = 0
    
    for root, dirs, files in os.walk(lua_dir):
        for file in files:
            if file.endswith('.lua'):
                total_files += 1
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8-sig') as f:
                        content = f.read()
                    
                    # Find all require statements
                    requires = re.findall(r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", content)
                    for req in requires:
                        # Normalize the require path
                        normalized = req
                        if req.startswith('utils.'):
                            normalized = req[6:]  # utils.json -> json
                        elif req.startswith('templates.'):
                            normalized = req[10:]  # templates.Madara -> Madara
                        elif req == 'fmd.crypto':
                            normalized = 'fmd_crypto'
                        
                        # Check if we can load it
                        lua = LuaHandler()
                        lua.init_state()
                        try:
                            lua.execute(f"local status, err = pcall(function() require('{normalized}') end); if not status then error(err) end")
                        except Exception as e:
                            err_msg = str(e)
                            if 'module' in err_msg.lower() or 'not found' in err_msg.lower():
                                key = normalized
                                if key not in missing_deps:
                                    missing_deps[key] = []
                                missing_deps[key].append(file)
                        lua.close_state()
                except Exception:
                    pass
    
    # Sort by frequency
    sorted_deps = sorted(missing_deps.items(), key=lambda x: len(x[1]), reverse=True)
    
    print('=== MISSING DEPENDENCIES ANALYSIS ===')
    print(f'Total Lua files scanned: {total_files}')
    print(f'Total unique missing modules: {len(sorted_deps)}')
    print()
    
    for dep, files in sorted_deps[:30]:  # Top 30
        print(f'{dep}: missing in {len(files)} files')
        if len(files) <= 5:
            print(f'  Files: {", ".join(files)}')
        else:
            print(f'  Files: {", ".join(files[:3])} ... and {len(files)-3} more')
        print()
    
    return sorted_deps

if __name__ == '__main__':
    analyze_missing_deps()
