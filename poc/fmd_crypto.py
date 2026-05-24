"""
FMD Crypto Module Implementation
Equivalent to: fmd.crypto in Pascal/Lua bindings
Provides cryptographic functions for Lua scripts (AES, Base64, MD5, SHA, etc.)
"""

import base64
import hashlib
import hmac
from typing import Union, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

class FMDCrypto:
    """
    Python implementation of fmd.crypto for Lua scripts.
    Provides encryption, hashing, and encoding functions.
    """
    
    def __init__(self):
        self.backend = default_backend()
    
    # ==================== Base64 Functions ====================
    
    def base64_encode(self, data: Union[str, bytes]) -> str:
        """Encode data to Base64 string."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.b64encode(data).decode('utf-8')
    
    def base64_decode(self, data: str) -> str:
        """Decode Base64 string to original data."""
        decoded = base64.b64decode(data.encode('utf-8'))
        try:
            return decoded.decode('utf-8')
        except UnicodeDecodeError:
            # Return as hex if not valid UTF-8
            return decoded.hex()
    
    def base64_url_encode(self, data: Union[str, bytes]) -> str:
        """Encode data to URL-safe Base64 string."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')
    
    def base64_url_decode(self, data: str) -> str:
        """Decode URL-safe Base64 string."""
        # Add padding if needed
        padding_needed = 4 - (len(data) % 4)
        if padding_needed != 4:
            data += '=' * padding_needed
        decoded = base64.urlsafe_b64decode(data.encode('utf-8'))
        try:
            return decoded.decode('utf-8')
        except UnicodeDecodeError:
            return decoded.hex()
    
    # ==================== Hash Functions ====================
    
    def md5(self, data: Union[str, bytes]) -> str:
        """Calculate MD5 hash."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.md5(data).hexdigest()
    
    def sha1(self, data: Union[str, bytes]) -> str:
        """Calculate SHA1 hash."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha1(data).hexdigest()
    
    def sha256(self, data: Union[str, bytes]) -> str:
        """Calculate SHA256 hash."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()
    
    def sha512(self, data: Union[str, bytes]) -> str:
        """Calculate SHA512 hash."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha512(data).hexdigest()
    
    def hmac_md5(self, data: Union[str, bytes], key: Union[str, bytes]) -> str:
        """Calculate HMAC-MD5."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        if isinstance(key, str):
            key = key.encode('utf-8')
        return hmac.new(key, data, hashlib.md5).hexdigest()
    
    def hmac_sha1(self, data: Union[str, bytes], key: Union[str, bytes]) -> str:
        """Calculate HMAC-SHA1."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        if isinstance(key, str):
            key = key.encode('utf-8')
        return hmac.new(key, data, hashlib.sha1).hexdigest()
    
    def hmac_sha256(self, data: Union[str, bytes], key: Union[str, bytes]) -> str:
        """Calculate HMAC-SHA256."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        if isinstance(key, str):
            key = key.encode('utf-8')
        return hmac.new(key, data, hashlib.sha256).hexdigest()
    
    # ==================== AES Encryption ====================
    
    def aes_encrypt_cbc(self, data: Union[str, bytes], key: bytes, 
                       iv: Optional[bytes] = None) -> str:
        """
        Encrypt data using AES-CBC with PKCS7 padding.
        Returns Base64 encoded ciphertext.
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Ensure key is correct length (16, 24, or 32 bytes)
        if len(key) not in [16, 24, 32]:
            raise ValueError("Key must be 16, 24, or 32 bytes")
        
        # Generate random IV if not provided
        if iv is None:
            import os
            iv = os.urandom(16)
        elif len(iv) != 16:
            raise ValueError("IV must be 16 bytes")
        
        # Apply PKCS7 padding
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # Encrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Return IV + ciphertext as Base64
        return base64.b64encode(iv + ciphertext).decode('utf-8')
    
    def aes_decrypt_cbc(self, data: Union[str, bytes], key: bytes, 
                       iv: Optional[bytes] = None) -> str:
        """
        Decrypt AES-CBC encrypted data.
        Input can be Base64 string or raw bytes.
        """
        if isinstance(data, str):
            data = base64.b64decode(data.encode('utf-8'))
        
        if len(key) not in [16, 24, 32]:
            raise ValueError("Key must be 16, 24, or 32 bytes")
        
        # Extract IV from data if not provided
        if iv is None:
            iv = data[:16]
            data = data[16:]
        elif len(iv) != 16:
            raise ValueError("IV must be 16 bytes")
        
        if len(data) % 16 != 0:
            raise ValueError("Ciphertext length must be multiple of 16")
        
        # Decrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(data) + decryptor.finalize()
        
        # Remove PKCS7 padding
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_data) + unpadder.finalize()
        
        try:
            return plaintext.decode('utf-8')
        except UnicodeDecodeError:
            return plaintext.hex()
    
    def aes_encrypt_ecb(self, data: Union[str, bytes], key: bytes) -> str:
        """
        Encrypt data using AES-ECB with PKCS7 padding.
        Returns Base64 encoded ciphertext.
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if len(key) not in [16, 24, 32]:
            raise ValueError("Key must be 16, 24, or 32 bytes")
        
        # Apply PKCS7 padding
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # Encrypt (ECB mode doesn't use IV)
        cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=self.backend)
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        return base64.b64encode(ciphertext).decode('utf-8')
    
    def aes_decrypt_ecb(self, data: Union[str, bytes], key: bytes) -> str:
        """
        Decrypt AES-ECB encrypted data.
        """
        if isinstance(data, str):
            data = base64.b64decode(data.encode('utf-8'))
        
        if len(key) not in [16, 24, 32]:
            raise ValueError("Key must be 16, 24, or 32 bytes")
        
        if len(data) % 16 != 0:
            raise ValueError("Ciphertext length must be multiple of 16")
        
        # Decrypt
        cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=self.backend)
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(data) + decryptor.finalize()
        
        # Remove PKCS7 padding
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_data) + unpadder.finalize()
        
        try:
            return plaintext.decode('utf-8')
        except UnicodeDecodeError:
            return plaintext.hex()
    
    # ==================== Utility Functions ====================
    
    def random_bytes(self, length: int) -> str:
        """Generate random bytes, returned as hex string."""
        import os
        return os.urandom(length).hex()
    
    def random_string(self, length: int, charset: str = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') -> str:
        """Generate random string from given charset."""
        import os
        result = []
        charset_len = len(charset)
        for _ in range(length):
            idx = os.urandom(1)[0] % charset_len
            result.append(charset[idx])
        return ''.join(result)
    
    def xor_cipher(self, data: Union[str, bytes], key: Union[str, bytes]) -> str:
        """Simple XOR cipher."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        if isinstance(key, str):
            key = key.encode('utf-8')
        
        result = bytearray()
        key_len = len(key)
        for i, byte in enumerate(data):
            result.append(byte ^ key[i % key_len])
        
        return bytes(result).hex()


# Global instance for Lua access
_crypto_instance = None

def get_crypto():
    """Get or create crypto instance."""
    global _crypto_instance
    if _crypto_instance is None:
        _crypto_instance = FMDCrypto()
    return _crypto_instance


def register_with_lua(lua_state):
    """
    Register fmd.crypto module with Lua state.
    Makes all crypto functions available as fmd.crypto.functionname()
    """
    crypto = get_crypto()
    
    # Create fmd table if it doesn't exist
    lua_state.execute("""
        if not fmd then
            fmd = {}
        end
        if not fmd.crypto then
            fmd.crypto = {}
        end
    """)
    
    # Register all methods - use simple assignment via Lua
    methods = {
        'base64_encode': crypto.base64_encode,
        'base64_decode': crypto.base64_decode,
        'base64_url_encode': crypto.base64_url_encode,
        'base64_url_decode': crypto.base64_url_decode,
        'md5': crypto.md5,
        'sha1': crypto.sha1,
        'sha256': crypto.sha256,
        'sha512': crypto.sha512,
        'hmac_md5': crypto.hmac_md5,
        'hmac_sha1': crypto.hmac_sha1,
        'hmac_sha256': crypto.hmac_sha256,
        'aes_encrypt_cbc': crypto.aes_encrypt_cbc,
        'aes_decrypt_cbc': crypto.aes_decrypt_cbc,
        'aes_encrypt_ecb': crypto.aes_encrypt_ecb,
        'aes_decrypt_ecb': crypto.aes_decrypt_ecb,
        'random_bytes': crypto.random_bytes,
        'random_string': crypto.random_string,
        'xor_cipher': crypto.xor_cipher,
    }
    
    # Expose methods to Lua by creating wrapper functions
    for name, func in methods.items():
        # Create a Lua function that calls the Python function
        lua_code = f"""
        local py_func = python.eval("crypto.{name}")
        fmd.crypto.{name} = function(...)
            return py_func(...)
        end
        """
        lua_state.execute(lua_code)
    
    return True


if __name__ == '__main__':
    """Test fmd.crypto implementation"""
    print("=" * 60)
    print("Testing FMD Crypto Module")
    print("=" * 60)
    
    crypto = get_crypto()
    all_passed = True
    
    # Test Base64
    print("\n[1] Testing Base64...")
    test_data = "Hello, World! 你好世界"
    encoded = crypto.base64_encode(test_data)
    decoded = crypto.base64_decode(encoded)
    if decoded == test_data:
        print(f"   ✓ Base64 encode/decode: {test_data} -> {encoded} -> {decoded}")
    else:
        print(f"   ✗ Base64 failed: expected '{test_data}', got '{decoded}'")
        all_passed = False
    
    # Test URL-safe Base64
    print("\n[2] Testing URL-safe Base64...")
    url_encoded = crypto.base64_url_encode(test_data)
    url_decoded = crypto.base64_url_decode(url_encoded)
    if url_decoded == test_data:
        print(f"   ✓ URL-safe Base64: {url_encoded}")
    else:
        print(f"   ✗ URL-safe Base64 failed")
        all_passed = False
    
    # Test Hash functions
    print("\n[3] Testing Hash functions...")
    hash_input = "test"
    print(f"   MD5('{hash_input}'): {crypto.md5(hash_input)}")
    print(f"   SHA1('{hash_input}'): {crypto.sha1(hash_input)}")
    print(f"   SHA256('{hash_input}'): {crypto.sha256(hash_input)}")
    print(f"   SHA512('{hash_input}'): {crypto.sha512(hash_input)[:32]}...")
    
    # Test HMAC
    print("\n[4] Testing HMAC...")
    hmac_key = "secret"
    print(f"   HMAC-MD5: {crypto.hmac_md5(hash_input, hmac_key)}")
    print(f"   HMAC-SHA256: {crypto.hmac_sha256(hash_input, hmac_key)}")
    
    # Test AES CBC
    print("\n[5] Testing AES-CBC...")
    aes_key = b'0123456789abcdef'  # 16 bytes
    aes_data = "Secret message for encryption test"
    encrypted = crypto.aes_encrypt_cbc(aes_data, aes_key)
    decrypted = crypto.aes_decrypt_cbc(encrypted, aes_key)
    if decrypted == aes_data:
        print(f"   ✓ AES-CBC: {aes_data} -> [encrypted] -> {decrypted}")
    else:
        print(f"   ✗ AES-CBC failed: expected '{aes_data}', got '{decrypted}'")
        all_passed = False
    
    # Test AES ECB
    print("\n[6] Testing AES-ECB...")
    encrypted_ecb = crypto.aes_encrypt_ecb(aes_data, aes_key)
    decrypted_ecb = crypto.aes_decrypt_ecb(encrypted_ecb, aes_key)
    if decrypted_ecb == aes_data:
        print(f"   ✓ AES-ECB: {aes_data} -> [encrypted] -> {decrypted_ecb}")
    else:
        print(f"   ✗ AES-ECB failed")
        all_passed = False
    
    # Test random functions
    print("\n[7] Testing Random functions...")
    rand_bytes = crypto.random_bytes(16)
    rand_string = crypto.random_string(32)
    print(f"   Random bytes (hex): {rand_bytes}")
    print(f"   Random string: {rand_string}")
    
    # Test XOR cipher
    print("\n[8] Testing XOR cipher...")
    xor_data = "XOR test data"
    xor_key = "key"
    xor_result = crypto.xor_cipher(xor_data, xor_key)
    print(f"   XOR('{xor_data}', '{xor_key}'): {xor_result}")
    
    # Test with actual Lua
    print("\n[9] Testing Lua integration...")
    try:
        from lupa import LuaRuntime
        lua = LuaRuntime(unpack_returned_tuples=True)
        
        # Register crypto module
        register_with_lua(lua)
        
        # Test Lua script using fmd.crypto
        lua_test = """
            local test_data = "Lua crypto test"
            local encoded = fmd.crypto.base64_encode(test_data)
            local decoded = fmd.crypto.base64_decode(encoded)
            local md5_hash = fmd.crypto.md5(test_data)
            
            return {
                original = test_data,
                encoded = encoded,
                decoded = decoded,
                md5 = md5_hash,
                match = (test_data == decoded)
            }
        """
        
        result = lua.execute(lua_test)
        print(f"   Original: {result['original']}")
        print(f"   Encoded: {result['encoded']}")
        print(f"   Decoded: {result['decoded']}")
        print(f"   MD5: {result['md5']}")
        
        if result['match']:
            print("   ✓ Lua integration successful!")
        else:
            print("   ✗ Lua integration failed - decode mismatch")
            all_passed = False
            
    except Exception as e:
        print(f"   ✗ Lua integration error: {e}")
        all_passed = False
    
    # Final result
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All FMD Crypto tests PASSED!")
    else:
        print("❌ Some tests FAILED")
    print("=" * 60)
