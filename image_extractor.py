"""
Image Extraction Utility for HTML Games
Extracts the first image from HTML files for use as thumbnails
"""
import re
import base64
import logging
from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse
import requests
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

class ImageExtractor:
    """Utility class for extracting images from HTML content"""
    
    def __init__(self):
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}
    
    def extract_first_image(self, html_content: str, base_url: str = None) -> Optional[str]:
        """
        Extracts the first image from HTML content
        
        Args:
            html_content: HTML content as string
            base_url: Base URL for resolving relative image URLs
            
        Returns:
            Base64 encoded image data URL or None if no image found
        """
        try:
            # Find all img tags
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
            img_matches = re.findall(img_pattern, html_content, re.IGNORECASE)
            
            if not img_matches:
                # Try to find images in CSS background-image
                css_pattern = r'background-image:\s*url\(["\']?([^"\']+)["\']?\)'
                css_matches = re.findall(css_pattern, html_content, re.IGNORECASE)
                img_matches = css_matches
            
            if not img_matches:
                # Try to find canvas elements that might contain game graphics
                canvas_pattern = r'<canvas[^>]*>'
                if re.search(canvas_pattern, html_content, re.IGNORECASE):
                    # Generate a placeholder for canvas-based games
                    return self._generate_canvas_placeholder()
                
                return None
            
            # Get the first image URL
            first_img_url = img_matches[0]
            
            # Resolve relative URLs
            if base_url and not urlparse(first_img_url).netloc:
                first_img_url = urljoin(base_url, first_img_url)
            
            # Convert to base64 data URL
            return self._url_to_base64(first_img_url)
            
        except Exception as e:
            logger.error(f"Error extracting image from HTML: {e}")
            return None
    
    def _url_to_base64(self, image_url: str) -> Optional[str]:
        """
        Converts image URL to base64 data URL
        
        Args:
            image_url: URL of the image
            
        Returns:
            Base64 data URL or None if conversion fails
        """
        try:
            # Handle data URLs
            if image_url.startswith('data:'):
                return image_url
            
            # Handle relative URLs or local files
            if not urlparse(image_url).netloc and not image_url.startswith('http'):
                # This might be a local file path, skip for now
                return self._generate_placeholder()
            
            # Download image
            response = requests.get(image_url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return self._generate_placeholder()
            
            # Convert to base64
            image_data = response.content
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            return f"data:{content_type};base64,{base64_data}"
            
        except Exception as e:
            logger.warning(f"Could not convert image URL to base64: {e}")
            return self._generate_placeholder()
    
    def _generate_placeholder(self) -> str:
        """
        Generates a placeholder image for games without images
        
        Returns:
            Base64 data URL of a placeholder image
        """
        try:
            # Create a simple placeholder image
            img = Image.new('RGB', (300, 200), color='#1a1a1a')
            
            # Add some basic styling to make it look like a game placeholder
            from PIL import ImageDraw, ImageFont
            
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font, fallback to basic if not available
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Draw placeholder text
            text = "GAME PREVIEW"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (300 - text_width) // 2
            y = (200 - text_height) // 2
            
            draw.text((x, y), text, fill='#00ff00', font=font)
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_data = buffer.getvalue()
            base64_data = base64.b64encode(img_data).decode('utf-8')
            
            return f"data:image/png;base64,{base64_data}"
            
        except Exception as e:
            logger.error(f"Error generating placeholder: {e}")
            # Return a simple colored rectangle as fallback
            return "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iIzFhMWExYSIvPjx0ZXh0IHg9IjE1MCIgeT0iMTAwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IiMwMGZmMDAiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkdBTUUgUFJFVklFVzwvdGV4dD48L3N2Zz4="
    
    def _generate_canvas_placeholder(self) -> str:
        """
        Generates a special placeholder for canvas-based games
        
        Returns:
            Base64 data URL of a canvas game placeholder
        """
        return "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iIzAwMDAwMCIgc3Ryb2tlPSIjMDBmZjAwIiBzdHJva2Utd2lkdGg9IjIiLz48dGV4dCB4PSIxNTAiIHk9IjEwMCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE2IiBmaWxsPSIjMDBmZjAwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5DQU5WQVMgR0FNRTwvdGV4dD48L3N2Zz4="
    
    def extract_game_info(self, html_content: str) -> dict:
        """
        Extracts game information from HTML content
        
        Args:
            html_content: HTML content as string
            
        Returns:
            Dictionary with extracted game information
        """
        info = {
            'title': 'Untitled Game',
            'description': 'A browser game',
            'category': 'GAME'
        }
        
        try:
            # Extract title from <title> tag
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
            if title_match:
                info['title'] = title_match.group(1).strip()
            
            # Extract description from meta description
            desc_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\'][^>]*>', html_content, re.IGNORECASE)
            if desc_match:
                info['description'] = desc_match.group(1).strip()
            
            # Try to determine category based on content
            if 'canvas' in html_content.lower():
                info['category'] = 'CANVAS'
            elif 'arcade' in html_content.lower():
                info['category'] = 'ARCADE'
            elif 'puzzle' in html_content.lower():
                info['category'] = 'PUZZLE'
            elif 'shooter' in html_content.lower():
                info['category'] = 'SHOOTER'
            elif 'platform' in html_content.lower():
                info['category'] = 'PLATFORM'
            
        except Exception as e:
            logger.error(f"Error extracting game info: {e}")
        
        return info

# Global instance
image_extractor = ImageExtractor()
