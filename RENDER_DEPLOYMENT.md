# Render.com Deployment Guide

This guide explains how to deploy your Flask game platform to Render.com with working PNG thumbnail generation.

## Problem Solved

The original issue was that PNG thumbnails weren't generating on Render.com because:
1. Chrome/ChromeDriver wasn't installed in the Render.com environment
2. Selenium WebDriver couldn't initialize without proper browser setup
3. No fallback method was available when Selenium failed

## Solution Implemented

### 1. Enhanced HTML Preview Generator
- **Fallback Method**: Uses PIL (Pillow) to create thumbnails when Selenium fails
- **Render.com Detection**: Automatically detects Render.com environment
- **Better Error Handling**: Comprehensive logging and graceful degradation
- **Multiple Driver Support**: Uses undetected-chromedriver for better compatibility

### 2. Deployment Configuration
- **render.yaml**: Proper Render.com configuration with Chrome installation
- **Procfile**: Alternative deployment method
- **setup_render.py**: Automated setup script for Chrome/ChromeDriver

### 3. Dependencies Added
- `Pillow==10.1.0`: For fallback image generation
- `undetected-chromedriver==3.5.4`: Better Chrome driver for cloud environments

## Files Created/Modified

### New Files:
- `render.yaml` - Render.com deployment configuration
- `Procfile` - Alternative deployment method
- `setup_render.py` - Chrome/ChromeDriver installation script
- `RENDER_DEPLOYMENT.md` - This guide

### Modified Files:
- `html_preview_generator.py` - Enhanced with fallback methods
- `requirements.txt` - Added new dependencies

## Deployment Steps

### Option 1: Using render.yaml (Recommended)
1. Push your code to GitHub
2. In Render.com dashboard, create a new Web Service
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. The deployment will:
   - Install Python dependencies
   - Run the setup script to install Chrome/ChromeDriver
   - Start the application with Gunicorn

### Option 2: Using Procfile
1. Push your code to GitHub
2. In Render.com dashboard, create a new Web Service
3. Connect your GitHub repository
4. Set the build command to: `pip install -r requirements.txt`
5. Set the start command to: `python setup_render.py && gunicorn -k gthread -w 1 --threads 8 --timeout 300 --graceful-timeout 180 --keep-alive 5 app:app --bind 0.0.0.0:$PORT`

## Environment Variables Required

Make sure to set these in your Render.com dashboard:

```
FLASK_ENV=production
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_secret_key
```

## How Thumbnail Generation Works

### Primary Method (Selenium + Chrome)
1. Creates temporary HTML file
2. Launches headless Chrome browser
3. Loads HTML file and waits for rendering
4. Takes screenshot and saves as PNG
5. Cleans up temporary files

### Fallback Method (PIL)
1. Reads HTML content
2. Extracts game title
3. Creates image with PIL
4. Draws title and "HTML Game" text
5. Saves as PNG thumbnail

### Automatic Fallback
- If Selenium fails to initialize (no Chrome/ChromeDriver)
- If WebDriver throws an error during screenshot
- If the generated screenshot is empty or corrupted

## Troubleshooting

### If thumbnails still don't generate:
1. Check Render.com logs for errors
2. Verify Chrome installation in setup script
3. Check if fallback method is being used
4. Ensure all environment variables are set

### Common Issues:
- **Chrome not found**: Setup script will install Chrome automatically
- **Permission denied**: ChromeDriver needs executable permissions
- **Memory issues**: Render.com starter plan has limited memory
- **Timeout errors**: Increase wait times in thumbnail generation

## Testing Locally

To test the thumbnail generation locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Test thumbnail generation
python html_preview_generator.py path/to/game.html

# Test the setup script
python setup_render.py
```

## Monitoring

Check your Render.com logs to see:
- Chrome installation progress
- Thumbnail generation attempts
- Fallback method usage
- Any errors or warnings

The application will log detailed information about thumbnail generation, making it easy to debug issues.

## Performance Notes

- **Selenium method**: Higher quality thumbnails, requires more resources
- **PIL fallback**: Faster, lower resource usage, basic thumbnails
- **Memory usage**: Chrome can be memory-intensive on Render.com starter plan
- **Startup time**: First thumbnail generation may be slower due to Chrome initialization

## Success Indicators

You'll know the deployment is working when:
1. Games upload successfully
2. Thumbnails appear in the games list
3. No errors in Render.com logs
4. Both AI-generated and uploaded games show thumbnails

The system is designed to always generate some form of thumbnail, even if the primary method fails.
