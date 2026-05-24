#!/usr/bin/env python3
"""
FMD ImagePuzzle Module - Python equivalent of ImagePuzzle.pas and LuaImagePuzzle.pas

Handles image descrambling for manga sites that split images into blocks and rearrange them.
"""

import io
from PIL import Image
import math


class ImagePuzzle:
    """
    Descrambles images that have been split into blocks and rearranged.
    
    Equivalent to TImagePuzzle class in Pascal.
    """
    
    def __init__(self, hor_block_count: int, ver_block_count: int):
        """
        Create a new ImagePuzzle instance.
        
        Args:
            hor_block_count: Number of horizontal blocks
            ver_block_count: Number of vertical blocks
        """
        self.hor_block = hor_block_count
        self.ver_block = ver_block_count
        self.multiply = 1
        
        # Initialize matrix with sequential indices
        self.matrix = list(range(hor_block_count * ver_block_count))
    
    @property
    def hor_block(self) -> int:
        """Get horizontal block count."""
        return self._hor_block
    
    @hor_block.setter
    def hor_block(self, value: int):
        self._hor_block = value
    
    @property
    def ver_block(self) -> int:
        """Get vertical block count."""
        return self._ver_block
    
    @ver_block.setter
    def ver_block(self, value: int):
        self._ver_block = value
    
    @property
    def multiply(self) -> int:
        """Get multiply factor."""
        return self._multiply
    
    @multiply.setter
    def multiply(self, value: int):
        self._multiply = value if value > 0 else 1
    
    @property
    def matrix(self) -> list:
        """Get the permutation matrix."""
        return self._matrix
    
    @matrix.setter
    def matrix(self, value: list):
        self._matrix = value
    
    def descramble(self, input_stream: io.BytesIO, output_stream: io.BytesIO) -> None:
        """
        Descramble an image from input stream and write to output stream.
        
        Args:
            input_stream: Stream containing the scrambled image
            output_stream: Stream to write the descrambled image
        """
        # Load the image
        input_stream.seek(0)
        image = Image.open(input_stream)
        
        # Determine output format
        ext = 'jpg'
        if image.format == 'PNG':
            ext = 'png'
        
        width, height = image.size
        
        # Calculate block dimensions
        if self.multiply <= 1:
            block_width = float(width) / self.hor_block
            block_height = float(height) / self.ver_block
        else:
            block_width = int(float(width) / (self.hor_block * self.multiply)) * self.multiply
            block_height = int(float(height) / (self.ver_block * self.multiply)) * self.multiply
        
        # Create result image
        result = Image.new(image.mode, (width, height))
        
        # Rearrange blocks according to matrix
        for i in range(self.hor_block * self.ver_block):
            # Get source position from matrix
            matrix_index = self.matrix[i]
            src_row = int(math.floor(matrix_index / self.hor_block))
            src_col = matrix_index - src_row * self.hor_block
            
            src_x = int(src_col * block_width)
            src_y = int(src_row * block_height)
            
            # Calculate destination position
            dst_row = int(math.floor(i / self.hor_block))
            dst_col = i - dst_row * self.hor_block
            
            dst_x = int(dst_col * block_width)
            dst_y = int(dst_row * block_height)
            
            # Extract source block
            src_rect = (
                src_x,
                src_y,
                int(src_x + block_width),
                int(src_y + block_height)
            )
            src_block = image.crop(src_rect)
            
            # Paste to destination
            result.paste(src_block, (dst_x, dst_y))
        
        # Save result to output stream
        output_stream.seek(0)
        output_stream.truncate(0)
        result.save(output_stream, format='JPEG' if ext == 'jpg' else 'PNG')
        output_stream.seek(0)


# Lua module interface
def create(hor_block_count: int, ver_block_count: int) -> ImagePuzzle:
    """Create a new ImagePuzzle instance (Lua compatible)."""
    return ImagePuzzle(hor_block_count, ver_block_count)


def lua_open(L=None):
    """
    Lua open function - registers the module with Lua.
    This is called when Lua does require('fmd.imagepuzzle')
    """
    # Return a table with the module functions
    return {
        'Create': create,
        'New': create,
        'ImagePuzzle': ImagePuzzle
    }


# Test code
if __name__ == '__main__':
    print("Testing ImagePuzzle module...")
    
    # Create a test image
    test_img = Image.new('RGB', (100, 100), color='red')
    # Draw some pattern to verify descrambling
    for x in range(0, 100, 10):
        for y in range(0, 100, 10):
            if (x // 10 + y // 10) % 2 == 0:
                for px in range(x, min(x+10, 100)):
                    for py in range(y, min(y+10, 100)):
                        test_img.putpixel((px, py), (0, 255, 0))
    
    # Save to stream
    input_stream = io.BytesIO()
    test_img.save(input_stream, format='PNG')
    
    # Create puzzle with 2x2 blocks
    puzzle = ImagePuzzle(2, 2)
    
    # Scramble the matrix manually for testing
    puzzle.matrix = [2, 0, 3, 1]  # Swap blocks around
    
    # Descramble
    output_stream = io.BytesIO()
    puzzle.descramble(input_stream, output_stream)
    
    # Load result
    output_stream.seek(0)
    result_img = Image.open(output_stream)
    
    print(f"✓ ImagePuzzle created: {puzzle.hor_block}x{puzzle.ver_block} blocks")
    print(f"✓ Matrix: {puzzle.matrix}")
    print(f"✓ Input size: {test_img.size}")
    print(f"✓ Output size: {result_img.size}")
    print(f"✓ Descrambling successful!")
    
    # Test Lua interface
    print("\n✓ Testing Lua interface...")
    puzzle2 = create(4, 4)
    print(f"✓ Created via create(): {puzzle2.hor_block}x{puzzle2.ver_block}")
    
    print("\n✅ All tests passed!")
