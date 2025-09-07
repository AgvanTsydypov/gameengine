#!/usr/bin/env python3
"""
HTML Preview Generator

This script generates photo previews (screenshots) of HTML files.
It uses Selenium with a headless browser to render HTML files and capture screenshots.

Usage:
    python html_preview_generator.py <html_file_path> [output_path]
    
Example:
    python html_preview_generator.py /Users/agmac/Desktop/app/deepseek_game_Space_Pac-Man_3D_20250906_204843.html
"""

import os
import sys
import time
import argparse
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
from PIL import Image, ImageDraw, ImageFont
import io
import base64


class HTMLPreviewGenerator:
    def __init__(self, headless=True, window_size=(1920, 1080)):
        """
        Initialize the HTML Preview Generator.
        
        Args:
            headless (bool): Whether to run browser in headless mode
            window_size (tuple): Browser window size (width, height)
        """
        self.headless = headless
        self.window_size = window_size
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self.is_render_env = self._is_render_environment()
    
    def _is_render_environment(self):
        """Check if running on Render.com"""
        return os.getenv('RENDER') == 'true' or os.getenv('RENDER_EXTERNAL_URL') is not None
    
    def _create_fallback_thumbnail(self, html_content, output_path, title="Game Preview"):
        """
        Create a fallback thumbnail using PIL when Selenium is not available
        
        Args:
            html_content: HTML content as string
            output_path: Path where to save the thumbnail
            title: Title to display on the thumbnail
            
        Returns:
            str: Path to the generated thumbnail, or None if failed
        """
        try:
            self.logger.info("Creating fallback thumbnail using PIL")
            
            # Create a thumbnail image
            width, height = 800, 600
            img = Image.new('RGB', (width, height), color='#1a1a1a')
            draw = ImageDraw.Draw(img)
            
            # Try to load a font
            try:
                # Try different font paths
                font_paths = [
                    '/System/Library/Fonts/Arial.ttf',  # macOS
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
                    '/usr/share/fonts/TTF/arial.ttf',  # Linux alternative
                ]
                font = None
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        font = ImageFont.truetype(font_path, 24)
                        break
                
                if font is None:
                    font = ImageFont.load_default()
            except:
                font = ImageFont.load_default()
            
            # Draw title
            title_text = title[:30] + "..." if len(title) > 30 else title
            bbox = draw.textbbox((0, 0), title_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2 - 50
            
            draw.text((x, y), title_text, fill='#00ff00', font=font)
            
            # Draw "HTML Game" text
            game_text = "HTML Game"
            bbox = draw.textbbox((0, 0), game_text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = y + text_height + 20
            
            draw.text((x, y), game_text, fill='#ffffff', font=font)
            
            # Draw a border
            draw.rectangle([10, 10, width-10, height-10], outline='#00ff00', width=2)
            
            # Save the image
            img.save(output_path, 'PNG')
            
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                self.logger.info(f"Fallback thumbnail created: {output_path} (size: {file_size} bytes)")
                return str(output_path)
            else:
                self.logger.error("Failed to create fallback thumbnail")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating fallback thumbnail: {e}")
            return None
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options."""
        try:
            # Try undetected-chromedriver first (better for Render.com)
            if self.is_render_env:
                self.logger.info("Setting up undetected Chrome driver for Render.com")
                options = uc.ChromeOptions()
                if self.headless:
                    options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-logging")
                options.add_argument("--disable-web-security")
                options.add_argument("--allow-running-insecure-content")
                options.add_argument(f"--window-size={self.window_size[0]},{self.window_size[1]}")
                
                self.driver = uc.Chrome(options=options)
                self.driver.set_window_size(self.window_size[0], self.window_size[1])
                self.logger.info("✓ Undetected Chrome WebDriver initialized")
                return True
            
            # Fallback to regular Selenium
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Additional options for better rendering
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument(f"--window-size={self.window_size[0]},{self.window_size[1]}")
            
            # Set user agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Initialize the driver with automatic ChromeDriver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_window_size(self.window_size[0], self.window_size[1])
            
            self.logger.info(f"✓ Chrome WebDriver initialized (headless: {self.headless})")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Failed to initialize Chrome WebDriver: {e}")
            self.logger.info("Chrome/ChromeDriver not available, will use fallback method")
            return False
    
    def generate_preview(self, html_file_path, output_path=None, wait_time=3):
        """
        Generate a preview screenshot of an HTML file.
        
        Args:
            html_file_path (str): Path to the HTML file
            output_path (str, optional): Output path for the screenshot
            wait_time (int): Time to wait for page to load (seconds)
            
        Returns:
            str: Path to the generated screenshot, or None if failed
        """
        if not os.path.exists(html_file_path):
            self.logger.error(f"HTML file not found: {html_file_path}")
            return None
        
        # Generate output path if not provided
        if not output_path:
            html_file = Path(html_file_path)
            output_path = html_file.parent / f"{html_file.stem}_preview.png"
        
        # Try to setup driver, if it fails, use fallback
        if not self.driver:
            if not self.setup_driver():
                self.logger.warning("Selenium setup failed, using fallback thumbnail generation")
                # Read HTML content for fallback
                try:
                    with open(html_file_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # Extract title from HTML
                    import re
                    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
                    title = title_match.group(1).strip() if title_match else "Game Preview"
                    
                    return self._create_fallback_thumbnail(html_content, output_path, title)
                except Exception as e:
                    self.logger.error(f"Fallback thumbnail generation failed: {e}")
                    return None
        
        try:
            # Convert to absolute path and file URL
            html_file_path = os.path.abspath(html_file_path)
            file_url = f"file://{html_file_path}"
            
            self.logger.info(f"Loading HTML file: {html_file_path}")
            self.logger.info(f"File URL: {file_url}")
            
            # Load the HTML file
            self.driver.get(file_url)
            
            # Wait for page to load
            self.logger.info(f"Waiting {wait_time} seconds for page to load...")
            time.sleep(wait_time)
            
            # Try to wait for canvas or other dynamic content to render
            try:
                # Wait for canvas element if it exists (for games)
                WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.TAG_NAME, "canvas"))
                )
                self.logger.info("Canvas element detected, waiting for rendering...")
                time.sleep(1)  # Reduced additional wait for canvas rendering
            except TimeoutException:
                self.logger.info("No canvas element found, proceeding with screenshot")
            
            # Take screenshot
            self.logger.info("Taking screenshot...")
            self.driver.save_screenshot(str(output_path))
            
            # Verify screenshot was created and has content
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                if file_size > 0:
                    self.logger.info(f"Screenshot saved: {output_path} (size: {file_size} bytes)")
                    return str(output_path)
                else:
                    self.logger.error(f"Screenshot file is empty: {output_path}")
                    return None
            else:
                self.logger.error(f"Screenshot file was not created: {output_path}")
                return None
            
        except WebDriverException as e:
            self.logger.error(f"WebDriver error: {e}")
            # Try fallback method
            return self._try_fallback_generation(html_file_path, output_path)
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            # Try fallback method
            return self._try_fallback_generation(html_file_path, output_path)
    
    def _try_fallback_generation(self, html_file_path, output_path):
        """Try to generate thumbnail using fallback method"""
        try:
            self.logger.info("Attempting fallback thumbnail generation")
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract title from HTML
            import re
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else "Game Preview"
            
            return self._create_fallback_thumbnail(html_content, output_path, title)
        except Exception as e:
            self.logger.error(f"Fallback generation also failed: {e}")
            return None
    
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            print("✓ WebDriver closed")


def main():
    """Main function to handle command line arguments and generate preview."""
    parser = argparse.ArgumentParser(
        description="Generate photo previews of HTML files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python html_preview_generator.py game.html
  python html_preview_generator.py game.html preview.png
  python html_preview_generator.py /path/to/game.html /path/to/output.png
        """
    )
    
    parser.add_argument(
        "html_file",
        help="Path to the HTML file to preview"
    )
    
    parser.add_argument(
        "output_path",
        nargs="?",
        help="Output path for the screenshot (optional)"
    )
    
    parser.add_argument(
        "--wait",
        type=int,
        default=3,
        help="Time to wait for page to load in seconds (default: 3)"
    )
    
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in visible mode (for debugging)"
    )
    
    parser.add_argument(
        "--width",
        type=int,
        default=1920,
        help="Browser window width (default: 1920)"
    )
    
    parser.add_argument(
        "--height",
        type=int,
        default=1080,
        help="Browser window height (default: 1080)"
    )
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = HTMLPreviewGenerator(
        headless=not args.no_headless,
        window_size=(args.width, args.height)
    )
    
    try:
        # Generate preview
        result = generator.generate_preview(
            args.html_file,
            args.output_path,
            args.wait
        )
        
        if result:
            print(f"\n🎉 Success! Preview generated: {result}")
            sys.exit(0)
        else:
            print("\n❌ Failed to generate preview")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
    finally:
        generator.close()


if __name__ == "__main__":
    main()
