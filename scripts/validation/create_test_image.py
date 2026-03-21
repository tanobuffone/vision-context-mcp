#!/usr/bin/env python3
"""
Create test image for validation testing.
Generates a simple test image with various visual elements.
"""

import numpy as np
from PIL import Image, ImageDraw

def create_test_image(output_path: str = "/tmp/test_image_vision_mcp.jpg"):
    """Create a test image with multiple visual elements."""
    
    width, height = 400, 400
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Sky gradient
    for y in range(height // 2):
        color = (
            int(135 + (200 - 135) * y / (height // 2)),
            int(206 + (230 - 206) * y / (height // 2)),
            int(235 + (250 - 235) * y / (height // 2))
        )
        draw.line([(0, y), (width, y)], fill=color)
    
    # Ground
    draw.rectangle([0, height // 2, width, height], fill=(34, 139, 34))
    
    # Sun
    draw.ellipse([300, 30, 370, 100], fill=(255, 255, 0))
    
    # House
    draw.rectangle([50, 200, 150, 320], fill=(139, 69, 19))
    draw.polygon([(40, 200), (100, 140), (160, 200)], fill=(178, 34, 34))
    draw.rectangle([85, 260, 115, 320], fill=(101, 67, 33))
    
    # Tree
    draw.rectangle([250, 250, 270, 320], fill=(101, 67, 33))
    draw.ellipse([220, 180, 300, 270], fill=(34, 139, 34))
    
    # Person
    draw.ellipse([310, 230, 330, 250], fill=(255, 218, 185))
    draw.line([(320, 250), (320, 290)], fill=(0, 0, 0), width=3)
    draw.line([(320, 260), (300, 280)], fill=(0, 0, 0), width=3)
    draw.line([(320, 260), (340, 280)], fill=(0, 0, 0), width=3)
    
    # Car
    draw.rectangle([200, 330, 300, 360], fill=(220, 20, 60))
    draw.ellipse([210, 355, 230, 375], fill=(50, 50, 50))
    draw.ellipse([270, 355, 290, 375], fill=(50, 50, 50))
    
    img.save(output_path, quality=95)
    print(f"Test image created: {output_path}")
    return output_path

if __name__ == "__main__":
    create_test_image()