"""
HTTP Cookie Manager
Equivalent to: httpcookiemanager.pas

Handles cookie storage, loading, saving, and management for HTTP requests.
Supports Netscape cookie format and domain/path matching.
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from dataclasses import dataclass, asdict


@dataclass
class Cookie:
    """Represents a single HTTP cookie"""
    name: str
    value: str
    domain: str = ""
    path: str = "/"
    expires: int = 0  # Unix timestamp, 0 = session cookie
    secure: bool = False
    httponly: bool = False
    
    def is_expired(self) -> bool:
        """Check if cookie has expired"""
        if self.expires == 0:
            return False  # Session cookies don't expire
        return time.time() > self.expires
    
    def matches_url(self, url: str) -> bool:
        """Check if cookie matches the given URL"""
        parsed = urlparse(url)
        host = parsed.netloc.split(':')[0]  # Remove port if present
        
        # Check domain
        if self.domain:
            if not (host == self.domain or host.endswith('.' + self.domain)):
                return False
        
        # Check path
        if not parsed.path.startswith(self.path):
            return False
        
        # Check secure flag
        if self.secure and parsed.scheme != 'https':
            return False
            
        return True
    
    def to_netscape(self) -> str:
        """Convert to Netscape cookie file format"""
        domain = self.domain
        if not domain.startswith('.'):
            domain = '.' + domain
            
        flag = "TRUE" if self.domain.startswith('.') else "FALSE"
        if self.secure:
            flag += "\tTRUE"
        else:
            flag += "\tFALSE"
            
        expiry = str(self.expires) if self.expires > 0 else "0"
        
        return f"{domain}\t{flag}\t{self.path}\t{self.secure!s}\t{expiry}\t{self.name}\t{self.value}"
    
    @classmethod
    def from_netscape(cls, line: str) -> Optional['Cookie']:
        """Parse from Netscape cookie file format"""
        parts = line.strip().split('\t')
        if len(parts) < 7:
            return None
            
        try:
            domain = parts[0]
            secure = parts[3].upper() == 'TRUE'
            expires = int(parts[4]) if parts[4] != '0' else 0
            
            return cls(
                name=parts[5],
                value=parts[6],
                domain=domain.lstrip('.'),
                path=parts[2],
                expires=expires,
                secure=secure,
                httponly=False  # Netscape format doesn't support httponly
            )
        except (ValueError, IndexError):
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Cookie':
        """Create from dictionary"""
        return cls(**data)


class CookieManager:
    """
    Manages HTTP cookies for multiple domains.
    Equivalent to THTTPCookieManager in Pascal.
    """
    
    def __init__(self, cookie_file: Optional[str] = None):
        """
        Initialize cookie manager.
        
        Args:
            cookie_file: Path to cookie file (Netscape format or JSON)
        """
        self.cookies: Dict[str, List[Cookie]] = {}  # domain -> list of cookies
        self.cookie_file = cookie_file
        
        if cookie_file and os.path.exists(cookie_file):
            self.load(cookie_file)
    
    def add_cookie(self, cookie: Cookie) -> None:
        """Add or update a cookie"""
        domain = cookie.domain.lower()
        if not domain:
            domain = "default"
            
        if domain not in self.cookies:
            self.cookies[domain] = []
        
        # Remove existing cookie with same name and path
        self.cookies[domain] = [
            c for c in self.cookies[domain] 
            if not (c.name == cookie.name and c.path == cookie.path)
        ]
        
        # Add new cookie if not expired
        if not cookie.is_expired():
            self.cookies[domain].append(cookie)
    
    def add_cookie_from_header(self, set_cookie_header: str, url: str) -> None:
        """
        Parse Set-Cookie header and add cookie.
        
        Args:
            set_cookie_header: Value of Set-Cookie header
            url: URL that set the cookie
        """
        parsed = urlparse(url)
        host = parsed.netloc.split(':')[0]
        
        # Parse cookie name=value
        parts = set_cookie_header.split(';')
        name_value = parts[0].strip()
        
        if '=' not in name_value:
            return
            
        name, value = name_value.split('=', 1)
        name = name.strip()
        value = value.strip()
        
        cookie = Cookie(
            name=name,
            value=value,
            domain=host,
            path='/',
            secure=(parsed.scheme == 'https'),
            httponly=False
        )
        
        # Parse attributes
        for part in parts[1:]:
            part = part.strip().lower()
            if part.startswith('expires='):
                # Parse expires date (simplified)
                pass
            elif part.startswith('max-age='):
                try:
                    max_age = int(part.split('=')[1])
                    cookie.expires = int(time.time()) + max_age
                except ValueError:
                    pass
            elif part == 'secure':
                cookie.secure = True
            elif part == 'httponly':
                cookie.httponly = True
            elif part.startswith('path='):
                cookie.path = part.split('=')[1]
            elif part.startswith('domain='):
                cookie.domain = part.split('=')[1].lstrip('.')
        
        self.add_cookie(cookie)
    
    def get_cookies_for_url(self, url: str) -> List[Cookie]:
        """Get all valid cookies for a URL"""
        result = []
        parsed = urlparse(url)
        host = parsed.netloc.split(':')[0]
        
        # Check all domains that might match
        for domain, cookies in self.cookies.items():
            if host == domain or host.endswith('.' + domain):
                for cookie in cookies:
                    if not cookie.is_expired() and cookie.matches_url(url):
                        result.append(cookie)
        
        return result
    
    def get_cookie_string(self, url: str) -> str:
        """
        Get cookie string for HTTP request header.
        
        Returns:
            String in format: "name1=value1; name2=value2"
        """
        cookies = self.get_cookies_for_url(url)
        if not cookies:
            return ""
        
        return "; ".join(f"{c.name}={c.value}" for c in cookies)
    
    def remove_expired(self) -> int:
        """Remove all expired cookies. Returns count of removed cookies."""
        removed = 0
        for domain in list(self.cookies.keys()):
            before = len(self.cookies[domain])
            self.cookies[domain] = [c for c in self.cookies[domain] if not c.is_expired()]
            removed += before - len(self.cookies[domain])
            
            # Remove empty domains
            if not self.cookies[domain]:
                del self.cookies[domain]
        
        return removed
    
    def clear(self) -> None:
        """Clear all cookies"""
        self.cookies.clear()
    
    def clear_domain(self, domain: str) -> None:
        """Clear all cookies for a specific domain"""
        domain = domain.lower()
        if domain in self.cookies:
            del self.cookies[domain]
    
    def save(self, filepath: Optional[str] = None, format: str = 'json') -> None:
        """
        Save cookies to file.
        
        Args:
            filepath: Path to save to (uses default if None)
            format: 'json' or 'netscape'
        """
        filepath = filepath or self.cookie_file
        if not filepath:
            raise ValueError("No filepath specified")
        
        # Remove expired cookies first
        self.remove_expired()
        
        if format == 'json':
            data = {
                domain: [c.to_dict() for c in cookies]
                for domain, cookies in self.cookies.items()
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        elif format == 'netscape':
            lines = ["# Netscape HTTP Cookie File"]
            for cookies in self.cookies.values():
                for cookie in cookies:
                    lines.append(cookie.to_netscape())
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
    
    def load(self, filepath: Optional[str] = None) -> bool:
        """
        Load cookies from file.
        
        Args:
            filepath: Path to load from (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        filepath = filepath or self.cookie_file
        if not filepath or not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Try JSON format first
            if content.startswith('{'):
                data = json.loads(content)
                self.cookies.clear()
                for domain, cookies_data in data.items():
                    self.cookies[domain] = [Cookie.from_dict(c) for c in cookies_data]
                return True
            
            # Try Netscape format
            self.cookies.clear()
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                cookie = Cookie.from_netscape(line)
                if cookie:
                    self.add_cookie(cookie)
            
            return True
        except Exception as e:
            print(f"Error loading cookies: {e}")
            return False
    
    def get_all_cookies(self) -> List[Cookie]:
        """Get all cookies (including expired)"""
        result = []
        for cookies in self.cookies.values():
            result.extend(cookies)
        return result
    
    def count(self) -> int:
        """Get total number of cookies"""
        return sum(len(cookies) for cookies in self.cookies.values())


# Convenience functions for Lua integration
def create_cookie_manager(cookie_file: Optional[str] = None) -> CookieManager:
    """Create a new cookie manager instance"""
    return CookieManager(cookie_file)


if __name__ == "__main__":
    # Test suite
    print("=" * 60)
    print("Testing HTTP Cookie Manager")
    print("=" * 60)
    
    # Test 1: Create and add cookies
    print("\n[Test 1] Creating cookies...")
    manager = CookieManager()
    
    cookie1 = Cookie(name="session", value="abc123", domain="example.com", path="/")
    cookie2 = Cookie(name="user", value="john", domain="example.com", path="/profile", secure=True)
    cookie3 = Cookie(name="temp", value="xyz", domain="test.com", path="/", expires=int(time.time()) - 100)  # Expired
    
    manager.add_cookie(cookie1)
    manager.add_cookie(cookie2)
    manager.add_cookie(cookie3)
    
    assert manager.count() == 2, "Should have 2 cookies (1 expired)"
    print("✓ Cookies added successfully")
    
    # Test 2: Get cookies for URL
    print("\n[Test 2] Getting cookies for URL...")
    cookies = manager.get_cookies_for_url("https://example.com/profile/settings")
    assert len(cookies) == 2, f"Should have 2 cookies, got {len(cookies)}"
    print(f"✓ Found {len(cookies)} cookies for URL")
    
    # Test 3: Cookie string
    print("\n[Test 3] Generating cookie string...")
    cookie_str = manager.get_cookie_string("https://example.com/profile")
    assert "session=abc123" in cookie_str, "Should contain session cookie"
    print(f"✓ Cookie string: {cookie_str}")
    
    # Test 4: Parse Set-Cookie header
    print("\n[Test 4] Parsing Set-Cookie header...")
    manager.add_cookie_from_header(
        "newcookie=newvalue; Path=/api; Secure; HttpOnly",
        "https://api.example.com/test"
    )
    cookies = manager.get_cookies_for_url("https://api.example.com/api/v1")
    assert any(c.name == "newcookie" for c in cookies), "Should have newcookie"
    print("✓ Set-Cookie header parsed successfully")
    
    # Test 5: Save and load (JSON)
    print("\n[Test 5] Saving and loading cookies (JSON)...")
    test_file = "/tmp/test_cookies.json"
    manager.save(test_file, format='json')
    
    manager2 = CookieManager()
    assert manager2.load(test_file), "Should load successfully"
    assert manager2.count() >= 2, "Should have loaded cookies"
    print(f"✓ Saved and loaded {manager2.count()} cookies")
    
    # Test 6: Save and load (Netscape)
    print("\n[Test 6] Saving and loading cookies (Netscape)...")
    test_file_ns = "/tmp/test_cookies.txt"
    manager.save(test_file_ns, format='netscape')
    
    manager3 = CookieManager()
    assert manager3.load(test_file_ns), "Should load successfully"
    print(f"✓ Loaded {manager3.count()} cookies from Netscape format")
    
    # Test 7: Remove expired
    print("\n[Test 7] Removing expired cookies...")
    initial_count = manager.count()
    removed = manager.remove_expired()
    print(f"✓ Removed {removed} expired cookies")
    
    # Test 8: Clear domain
    print("\n[Test 8] Clearing domain...")
    manager.clear_domain("test.com")
    print("✓ Domain cleared")
    
    # Cleanup
    os.remove(test_file)
    os.remove(test_file_ns)
    
    print("\n" + "=" * 60)
    print("All Cookie Manager tests passed! ✓")
    print("=" * 60)
