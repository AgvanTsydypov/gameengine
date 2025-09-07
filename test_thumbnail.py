#!/usr/bin/env python3
"""
Test script for thumbnail generation
Tests both Selenium and PIL fallback methods
"""

import os
import tempfile
import logging
from html_preview_generator import HTMLPreviewGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_html():
    """Create a test HTML file for thumbnail generation"""
    test_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test Game - Space Adventure</title>
        <style>
            body {
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #1e3c72, #2a5298);
                color: white;
                font-family: Arial, sans-serif;
                text-align: center;
            }
            .game-container {
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                color: #00ff00;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }
            .game-area {
                background: rgba(0,0,0,0.3);
                border: 2px solid #00ff00;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }
            .start-button {
                background: #00ff00;
                color: black;
                border: none;
                padding: 15px 30px;
                font-size: 18px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
            }
            .start-button:hover {
                background: #00cc00;
            }
        </style>
    </head>
    <body>
        <div class="game-container">
            <h1>🚀 Space Adventure Game</h1>
            <div class="game-area">
                <p>Welcome to the ultimate space adventure!</p>
                <p>Navigate through asteroid fields, collect power-ups, and reach the final destination.</p>
                <button class="start-button" onclick="startGame()">Start Game</button>
            </div>
            <p>Use arrow keys to move, spacebar to shoot!</p>
        </div>
        
        <script>
            function startGame() {
                alert('Game started! This is a test game for thumbnail generation.');
            }
        </script>
    </body>
    </html>
    """
    return test_html

def test_thumbnail_generation():
    """Test thumbnail generation with both methods"""
    logger.info("Starting thumbnail generation test...")
    
    # Create test HTML
    test_html = create_test_html()
    
    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(test_html)
        temp_html_path = f.name
    
    try:
        # Test thumbnail generation
        generator = HTMLPreviewGenerator(headless=True, window_size=(800, 600))
        
        logger.info("Testing thumbnail generation...")
        result = generator.generate_preview(
            html_file_path=temp_html_path,
            wait_time=3
        )
        
        if result and os.path.exists(result):
            file_size = os.path.getsize(result)
            logger.info(f"✅ Thumbnail generated successfully!")
            logger.info(f"   File: {result}")
            logger.info(f"   Size: {file_size} bytes")
            
            # Check if it's a valid image
            try:
                from PIL import Image
                with Image.open(result) as img:
                    logger.info(f"   Dimensions: {img.size}")
                    logger.info(f"   Format: {img.format}")
                    logger.info(f"   Mode: {img.mode}")
            except Exception as e:
                logger.warning(f"   Could not verify image properties: {e}")
            
            return True
        else:
            logger.error("❌ Thumbnail generation failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during thumbnail generation: {e}")
        return False
    finally:
        # Clean up
        if 'generator' in locals():
            generator.close()
        
        if os.path.exists(temp_html_path):
            os.unlink(temp_html_path)
            logger.info("Cleaned up temporary HTML file")

def test_fallback_method():
    """Test the PIL fallback method directly"""
    logger.info("Testing PIL fallback method...")
    
    test_html = create_test_html()
    
    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(test_html)
        temp_html_path = f.name
    
    try:
        generator = HTMLPreviewGenerator(headless=True)
        
        # Test fallback method directly
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            fallback_path = f.name
        
        result = generator._create_fallback_thumbnail(test_html, fallback_path, "Test Game")
        
        if result and os.path.exists(result):
            file_size = os.path.getsize(result)
            logger.info(f"✅ Fallback thumbnail generated successfully!")
            logger.info(f"   File: {result}")
            logger.info(f"   Size: {file_size} bytes")
            return True
        else:
            logger.error("❌ Fallback thumbnail generation failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during fallback test: {e}")
        return False
    finally:
        # Clean up
        if 'generator' in locals():
            generator.close()
        
        if os.path.exists(temp_html_path):
            os.unlink(temp_html_path)
        
        if 'fallback_path' in locals() and os.path.exists(fallback_path):
            os.unlink(fallback_path)

def main():
    """Main test function"""
    logger.info("=" * 50)
    logger.info("THUMBNAIL GENERATION TEST")
    logger.info("=" * 50)
    
    # Test 1: Full thumbnail generation (Selenium + fallback)
    logger.info("\n1. Testing full thumbnail generation...")
    success1 = test_thumbnail_generation()
    
    # Test 2: Fallback method only
    logger.info("\n2. Testing PIL fallback method...")
    success2 = test_fallback_method()
    
    # Results
    logger.info("\n" + "=" * 50)
    logger.info("TEST RESULTS")
    logger.info("=" * 50)
    logger.info(f"Full thumbnail generation: {'✅ PASS' if success1 else '❌ FAIL'}")
    logger.info(f"PIL fallback method: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 or success2:
        logger.info("✅ At least one method works - deployment should be successful!")
    else:
        logger.error("❌ Both methods failed - check your setup!")
    
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
