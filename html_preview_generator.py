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
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager


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
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options."""
        try:
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
            
            print(f"✓ Chrome WebDriver initialized (headless: {self.headless})")
            return True
            
        except Exception as e:
            print(f"✗ Failed to initialize Chrome WebDriver: {e}")
            print("Make sure Chrome and ChromeDriver are installed.")
            print("You can install ChromeDriver with: brew install chromedriver")
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
            print(f"✗ HTML file not found: {html_file_path}")
            return None
        
        if not self.driver:
            if not self.setup_driver():
                return None
        
        try:
            # Convert to absolute path and file URL
            html_file_path = os.path.abspath(html_file_path)
            file_url = f"file://{html_file_path}"
            
            print(f"📄 Loading HTML file: {html_file_path}")
            print(f"🌐 File URL: {file_url}")
            
            # Load the HTML file
            self.driver.get(file_url)
            
            # Wait for page to load
            print(f"⏳ Waiting {wait_time} seconds for page to load...")
            time.sleep(wait_time)
            
            # Try to wait for canvas or other dynamic content to render
            try:
                # Wait for canvas element if it exists (for games)
                WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.TAG_NAME, "canvas"))
                )
                print("✓ Canvas element detected, waiting for rendering...")
                time.sleep(1)  # Reduced additional wait for canvas rendering
            except TimeoutException:
                print("ℹ️  No canvas element found, proceeding with screenshot")
            
            # Generate output path if not provided
            if not output_path:
                html_file = Path(html_file_path)
                output_path = html_file.parent / f"{html_file.stem}_preview.png"
            
            # Take screenshot
            print(f"📸 Taking screenshot...")
            self.driver.save_screenshot(str(output_path))
            
            # Verify screenshot was created and has content
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                if file_size > 0:
                    print(f"✅ Screenshot saved: {output_path} (size: {file_size} bytes)")
                    return str(output_path)
                else:
                    print(f"❌ Screenshot file is empty: {output_path}")
                    return None
            else:
                print(f"❌ Screenshot file was not created: {output_path}")
                return None
            
        except WebDriverException as e:
            print(f"✗ WebDriver error: {e}")
            return None
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
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
