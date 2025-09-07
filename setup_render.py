#!/usr/bin/env python3
"""
Setup script for Render.com deployment
This script helps configure the environment for thumbnail generation on Render.com
"""

import os
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_render_environment():
    """Check if running on Render.com"""
    return os.getenv('RENDER') == 'true' or os.getenv('RENDER_EXTERNAL_URL') is not None

def install_chrome_dependencies():
    """Install Chrome and ChromeDriver on Render.com"""
    if not check_render_environment():
        logger.info("Not running on Render.com, skipping Chrome installation")
        return True
    
    try:
        logger.info("Installing Chrome and ChromeDriver for Render.com...")
        
        # Update package list
        logger.info("Updating package list...")
        subprocess.run(['apt-get', 'update'], check=True)
        
        # Install required packages
        logger.info("Installing required packages...")
        subprocess.run(['apt-get', 'install', '-y', 'wget', 'gnupg', 'unzip', 'curl'], check=True)
        
        # Add Google Chrome repository
        logger.info("Adding Google Chrome repository...")
        subprocess.run([
            'wget', '-q', '-O', '-', 
            'https://dl.google.com/linux/linux_signing_key.pub'
        ], check=True, stdout=subprocess.PIPE)
        
        # Add Chrome repository
        logger.info("Configuring Chrome repository...")
        with open('/etc/apt/sources.list.d/google-chrome.list', 'w') as f:
            f.write('deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main\n')
        
        # Update package list again
        logger.info("Updating package list with Chrome repository...")
        subprocess.run(['apt-get', 'update'], check=True)
        
        # Install Chrome
        logger.info("Installing Google Chrome...")
        subprocess.run(['apt-get', 'install', '-y', 'google-chrome-stable'], check=True)
        
        # Verify Chrome installation
        try:
            result = subprocess.run(['google-chrome', '--version'], 
                                  capture_output=True, text=True, check=True)
            chrome_version = result.stdout.strip().split()[2].split('.')[0:3]
            chrome_version_str = '.'.join(chrome_version)
            logger.info(f"Chrome version: {chrome_version_str}")
        except Exception as e:
            logger.error(f"Failed to get Chrome version: {e}")
            return False
        
        # Install ChromeDriver
        logger.info("Installing ChromeDriver...")
        try:
            # Try to get ChromeDriver version
            chromedriver_version_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{chrome_version_str}"
            result = subprocess.run(['curl', '-s', chromedriver_version_url], 
                                  capture_output=True, text=True, check=True)
            chromedriver_version = result.stdout.strip()
            logger.info(f"ChromeDriver version: {chromedriver_version}")
            
            # Download and install ChromeDriver
            download_url = f"https://chromedriver.storage.googleapis.com/{chromedriver_version}/chromedriver_linux64.zip"
            logger.info(f"Downloading ChromeDriver from: {download_url}")
            subprocess.run(['wget', '-O', '/tmp/chromedriver.zip', download_url], check=True)
            subprocess.run(['unzip', '/tmp/chromedriver.zip', '-d', '/tmp/'], check=True)
            subprocess.run(['mv', '/tmp/chromedriver', '/usr/local/bin/'], check=True)
            subprocess.run(['chmod', '+x', '/usr/local/bin/chromedriver'], check=True)
            
            # Verify ChromeDriver installation
            result = subprocess.run(['chromedriver', '--version'], 
                                  capture_output=True, text=True, check=True)
            logger.info(f"ChromeDriver installed: {result.stdout.strip()}")
            
        except Exception as e:
            logger.error(f"Failed to install ChromeDriver: {e}")
            # Try alternative method with webdriver-manager
            logger.info("Trying alternative ChromeDriver installation...")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                driver_path = ChromeDriverManager().install()
                logger.info(f"ChromeDriver installed via webdriver-manager: {driver_path}")
            except Exception as e2:
                logger.error(f"Alternative ChromeDriver installation also failed: {e2}")
                return False
        
        logger.info("Chrome and ChromeDriver installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Chrome dependencies: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during Chrome installation: {e}")
        return False

def test_thumbnail_generation():
    """Test thumbnail generation functionality"""
    try:
        from html_preview_generator import HTMLPreviewGenerator
        
        # Create a simple test HTML
        test_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Game</title>
        </head>
        <body>
            <h1>Test Game</h1>
            <p>This is a test game for thumbnail generation.</p>
        </body>
        </html>
        """
        
        # Write test HTML to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(test_html)
            temp_file = f.name
        
        try:
            # Test thumbnail generation
            generator = HTMLPreviewGenerator(headless=True)
            result = generator.generate_preview(temp_file)
            
            if result and os.path.exists(result):
                logger.info(f"Thumbnail generation test successful: {result}")
                return True
            else:
                logger.error("Thumbnail generation test failed")
                return False
        finally:
            generator.close()
            os.unlink(temp_file)
            
    except Exception as e:
        logger.error(f"Thumbnail generation test failed: {e}")
        return False

def main():
    """Main setup function"""
    logger.info("Starting Render.com setup...")
    
    # Check if we're on Render.com
    if check_render_environment():
        logger.info("Running on Render.com environment")
        
        # Install Chrome dependencies
        if install_chrome_dependencies():
            logger.info("Chrome dependencies installed successfully")
        else:
            logger.warning("Failed to install Chrome dependencies, will use fallback method")
    else:
        logger.info("Running in local environment")
    
    # Test thumbnail generation
    if test_thumbnail_generation():
        logger.info("Thumbnail generation is working correctly")
    else:
        logger.warning("Thumbnail generation test failed, but fallback method should work")
    
    logger.info("Setup completed")

if __name__ == "__main__":
    main()
