"""
Free Manga Downloader - Python Migration
HTTP Client Module

Python equivalent of httpsendthread.pas
Provides HTTP client functionality with cookies, redirects, compression, and retries.
"""

import sys
import os
import time
import gzip
import brotli
import zstandard
from typing import Optional, Dict, Any, Callable, List
from urllib.parse import urlparse, urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import http.cookiejar as cookiejar
from datetime import datetime, timedelta
import re


class HTTPQueue:
    """
    Python equivalent of THTTPQueue
    Manages connection pooling and limits
    """
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._active_connections = 0
        import threading
        self._lock = threading.Lock()
    
    def add_connection(self):
        """Add a connection to the pool"""
        with self._lock:
            while self._active_connections >= self.max_connections:
                time.sleep(0.1)
            self._active_connections += 1
    
    def done_connection(self):
        """Release a connection from the pool"""
        with self._lock:
            self._active_connections -= 1
    
    @property
    def active_connections(self) -> int:
        """Get number of active connections"""
        return self._active_connections


class HTTPSendThread:
    """
    Python equivalent of THTTPSendThread
    
    Provides HTTP client functionality with:
    - Cookie management
    - Redirect following
    - GZIP/Brotli/Zstd compression
    - Retry logic
    - Custom headers
    - Timeout management
    """
    
    def __init__(self, owner=None):
        """
        Initialize HTTP client
        
        Args:
            owner: Owner object (optional)
        """
        self._owner = owner
        self._running = False
        self._url = ""
        self._retry_count = 3
        self._compress = True
        self._follow_redirection = True
        self._max_redirect = 10
        self._allow_server_error_response = False
        self._enabled_cookies = True
        self._clear_cookies = False
        self._timeout = 30000  # milliseconds
        
        # Session with cookie jar
        self._session = requests.Session()
        if self._enabled_cookies:
            self._session.cookies = cookiejar.CookieJar()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self._retry_count,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        
        # Default headers
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        # Event callbacks
        self.on_method: Optional[Callable] = None
        self.on_request: Optional[Callable] = None
        self.on_redirect: Optional[Callable] = None
        
        # Response data
        self.document = b""
        self.headers = {}
        self.status_code = 0
        self.mimetype = ""
        self.charset = "utf-8"
    
    @property
    def timeout(self) -> int:
        """Get timeout in milliseconds"""
        return self._timeout
    
    @timeout.setter
    def timeout(self, value: int):
        """Set timeout in milliseconds"""
        self._timeout = value
    
    @property
    def running(self) -> bool:
        """Check if HTTP client is running"""
        return self._running
    
    @property
    def url(self) -> str:
        """Get current URL"""
        return self._url
    
    @property
    def compress(self) -> bool:
        """Check if compression is enabled"""
        return self._compress
    
    @compress.setter
    def compress(self, value: bool):
        """Enable/disable compression"""
        self._compress = value
    
    @property
    def follow_redirection(self) -> bool:
        """Check if redirects are followed"""
        return self._follow_redirection
    
    @follow_redirection.setter
    def follow_redirection(self, value: bool):
        """Enable/disable redirect following"""
        self._follow_redirection = value
    
    @property
    def max_redirect(self) -> int:
        """Get maximum redirect count"""
        return self._max_redirect
    
    @max_redirect.setter
    def max_redirect(self, value: int):
        """Set maximum redirect count"""
        self._max_redirect = value
    
    @property
    def enabled_cookies(self) -> bool:
        """Check if cookies are enabled"""
        return self._enabled_cookies
    
    @enabled_cookies.setter
    def enabled_cookies(self, value: bool):
        """Enable/disable cookies"""
        self._enabled_cookies = value
        if not value:
            self._session.cookies = cookiejar.CookieJar()
    
    @property
    def clear_cookies(self) -> bool:
        """Check if cookies should be cleared"""
        return self._clear_cookies
    
    @clear_cookies.setter
    def clear_cookies(self, value: bool):
        """Set clear cookies flag"""
        self._clear_cookies = value
        if value:
            self._session.cookies.clear()
    
    def _normalize_headers(self):
        """Normalize headers for request"""
        if self._compress:
            self._headers['Accept-Encoding'] = 'gzip, deflate, br'
        else:
            self._headers.pop('Accept-Encoding', None)
    
    def _set_http_cookies(self):
        """Set HTTP cookies from cookie manager (placeholder)"""
        # Cookies are managed automatically by requests.Session
        pass
    
    def _decompress_content(self, content: bytes, encoding: str) -> bytes:
        """
        Decompress content based on encoding
        
        Args:
            content: Compressed content
            encoding: Compression type
            
        Returns:
            Decompressed content
        """
        try:
            if encoding == 'gzip':
                return gzip.decompress(content)
            elif encoding == 'deflate':
                return zlib.decompress(content)
            elif encoding == 'br':
                return brotli.decompress(content)
            elif encoding.startswith('zstd'):
                dctx = zstandard.ZstdDecompressor()
                return dctx.decompress(content)
            else:
                return content
        except Exception as e:
            print(f"Decompression error: {e}")
            return content
    
    def http_method(self, method: str, url: str) -> bool:
        """
        Execute HTTP method
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            
        Returns:
            True on success
        """
        return self.http_request(method, url)
    
    def http_request(self, method: str, url: str, response_obj: Any = None) -> bool:
        """
        Execute HTTP request with full processing
        
        Args:
            method: HTTP method
            url: URL to request
            response_obj: Optional response object
            
        Returns:
            True on success
        """
        self._running = True
        self._url = url
        
        try:
            # Call event handler if set
            if self.on_method:
                self.on_method(self)
            
            # Normalize headers
            self._normalize_headers()
            
            # Set cookies
            if self._enabled_cookies:
                self._set_http_cookies()
            
            # Prepare request
            timeout_sec = self._timeout / 1000.0
            allow_redirects = self._follow_redirection
            
            # Execute request
            resp = self._session.request(
                method=method.upper(),
                url=url,
                headers=self._headers,
                timeout=timeout_sec,
                allow_redirects=allow_redirects,
                stream=False
            )
            
            # Store response
            self.status_code = resp.status_code
            self.headers = dict(resp.headers)
            self.mimetype = resp.headers.get('Content-Type', '').split(';')[0].strip()
            
            # Extract charset from Content-Type
            content_type = resp.headers.get('Content-Type', '')
            if 'charset=' in content_type:
                self.charset = content_type.split('charset=')[-1].split(';')[0].strip()
            
            # Get content
            content = resp.content
            
            # Decompress if needed
            content_encoding = resp.headers.get('Content-Encoding', '')
            if content_encoding and self._compress:
                content = self._decompress_content(content, content_encoding)
            
            self.document = content
            
            # Handle redirects manually if needed
            if resp.is_redirect and self._follow_redirection:
                location = resp.headers.get('Location', '')
                if location and self.on_redirect:
                    self.on_redirect(self, location)
            
            # Call request event handler
            if self.on_request:
                result = self.on_request(self, method, url, response_obj)
                return result
            
            return resp.ok or self._allow_server_error_response
            
        except Exception as e:
            print(f"HTTP request error: {e}")
            return False
        finally:
            self._running = False
    
    def head(self, url: str, response_obj: Any = None) -> bool:
        """Execute HEAD request"""
        return self.http_request('HEAD', url, response_obj)
    
    def get(self, url: str, response_obj: Any = None) -> bool:
        """Execute GET request"""
        return self.http_request('GET', url, response_obj)
    
    def post(self, url: str, data: Any = None, response_obj: Any = None) -> bool:
        """Execute POST request"""
        self._running = True
        self._url = url
        
        try:
            self._normalize_headers()
            timeout_sec = self._timeout / 1000.0
            
            resp = self._session.post(
                url=url,
                data=data,
                headers=self._headers,
                timeout=timeout_sec,
                allow_redirects=self._follow_redirection
            )
            
            self.status_code = resp.status_code
            self.headers = dict(resp.headers)
            self.document = resp.content
            
            return resp.ok or self._allow_server_error_response
            
        except Exception as e:
            print(f"POST request error: {e}")
            return False
        finally:
            self._running = False
    
    def put(self, url: str, data: Any = None, response_obj: Any = None) -> bool:
        """Execute PUT request"""
        return self.http_request('PUT', url, response_obj)
    
    def delete(self, url: str, response_obj: Any = None) -> bool:
        """Execute DELETE request"""
        return self.http_request('DELETE', url, response_obj)
    
    def parse_http_cookies(self):
        """Parse HTTP cookies from response headers"""
        # Cookies are automatically managed by requests
        pass
    
    def add_cookie(self, name: str, value: str, domain: str = None, path: str = '/'):
        """
        Add a cookie to the cookie jar
        
        Args:
            name: Cookie name
            value: Cookie value
            domain: Cookie domain
            path: Cookie path
        """
        if domain is None:
            # Extract domain from current URL
            parsed = urlparse(self._url)
            domain = parsed.hostname
        
        cookie = cookiejar.Cookie(
            version=0,
            name=name,
            value=value,
            port=None,
            port_specified=False,
            domain=domain,
            domain_specified=True,
            domain_initial_dot=False,
            path=path,
            path_specified=True,
            secure=False,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={}
        )
        self._session.cookies.set_cookie(cookie)
    
    def clear_all_cookies(self):
        """Clear all cookies"""
        self._session.cookies.clear()
    
    def get_document_string(self) -> str:
        """Get document content as string"""
        try:
            return self.document.decode(self.charset, errors='replace')
        except:
            return self.document.decode('utf-8', errors='replace')
    
    def destroy(self):
        """Cleanup resources"""
        self._session.close()


# Convenience functions
def http_get(url: str, headers: Dict = None, timeout: int = 30000) -> Optional[str]:
    """
    Simple HTTP GET request
    
    Args:
        url: URL to fetch
        headers: Optional headers
        timeout: Timeout in milliseconds
        
    Returns:
        Response text or None on error
    """
    http = HTTPSendThread()
    if headers:
        http._headers.update(headers)
    http.timeout = timeout
    
    if http.get(url):
        return http.get_document_string()
    return None


def http_post(url: str, data: Dict = None, headers: Dict = None, 
              timeout: int = 30000) -> Optional[str]:
    """
    Simple HTTP POST request
    
    Args:
        url: URL to post to
        data: POST data
        headers: Optional headers
        timeout: Timeout in milliseconds
        
    Returns:
        Response text or None on error
    """
    http = HTTPSendThread()
    if headers:
        http._headers.update(headers)
    http.timeout = timeout
    
    if http.post(url, data=data):
        return http.get_document_string()
    return None


# Test and example usage
if __name__ == '__main__':
    print("Testing HTTPSendThread...")
    
    # Test 1: Basic GET request
    http = HTTPSendThread()
    print("✓ HTTPSendThread created")
    
    # Test 2: Simple request to httpbin
    test_url = "https://httpbin.org/get"
    print(f"Testing GET request to {test_url}...")
    
    if http.get(test_url):
        print(f"✓ GET successful, status: {http.status_code}")
        print(f"  Content length: {len(http.document)} bytes")
    else:
        print("✗ GET failed")
    
    # Test 3: Check headers
    print(f"✓ Headers received: {len(http.headers)} headers")
    
    # Test 4: Cookie management
    http.add_cookie("test_cookie", "test_value", domain="httpbin.org")
    print("✓ Cookie added")
    
    # Test 5: POST request
    post_url = "https://httpbin.org/post"
    print(f"Testing POST request to {post_url}...")
    
    if http.post(post_url, data={"key": "value"}):
        print(f"✓ POST successful, status: {http.status_code}")
    else:
        print("✗ POST failed")
    
    # Test 6: Compression
    http.compress = True
    print("✓ Compression enabled")
    
    # Test 7: Timeout setting
    http.timeout = 5000
    print(f"✓ Timeout set to {http.timeout}ms")
    
    http.destroy()
    print("\n✅ HTTP client tests completed!")
