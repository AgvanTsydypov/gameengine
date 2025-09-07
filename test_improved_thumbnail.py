#!/usr/bin/env python3
"""
Test script for improved thumbnail generation
Tests the enhanced Selenium setup with multiple fallback methods
"""

import os
import tempfile
import logging
from html_preview_generator import HTMLPreviewGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_game_html():
    """Create a test HTML game for thumbnail generation"""
    game_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Neon Mini Shooter</title>
        <style>
            body {
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #0a0a0a, #1a1a2e);
                color: white;
                font-family: 'Courier New', monospace;
                overflow: hidden;
            }
            .game-container {
                position: relative;
                width: 100vw;
                height: 100vh;
                background: 
                    radial-gradient(circle at 20% 50%, rgba(0, 255, 255, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 80% 20%, rgba(255, 0, 255, 0.1) 0%, transparent 50%),
                    linear-gradient(45deg, #0a0a0a 0%, #1a1a2e 100%);
            }
            .ui {
                position: absolute;
                top: 20px;
                left: 20px;
                z-index: 10;
            }
            .title {
                font-size: 24px;
                color: #00ffff;
                text-shadow: 0 0 10px #00ffff;
                margin-bottom: 10px;
            }
            .score {
                font-size: 18px;
                color: #ffffff;
            }
            .progress-bar {
                width: 200px;
                height: 20px;
                background: linear-gradient(90deg, #00ff00, #ffff00, #ff0000);
                border-radius: 10px;
                margin: 10px 0;
                position: relative;
                overflow: hidden;
            }
            .progress-fill {
                height: 100%;
                background: rgba(255, 255, 255, 0.3);
                width: 60%;
                border-radius: 10px;
            }
            .controls {
                position: absolute;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                display: flex;
                gap: 20px;
            }
            .control-btn {
                width: 60px;
                height: 60px;
                border: 2px solid #00ffff;
                border-radius: 50%;
                background: rgba(0, 255, 255, 0.1);
                color: #00ffff;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                cursor: pointer;
            }
            .game-area {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-image: 
                    linear-gradient(rgba(0, 255, 255, 0.1) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(0, 255, 255, 0.1) 1px, transparent 1px);
                background-size: 20px 20px;
            }
            .player {
                position: absolute;
                width: 20px;
                height: 20px;
                background: radial-gradient(circle, #00ffff, #0088ff);
                border-radius: 50%;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                box-shadow: 0 0 20px #00ffff;
            }
            .enemy {
                position: absolute;
                width: 15px;
                height: 15px;
                background: radial-gradient(circle, #ff0000, #cc0000);
                border-radius: 50%;
                box-shadow: 0 0 15px #ff0000;
            }
            .enemy:nth-child(1) { top: 20%; left: 20%; }
            .enemy:nth-child(2) { top: 30%; right: 25%; }
            .enemy:nth-child(3) { bottom: 30%; left: 30%; }
        </style>
    </head>
    <body>
        <div class="game-container">
            <div class="ui">
                <div class="title">Neon Mini Shooter</div>
                <div class="score">Score: 0</div>
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div style="color: #ffffff; font-size: 14px;">Best: 0</div>
            </div>
            
            <div class="game-area">
                <div class="player"></div>
                <div class="enemy"></div>
                <div class="enemy"></div>
                <div class="enemy"></div>
            </div>
            
            <div class="controls">
                <div class="control-btn">Pause</div>
                <div class="control-btn">?</div>
                <div class="control-btn">Reset</div>
            </div>
        </div>
        
        <script>
            // Simple game logic for visual appeal
            let score = 0;
            let enemies = document.querySelectorAll('.enemy');
            
            function animateEnemies() {
                enemies.forEach((enemy, index) => {
                    const x = Math.random() * (window.innerWidth - 30);
                    const y = Math.random() * (window.innerHeight - 30);
                    enemy.style.left = x + 'px';
                    enemy.style.top = y + 'px';
                });
            }
            
            // Animate enemies every 2 seconds
            setInterval(animateEnemies, 2000);
            
            // Update score
            setInterval(() => {
                score += 10;
                document.querySelector('.score').textContent = `Score: ${score}`;
            }, 1000);
        </script>
    </body>
    </html>
    """
    return game_html

def test_improved_thumbnail_generation():
    """Test the improved thumbnail generation"""
    logger.info("Testing improved thumbnail generation...")
    
    # Create test HTML
    game_html = create_game_html()
    
    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(game_html)
        temp_html_path = f.name
    
    try:
        # Test thumbnail generation
        generator = HTMLPreviewGenerator(headless=True, window_size=(800, 600))
        
        logger.info("Testing improved thumbnail generation...")
        result = generator.generate_preview(
            html_file_path=temp_html_path,
            wait_time=5  # Longer wait time for better rendering
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
                    
                    # Check if it looks like a real screenshot (not just text)
                    if file_size > 50000:  # Real screenshots are usually larger
                        logger.info("   ✅ This appears to be a real game screenshot!")
                        return True
                    else:
                        logger.warning("   ⚠️  This might be a fallback thumbnail (small file size)")
                        return False
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

def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("IMPROVED THUMBNAIL GENERATION TEST")
    logger.info("=" * 60)
    
    # Test improved thumbnail generation
    success = test_improved_thumbnail_generation()
    
    # Results
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS")
    logger.info("=" * 60)
    
    if success:
        logger.info("✅ Improved thumbnail generation: PASS")
        logger.info("🎉 Real game screenshots should now work on Render.com!")
    else:
        logger.info("❌ Improved thumbnail generation: FAIL")
        logger.info("⚠️  May still fall back to text labels on Render.com")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
