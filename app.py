from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import os
import logging
import json
import tempfile
from dotenv import load_dotenv
from config import config
from supabase_client import supabase_manager
from stripe_client import stripe_manager
from html_preview_generator import HTMLPreviewGenerator
import openai
import stripe

# Load environment variables from .env file
load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load configuration
config_name = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

# OpenAI configuration
openai_api_key = app.config.get('OPENAI_API_KEY')
if openai_api_key:
    openai.api_key = openai_api_key
    client = openai.OpenAI(api_key=openai_api_key)
else:
    logger.warning("⚠️  OpenAI API key not found. Game generation will not work.")
    client = None

# DeepSeek configuration
deepseek_api_key = app.config.get('DEEPSEEK_API_KEY')
if deepseek_api_key:
    deepseek_client = openai.OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")
else:
    logger.warning("⚠️  DeepSeek API key not found. DeepSeek model will not work.")
    deepseek_client = None

# Available AI models configuration
AVAILABLE_MODELS = {
    "gpt-5": {
        "name": "GPT-5",
        "api_url": "https://api.openai.com/v1/chat/completions",
        "supports_json_mode": True
    },
    "deepseek-chat": {
        "name": "DeepSeek Chat",
        "api_url": "https://api.deepseek.com/v1/chat/completions",
        "supports_json_mode": True
    },
    "gpt-5-mini": {
        "name": "GPT-5 Mini",
        "api_url": "https://api.openai.com/v1/chat/completions",
        "supports_json_mode": True
    }
}

def get_default_model():
    """Get the default OpenAI model"""
    return "gpt-5"

def get_model_config(model_id):
    """Get configuration for a specific model"""
    return AVAILABLE_MODELS.get(model_id, AVAILABLE_MODELS["gpt-5"])

def map_obfuscated_model(obfuscated_model):
    """Map obfuscated model values to actual model names"""
    model_mapping = {
        'QP': 'deepseek-chat',
        'PG': 'gpt-5-mini',
        'PE': 'gpt-5'
    }
    return model_mapping.get(obfuscated_model, 'gpt-5')

def generate_game_with_deepseek(user_prompt: str):
    """Generate a game using DeepSeek API"""
    if not deepseek_client:
        logger.error("DeepSeek client not initialized. Please check DEEPSEEK_API_KEY.")
        return None
        
    try:
        logger.info(f"Generating game with DeepSeek and prompt: {user_prompt[:100]}...")
        
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS_ONE_CALL},
                {"role": "user", "content": build_user_message(user_prompt)},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
            stream=False
        )
        
        content = response.choices[0].message.content.strip()
        logger.info(f"DeepSeek response received, length: {len(content)}")
        
        # Parse JSON response
        try:
            game_data = json.loads(content)
            if "title" in game_data and "html" in game_data:
                # Fix encoding issues in the generated HTML content
                game_data["html"] = fix_text_encoding(game_data["html"])
                game_data["title"] = fix_text_encoding(game_data["title"])
                return game_data
            else:
                logger.error("Invalid game data structure from DeepSeek")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from DeepSeek response: {e}")
            logger.error(f"Response content: {content[:500]}...")
            return None
            
    except Exception as e:
        logger.error(f"Error generating game with DeepSeek: {e}")
        return None

def refine_game_with_deepseek(instruction: str, current_html: str):
    """Refine existing game using DeepSeek API"""
    if not deepseek_client:
        logger.error("DeepSeek client not initialized. Please check DEEPSEEK_API_KEY.")
        return None
        
    SYSTEM = (
        "You are a senior front-end engineer. "
        "You will receive an existing FULL, self-contained HTML game. "
        "Apply the user's instructions and RETURN ONLY a full, valid HTML document "
        "(<html>...</html>) with inline CSS + vanilla JS; no external resources; "
        "no markdown, no JSON, no commentary."
    )
    USER = (
        "USER_INSTRUCTIONS:\n"
        f"{instruction}\n\n"
        "CURRENT_GAME_HTML:\n"
        f"{current_html}"
    )
    
    try:
        logger.info(f"Refining game with DeepSeek and instruction: {instruction[:100]}...")
        
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": USER},
            ],
            temperature=0.1,
            stream=False
        )
        
        new_html = response.choices[0].message.content.strip()
        logger.info(f"DeepSeek refinement completed, HTML length: {len(new_html)}")
        
        if new_html and (new_html.startswith("<!") or new_html.startswith("<html")):
            # Fix encoding issues in the refined HTML content
            new_html = fix_text_encoding(new_html)
            return new_html
        else:
            logger.error("Invalid HTML returned from DeepSeek refinement")
            logger.error(f"HTML starts with: {new_html[:50] if new_html else 'None'}")
            return None
            
    except Exception as e:
        logger.error(f"Error refining game with DeepSeek: {e}")
        return None

def fix_text_encoding(text):
    """Fix common text encoding issues in HTML content"""
    if not text:
        return text
    
    original_text = text
    
    # Fix common UTF-8 encoding issues that occur in OpenAI generated content
    fixes = {
        'â': '-',           # Fix hyphen encoding (most common issue)
        'Â': ' ',           # Fix space encoding
        'â€™': "'",         # Fix apostrophe
        'â€œ': '"',         # Fix opening quote
        'â€': '"',          # Fix closing quote
        'â€¦': '...',       # Fix ellipsis
        'â€"': '--',        # Fix em dash
        '\u201d': '-',      # Fix en dash using unicode  
        '\u2019': "'",      # Fix apostrophe using unicode
        'Ã¢â‚¬â€œ': '-',    # Another common hyphen encoding
        'Ã¢â‚¬â„¢': "'",    # Another apostrophe encoding
        'Ã¢ÂÂ': '-',        # Yet another hyphen pattern
        'ÃÂ': '-',          # Simple hyphen corruption
        # Add more specific patterns for "Tic-Tac-Toe" corruption
        'TicâTacâToe': 'Tic-Tac-Toe',
        'TicÂTacÂToe': 'Tic-Tac-Toe',
    }
    
    applied_fixes = []
    for bad_char, good_char in fixes.items():
        if bad_char in text:
            text = text.replace(bad_char, good_char)
            applied_fixes.append(f"{bad_char} -> {good_char}")
    
    # Log applied fixes for debugging
    if applied_fixes and logger:
        logger.info(f"Applied encoding fixes: {', '.join(applied_fixes)}")
    
    return text


def generate_game_thumbnail_with_multiple_attempts(html_content: str, game_title: str) -> str:
    """
    Generate a thumbnail with 3 attempts and increasing wait times
    
    Args:
        html_content: The HTML content of the game
        game_title: The title of the game
        
    Returns:
        Path to the generated thumbnail file, or None if all attempts failed
    """
    wait_times = [2, 8, 15]  # Increasing wait times for each attempt
    
    for attempt in range(3):
        try:
            logger.info(f"Thumbnail generation attempt {attempt + 1}/3 for {game_title}")
            
            temp_html_path = None
            generator = None
            
            try:
                # Validate HTML content
                if not html_content or len(html_content.strip()) == 0:
                    logger.error("Empty HTML content provided for thumbnail generation")
                    return None
                
                # Create a temporary HTML file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                    temp_file.write(html_content)
                    temp_html_path = temp_file.name
                
                logger.info(f"Created temporary HTML file: {temp_html_path}")
                
                # Generate thumbnail using HTMLPreviewGenerator
                generator = HTMLPreviewGenerator(headless=True, window_size=(800, 600))
                
                # Generate the thumbnail with current attempt's wait time
                thumbnail_path = generator.generate_preview(
                    html_file_path=temp_html_path,
                    wait_time=wait_times[attempt]
                )
                
                if thumbnail_path and os.path.exists(thumbnail_path):
                    file_size = os.path.getsize(thumbnail_path)
                    logger.info(f"Attempt {attempt + 1} thumbnail generated successfully: {thumbnail_path} (size: {file_size} bytes)")
                    
                    # Validate thumbnail file
                    if file_size > 0:
                        return thumbnail_path
                    else:
                        logger.error(f"Attempt {attempt + 1} generated thumbnail file is empty")
                else:
                    logger.error(f"Attempt {attempt + 1} failed to generate thumbnail")
                    
            except Exception as e:
                logger.error(f"Error in attempt {attempt + 1} for {game_title}: {e}")
                
            finally:
                # Clean up generator
                if generator:
                    try:
                        generator.close()
                    except Exception as e:
                        logger.warning(f"Error closing generator in attempt {attempt + 1}: {e}")
                
                # Clean up temporary HTML file
                if temp_html_path and os.path.exists(temp_html_path):
                    try:
                        os.unlink(temp_html_path)
                    except Exception as e:
                        logger.warning(f"Failed to clean up temporary file in attempt {attempt + 1}: {e}")
            
            # If this attempt failed and we have more attempts, wait before retrying
            if attempt < 2:
                logger.info(f"Waiting 2 seconds before attempt {attempt + 2}...")
                import time
                time.sleep(2)
                
        except Exception as e:
            logger.error(f"Unexpected error in attempt {attempt + 1} for {game_title}: {e}")
    
    logger.error(f"All 3 attempts failed for thumbnail generation: {game_title}")
    return None

# Game generation system instructions
SYSTEM_INSTRUCTIONS_ONE_CALL = """
You are a senior front-end engineer and compact game designer.
You will receive a free-form idea and must produce a SINGLE-FILE browser game.

OUTPUT REQUIREMENTS
- Output ONLY valid JSON (no markdown, no comments, no extra text).
- JSON shape (strict):
  {
    "title": string,
    "html": string  // full self-contained <!doctype html> ... </html>
  }

GAME CONSTRAINTS
- One single HTML file with inline CSS + vanilla JS only.
- No external assets, no web requests, no CDNs, no fonts, no external dependencies.
- Mobile-first and accessible:
  - Respect prefers-reduced-motion
  - Provide high contrast colors
  - Ensure large tap targets
  - Ensure focus-visible states
- Must run offline in modern browsers (Chrome/Safari/Firefox).
- No console errors; concise, clean JS.
- If persistence is used, only use localStorage (safe keying) and provide a visible Reset option.

You are not allowed to output anything else besides the strict JSON.
"""

def build_user_message(user_prompt: str) -> str:
    """Build user message for game generation"""
    return (
        "Create a complete, playable browser game from this idea. "
        "Pick the most fitting genre/mechanics based on the idea. "
        "The game must follow all SYSTEM constraints above. "
        "Return ONLY strict JSON in the required schema.\n\n"
        f"USER_IDEA:\n{user_prompt}"
    )

def generate_game_with_ai(user_prompt: str, model_id: str = "gpt-5"):
    """Generate a game using AI API"""
    model_config = get_model_config(model_id)
    
    # For DeepSeek, we need to use a different approach
    if model_id == "deepseek-chat":
        return generate_game_with_deepseek(user_prompt)
    
    # For OpenAI models, use the existing client
    if not client:
        logger.error("OpenAI client not initialized. Please check OPENAI_API_KEY.")
        return None
        
    try:
        logger.info(f"Generating game with {model_config['name']} and prompt: {user_prompt[:100]}...")
        
        # Prepare the request data
        data = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": SYSTEM_INSTRUCTIONS_ONE_CALL},
                {"role": "user", "content": build_user_message(user_prompt)},
            ]
        }
        
        # Add JSON mode if supported
        if model_config.get("supports_json_mode", False):
            data["response_format"] = {"type": "json_object"}
        
        response = client.chat.completions.create(**data)
        
        content = response.choices[0].message.content.strip()
        logger.info(f"OpenAI response received, length: {len(content)}")
        
        # Parse JSON response
        try:
            game_data = json.loads(content)
            if "title" in game_data and "html" in game_data:
                # Fix encoding issues in the generated HTML content
                game_data["html"] = fix_text_encoding(game_data["html"])
                game_data["title"] = fix_text_encoding(game_data["title"])
                return game_data
            else:
                logger.error("Invalid game data structure from OpenAI")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI response: {e}")
            logger.error(f"Response content: {content[:500]}...")
            return None
            
    except Exception as e:
        logger.error(f"Error generating game with AI: {e}")
        return None

def refine_game_with_ai(instruction: str, current_html: str, model_id: str = "gpt-5"):
    """Refine existing game using AI API"""
    model_config = get_model_config(model_id)
    
    # For DeepSeek, we need to use a different approach
    if model_id == "deepseek-chat":
        return refine_game_with_deepseek(instruction, current_html)
    
    # For OpenAI models, use the existing client
    if not client:
        logger.error("OpenAI client not initialized. Please check OPENAI_API_KEY.")
        return None
        
    try:
        logger.info(f"Refining game with {model_config['name']} and instruction: {instruction[:100]}...")
        
        SYSTEM = (
            "You are a highly skilled senior front-end engineer. "
            "You will be given a complete, self-contained HTML game (with inline CSS and vanilla JS). "
            "Your task is to modify and refine this game according to the user's instructions. "
            "Important rules:\n"
            "1. Output ONLY a single, complete, valid HTML document wrapped in <html>...</html>.\n"
            "2. Use ONLY inline CSS and vanilla JS (no external libraries, no CDN links).\n"
            "3. Do NOT include markdown, JSON, comments, explanations, or extra text outside the HTML.\n"
            "4. Ensure the final game remains playable and consistent with the instructions.\n"
        )

        USER = (
            "USER INSTRUCTIONS:\n"
            f"{instruction}\n\n"
            "CURRENT GAME HTML:\n"
            f"{current_html}"
        )

        # Prepare the request data
        data = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": USER},
            ]
        }
        
        # Add JSON mode if supported (though for refinement we don't need it)
        if model_config.get("supports_json_mode", False) and model_id != "deepseek-chat":
            # For refinement, we don't use JSON mode as we want HTML output
            pass

        response = client.chat.completions.create(**data)
        
        new_html = (response.choices[0].message.content or "").strip()
        logger.info(f"Game refinement completed, HTML length: {len(new_html)}")
        
        if new_html and (new_html.startswith("<!") or new_html.startswith("<html")):
            # Fix encoding issues in the refined HTML content
            new_html = fix_text_encoding(new_html)
            return new_html
        else:
            logger.error("Invalid HTML returned from refinement")
            logger.error(f"HTML starts with: {new_html[:50] if new_html else 'None'}")
            return None
            
    except Exception as e:
        logger.error(f"Error refining game with AI: {e}")
        return None

# User management functions via Supabase
def create_user(email, password):
    """Creates a new user in Supabase Auth"""
    if not supabase_manager.is_connected():
        logger.error("Supabase not connected for user creation")
        return None
    
    try:
        logger.info(f"Creating user: email={email}")
        
        # Use a separate client instance for user creation to avoid affecting the global client
        from supabase import create_client
        auth_client = create_client(supabase_manager.url, supabase_manager.key)
        
        # Create user in auth.users with email and password only
        auth_response = auth_client.auth.sign_up({
            "email": email,
            "password": password
        })
        
        logger.info(f"Auth response: {auth_response}")
        
        if auth_response.user:
            logger.info(f"User {email} successfully created in auth.users with ID: {auth_response.user.id}")
            # Sign out from the auth client to prevent session persistence
            auth_client.auth.sign_out()
            return {
                'user': auth_response.user,
                'user_id': auth_response.user.id
            }
        else:
            logger.error(f"Failed to create user - no user in response: {auth_response}")
            return None
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        logger.error(f"Exception type: {type(e)}")
        if hasattr(e, 'response'):
            logger.error(f"Response: {e.response}")
        return None

def authenticate_user(email, password):
    """Authenticates user via Supabase Auth"""
    if not supabase_manager.is_connected():
        logger.error("Supabase not connected")
        return None
    
    try:
        logger.info(f"Authentication attempt for user: {email}")
        
        # Use a separate client instance for authentication to avoid affecting the global client
        from supabase import create_client
        auth_client = create_client(supabase_manager.url, supabase_manager.key)
        
        auth_response = auth_client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        logger.info(f"Auth response: {auth_response}")
        
        if auth_response.user:
            logger.info(f"Successful authentication for {email}")
            # Sign out from the auth client immediately to prevent session persistence
            auth_client.auth.sign_out()
            return {
                'user': auth_response.user,
                'email': auth_response.user.email
            }
        else:
            logger.warning(f"Invalid credentials for {email} - no user in response")
            return None
        
    except Exception as e:
        logger.error(f"Authentication error for {email}: {e}")
        logger.error(f"Exception type: {type(e)}")
        if hasattr(e, 'response'):
            logger.error(f"Response: {e.response}")
        return None

# Routes
@app.route('/')
def index():
    authenticated = 'user_id' in session
    
    # Get trending games (most liked) for the homepage
    trending_games = []
    user_liked_games = []
    
    try:
        if supabase_manager.is_connected():
            # Get top 3 trending games ordered by likes with nicknames
            uploaded_games_raw = supabase_manager.get_games_with_nicknames(limit=3, order_by='likes_count')
            
            # Get user's liked games if authenticated
            if 'user_id' in session:
                user_liked_games = supabase_manager.get_user_liked_games(str(session['user_id']))
            
            # Transform games for homepage
            for game in uploaded_games_raw:
                # Use actual user-provided title, fallback to filename if not available
                title = game.get('title')
                if not title:
                    # Fallback: extract title from filename (remove .html extension)
                    title = game.get('filename', 'Untitled Game')
                    if title.endswith('.html'):
                        title = title[:-5]
                    title = title.replace('-', ' ').replace('_', ' ').title()
                
                # Use actual user-provided description, fallback to generic
                description = game.get('description')
                if not description:
                    description = f'Trending community game: {title}'
                
                # Get stats
                likes_count = game.get('likes_count', 0)
                plays_count = game.get('plays_count', 0)
                
                trending_games.append({
                    'id': game.get('id'),
                    'title': title,
                    'plays': f"{plays_count}",
                    'likes_count': likes_count,
                    'is_liked': game.get('id') in user_liked_games,
                    'description': description,
                    'created_at': game.get('created_at'),
                    'thumbnail_url': game.get('thumbnail_url'),
                    'user_nickname': game.get('user_nickname'),
                    'user_id': game.get('user_id')
                })
    except Exception as e:
        logger.error(f"Error fetching trending games: {e}")
    
    return render_template('index.html', authenticated=authenticated, trending_games=trending_games)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if not email or not password or not confirm_password:
            error_msg = 'All fields are required!'
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return jsonify({'success': False, 'error': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return render_template('register.html')
        
        if password != confirm_password:
            error_msg = 'Passwords do not match!'
            logger.warning(f"Password mismatch attempt for email: {email}")
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return jsonify({'success': False, 'error': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return render_template('register.html')
        
        # Create new user in Supabase
        try:
            result = create_user(email, password)
            if result:
                # Ensure user gets 2 credits upon registration
                user_id = result['user_id']
                if supabase_manager.is_connected():
                    # Create credits record for new user (should be automatic via trigger, but ensure it exists)
                    current_credits = supabase_manager.get_user_credits(user_id)
                    if current_credits == 0:
                        # If no credits record exists, create one with 2 credits
                        supabase_manager.create_user_credits_record(user_id, 2)
                        logger.info(f"Created credits record for new user {user_id} with 2 credits")
                
                success_msg = 'Registration successful! You can now log in.'
                # Check if this is an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({'success': True, 'message': success_msg})
                else:
                    flash(success_msg, 'success')
                    return redirect(url_for('login'))
            else:
                error_msg = 'Registration failed. A user with this email may already exist.'
                # Check if this is an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({'success': False, 'error': error_msg}), 400
                else:
                    flash(error_msg, 'error')
        except Exception as e:
            logger.error(f"Registration error: {e}")
            error_msg = 'Registration failed. Please try again.'
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return jsonify({'success': False, 'error': error_msg}), 500
            else:
                flash(error_msg, 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Authenticate user
        auth_result = authenticate_user(email, password)
        
        if auth_result:
            session['user_id'] = auth_result['user'].id
            session['email'] = auth_result['user'].email
            
            # Check if this is an AJAX request (from modal)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                # For AJAX requests, return JSON - stay on same page
                return jsonify({'success': True, 'stay_on_page': True})
            else:
                flash('Successfully logged in!', 'success')
                return redirect(url_for('index'))
        else:
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return jsonify({'success': False, 'error': 'Invalid email or password!'}), 400
            else:
                flash('Invalid email or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear Flask session (no need to sign out from Supabase since we don't maintain persistent auth sessions)
    session.clear()
    flash('Successfully logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/games')
def games():
    """Games page - displays all uploaded games from the database with likes and stats"""
    uploaded_games = []
    user_liked_games = []
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'likes_count').strip()
    
    # Validate sort parameter
    valid_sorts = ['likes_count', 'created_at', 'plays_count']
    if sort_by not in valid_sorts:
        sort_by = 'likes_count'
    
    try:
        if supabase_manager.is_connected():
            # Get games with statistics and nicknames ordered by selected sort option
            if search_query:
                uploaded_games_raw = supabase_manager.search_games_with_stats(search_query, order_by=sort_by)
            else:
                uploaded_games_raw = supabase_manager.get_games_with_nicknames(order_by=sort_by)
            
            # Get user's liked games if authenticated
            if 'user_id' in session:
                user_liked_games = supabase_manager.get_user_liked_games(str(session['user_id']))
            
            # Transform uploaded games to match template format
            for game in uploaded_games_raw:
                # Use actual user-provided title, fallback to filename if not available
                title = game.get('title')
                if not title:
                    # Fallback: extract title from filename (remove .html extension)
                    title = game.get('filename', 'Untitled Game')
                    if title.endswith('.html'):
                        title = title[:-5]
                    title = title.replace('-', ' ').replace('_', ' ').title()
                
                # Use actual user-provided description, fallback to generic
                description = game.get('description')
                if not description:
                    description = f'Community game: {title}'
                
                # Get stats
                likes_count = game.get('likes_count', 0)
                plays_count = game.get('plays_count', 0)
                
                uploaded_games.append({
                    'id': game.get('id'),
                    'title': title,
                    'plays': f"{plays_count}",
                    'likes_count': likes_count,
                    'is_liked': game.get('id') in user_liked_games,
                    'description': description,
                    'type': 'uploaded',
                    'filename': game.get('filename'),
                    'data_content': game.get('data_content'),
                    'created_at': game.get('created_at'),
                    'thumbnail_url': game.get('thumbnail_url'),
                    'user_nickname': game.get('user_nickname'),
                    'user_id': game.get('user_id')
                })
    except Exception as e:
        logger.error(f"Error fetching uploaded games: {e}")
    
    authenticated = 'user_id' in session
    return render_template('games.html', games=uploaded_games, authenticated=authenticated, search_query=search_query, sort_by=sort_by)

@app.route('/create-game')
def create_game():
    """Create game page - requires authentication"""
    if 'user_id' not in session:
        flash('Please log in to create a game.', 'error')
        return redirect(url_for('index'))
    
    # Get user's current credits
    user_credits = 0
    if supabase_manager.is_connected():
        user_credits = supabase_manager.get_user_credits(str(session['user_id']))
    
    # Define model pricing
    model_prices = {
        'QP': 1,  # Quick Prototype - 1 credit
        'PG': 2,  # Polished Game - 2 credits
        'PE': 6   # Premium Experience - 6 credits
    }
    
    authenticated = 'user_id' in session
    return render_template('create_game.html', 
                         authenticated=authenticated, 
                         user_credits=user_credits,
                         model_prices=model_prices)


@app.route('/my-games')
def my_games():
    """View user's uploaded games - requires authentication"""
    if 'user_id' not in session:
        flash('Please log in to view your games.', 'error')
        return redirect(url_for('index'))
    
    search_query = request.args.get('search', '').strip()
    
    try:
        # Get user's uploaded games from Supabase
        if search_query:
            user_games = supabase_manager.search_user_games(str(session['user_id']), search_query)
        else:
            user_games = supabase_manager.get_user_data(str(session['user_id']))
        
        # Filter for HTML games
        html_games = [game for game in user_games if game.get('data_type') == 'html_game']
        
        # Get user's current credits
        user_credits = 0
        if supabase_manager.is_connected():
            user_credits = supabase_manager.get_user_credits(str(session['user_id']))
        
        # Get user's nickname
        user_nickname = None
        if supabase_manager.is_connected():
            user_nickname = supabase_manager.get_user_nickname(str(session['user_id']))
        
        authenticated = 'user_id' in session
        return render_template('my_games.html', games=html_games, authenticated=authenticated, user_credits=user_credits, user_nickname=user_nickname, search_query=search_query)
        
    except Exception as e:
        logger.error(f"Error fetching user games: {e}")
        flash('Error loading your games. Please try again.', 'error')
        return redirect(url_for('index'))


@app.route('/set-nickname', methods=['POST'])
def set_nickname():
    """Set or update user's nickname"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please log in to set your nickname.'}), 401
    
    try:
        data = request.get_json()
        nickname = data.get('nickname', '').strip()
        
        if not nickname:
            return jsonify({'success': False, 'error': 'Nickname cannot be empty.'}), 400
        
        # Validate nickname length and characters
        if len(nickname) < 2 or len(nickname) > 50:
            return jsonify({'success': False, 'error': 'Nickname must be between 2 and 50 characters.'}), 400
        
        # Check for valid characters (alphanumeric, spaces, hyphens, underscores)
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', nickname):
            return jsonify({'success': False, 'error': 'Nickname can only contain letters, numbers, spaces, hyphens, and underscores.'}), 400
        
        # Set the nickname
        success = supabase_manager.set_user_nickname(str(session['user_id']), nickname)
        
        if success:
            return jsonify({'success': True, 'message': 'Nickname saved successfully!'})
        else:
            return jsonify({'success': False, 'error': 'Failed to save nickname. It may already be taken.'}), 400
            
    except Exception as e:
        logger.error(f"Error setting nickname: {e}")
        return jsonify({'success': False, 'error': 'An error occurred while saving your nickname.'}), 500


@app.route('/delete-nickname', methods=['POST'])
def delete_nickname():
    """Delete user's nickname"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please log in to delete your nickname.'}), 401
    
    try:
        success = supabase_manager.delete_user_nickname(str(session['user_id']))
        
        if success:
            return jsonify({'success': True, 'message': 'Nickname deleted successfully!'})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete nickname.'}), 400
            
    except Exception as e:
        logger.error(f"Error deleting nickname: {e}")
        return jsonify({'success': False, 'error': 'An error occurred while deleting your nickname.'}), 500


@app.route('/play-uploaded/<game_id>')
def play_uploaded_game(game_id):
    """Play any user's uploaded HTML game - accessible to all users"""
    try:
        # Get the specific game data by ID (from any user)
        game = supabase_manager.get_game_by_id(str(game_id))
        
        if not game:
            flash('Game not found.', 'error')
            return redirect(url_for('games'))
        
        # Get the author's nickname
        author_nickname = None
        if game.get('user_id'):
            author_nickname = supabase_manager.get_user_nickname(str(game['user_id']))
        
        # Add nickname to game data
        game['author_nickname'] = author_nickname
        
        # Increment play count
        supabase_manager.increment_game_play_count(str(game_id))
        
        authenticated = 'user_id' in session
        return render_template('play_uploaded_game.html', game=game, authenticated=authenticated)
        
    except Exception as e:
        logger.error(f"Error loading uploaded game: {e}")
        flash('Error loading game. Please try again.', 'error')
        return redirect(url_for('games'))

@app.route('/game-content/<game_id>')
def get_game_content(game_id):
    """Serve the HTML content of any game directly - accessible to all users"""
    try:
        # Get the specific game data by ID (from any user)
        game = supabase_manager.get_game_by_id(str(game_id))
        
        if not game:
            return "Game not found", 404
        
        # Fetch the HTML content from the storage URL
        import requests
        try:
            response = requests.get(game['data_content'], timeout=10)
            if response.status_code == 200:
                # Get the HTML content and fix encoding issues
                html_content = response.text
                
                # Log original content length for debugging
                logger.info(f"Original HTML content length: {len(html_content)}")
                
                # Try to fix encoding at byte level first
                try:
                    # If the content was improperly decoded, try to re-encode and decode correctly
                    if 'â' in html_content or 'Â' in html_content:
                        # Try to fix by re-encoding as latin-1 and decoding as utf-8
                        try:
                            fixed_content = html_content.encode('latin-1').decode('utf-8')
                            html_content = fixed_content
                            logger.info("Applied byte-level encoding fix")
                        except (UnicodeEncodeError, UnicodeDecodeError):
                            # If that fails, use the character-level fixes
                            pass
                except Exception as e:
                    logger.warning(f"Byte-level encoding fix failed: {e}")
                
                # Fix common encoding issues in the HTML content
                html_content = fix_text_encoding(html_content)
                
                # Log if changes were made
                if len(html_content) != len(response.text):
                    logger.info(f"Encoding fixes applied, new length: {len(html_content)}")
                
                # Return the fixed HTML content with proper headers
                return html_content, 200, {
                    'Content-Type': 'text/html; charset=utf-8',
                    'X-Frame-Options': 'SAMEORIGIN'
                }
            else:
                return f"Error loading game content: {response.status_code}", 500
        except requests.RequestException as e:
            logger.error(f"Error fetching game content: {e}")
            return "Error loading game content", 500
        
    except Exception as e:
        logger.error(f"Error serving game content: {e}")
        return "Error loading game", 500

# Legacy routes for backward compatibility
@app.route('/save_data', methods=['POST'])
def save_data():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data_type = request.form.get('data_type', 'text')
    data_content = request.form.get('data_content', '')
    filename = request.form.get('filename', '')
    
    if not data_content:
        return jsonify({'error': 'Content cannot be empty'}), 400
    
    if not supabase_manager.is_connected():
        return jsonify({'error': 'Supabase not connected. Check settings.'}), 500
    
    try:
        # Save to Supabase only
        result = supabase_manager.save_user_data(
            user_id=str(session['user_id']),
            data_type=data_type,
            data_content=data_content,
            filename=filename
        )
        
        if result:
            logger.info("Data saved to Supabase")
            return jsonify({'success': True, 'message': 'Data saved successfully'})
        else:
            return jsonify({'error': 'Error saving data to Supabase'}), 500
            
    except Exception as e:
        logger.error(f"Error saving data: {e}")
        return jsonify({'error': 'Error saving data'}), 500

@app.route('/delete_data/<data_id>', methods=['POST'])
def delete_data(data_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    if not supabase_manager.is_connected():
        return jsonify({'error': 'Supabase not connected. Check settings.'}), 500
    
    try:
        # Delete from Supabase only
        result = supabase_manager.delete_user_data(
            data_id=str(data_id),
            user_id=str(session['user_id'])
        )
        
        if result:
            logger.info("Data deleted from Supabase")
            return jsonify({'success': True, 'message': 'Data deleted successfully'})
        else:
            return jsonify({'error': 'Data not found or error deleting'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting data: {e}")
        return jsonify({'error': 'Error deleting data'}), 500

# Stripe Payment Links integration for balance top-ups
@app.route('/payment')
def payment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if not stripe_manager.is_configured():
        flash('Stripe not configured. Payment feature will be available after setup', 'warning')
        return redirect(url_for('my_games'))
    
    # Get user's current credits
    user_credits = 0
    if supabase_manager.is_connected():
        user_credits = supabase_manager.get_user_credits(str(session['user_id']))
    
    # Define credit packages with Payment Links
    credit_packages = [
        {
            'credits': 50, 
            'price': 5.00, 
            'price_cents': 500, 
            'name': 'Starter Pack', 
            'description': 'Perfect for trying out our AI game generation', 
            'price_per_credit': 0.10,
            'payment_link_url': 'https://buy.stripe.com/test_5kQ7sM1Gy6Kj0sz0b88g003'
        },
        {
            'credits': 120, 
            'price': 10.00, 
            'price_cents': 1000, 
            'name': 'Creator Pack', 
            'description': 'Great for regular game creators', 
            'popular': True, 
            'price_per_credit': 0.083,
            'payment_link_url': 'https://buy.stripe.com/test_8x228s9904Cbcbh4ro8g004'
        },
        {
            'credits': 300, 
            'price': 20.00, 
            'price_cents': 2000, 
            'name': 'Pro Pack', 
            'description': 'Best value for serious game developers', 
            'price_per_credit': 0.067,
            'payment_link_url': 'https://buy.stripe.com/test_4gMdRa2KC3y7grx7DA8g005'
        }
    ]
    
    authenticated = 'user_id' in session
    return render_template('payment.html', 
                         authenticated=authenticated, 
                         user_credits=user_credits,
                         credit_packages=credit_packages,
                         stripe_publishable_key=stripe_manager.publishable_key)

@app.route('/create_payment_intent', methods=['POST'])
def create_payment_intent():
    """Creates payment intent via Stripe"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    if not stripe_manager.is_configured():
        return jsonify({'error': 'Stripe not configured'}), 400
    
    try:
        amount = int(request.json.get('amount', 1000))  # Default $10.00
        currency = request.json.get('currency', 'usd')
        
        # Get email from session
        user_email = session.get('email')
        if not user_email:
            return jsonify({'error': 'User email not found in session'}), 400
        
        # Create or get Stripe customer
        customer = stripe_manager.get_customer_by_email(user_email)
        if not customer:
            customer = stripe_manager.create_customer(user_email, user_email)
        
        if customer:
            # Create payment intent
            intent = stripe_manager.create_payment_intent(
                amount=amount,
                currency=currency,
                customer_id=customer.id
            )
            
            if intent:
                return jsonify({
                    'success': True,
                    'client_secret': intent.client_secret,
                    'customer_id': customer.id
                })
        
        return jsonify({'error': 'Failed to create payment intent'}), 500
        
    except Exception as e:
        logger.error(f"Error creating payment intent: {e}")
        return jsonify({'error': 'Error creating payment'}), 500

@app.route('/stripe_webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    if not stripe_manager.verify_webhook_signature(payload, sig_header):
        logger.error("Invalid webhook signature")
        return jsonify({'error': 'Invalid signature'}), 400
    
    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )
        
        # Handle successful payment (Payment Links use checkout.session.completed)
        if event.type == 'checkout.session.completed':
            session = event.data.object
            line_items = stripe.checkout.Session.list_line_items(session.id)
            
            # Get the product name to determine credits
            if line_items.data:
                product_name = line_items.data[0].description
                credits = 0
                
                # Map product names to credits
                if '50 Credits' in product_name:
                    credits = 50
                elif '120 Credits' in product_name:
                    credits = 120
                elif '300 Credits' in product_name:
                    credits = 300
                
                if credits > 0:
                    # Get customer email to find user
                    customer_email = session.customer_details.email
                    if customer_email:
                        # Find user by email
                        user = supabase_manager.get_user_by_email(customer_email)
                        if user:
                            user_id = user['id']
                            # Add credits to user account
                            success = supabase_manager.add_credits(user_id, credits)
                            if success:
                                logger.info(f"Added {credits} credits to user {user_id} ({customer_email}) after successful payment")
                            else:
                                logger.error(f"Failed to add credits to user {user_id}")
                        else:
                            logger.error(f"User not found for email: {customer_email}")
                    else:
                        logger.error("No customer email found in checkout session")
                else:
                    logger.error(f"Unknown product in checkout session: {product_name}")
            else:
                logger.error("No line items found in checkout session")
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'error': 'Webhook processing failed'}), 500

@app.route('/payment_success')
def payment_success():
    """Handle successful payment redirects"""
    if 'user_id' not in session:
        flash('Please log in to view your payment status.', 'error')
        return redirect(url_for('login'))
    
    # Get updated user credits
    user_credits = 0
    if supabase_manager.is_connected():
        user_credits = supabase_manager.get_user_credits(str(session['user_id']))
    
    flash('Payment successful! Your credits have been added to your account.', 'success')
    return redirect(url_for('my_games'))

# ============ LIKES SYSTEM ROUTES ============

@app.route('/like_game', methods=['POST'])
def like_game():
    """Like a game - requires authentication"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        game_id = data.get('game_id')
        
        if not game_id:
            return jsonify({'error': 'Game ID is required'}), 400
        
        # Verify game exists
        game = supabase_manager.get_game_by_id(str(game_id))
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        # Like the game
        success = supabase_manager.like_game(str(game_id), str(session['user_id']))
        
        if success:
            return jsonify({'success': True, 'message': 'Game liked successfully'})
        else:
            return jsonify({'error': 'Failed to like game'}), 500
            
    except Exception as e:
        logger.error(f"Error liking game: {e}")
        return jsonify({'error': 'Error liking game'}), 500

@app.route('/unlike_game', methods=['POST'])
def unlike_game():
    """Unlike a game - requires authentication"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        game_id = data.get('game_id')
        
        if not game_id:
            return jsonify({'error': 'Game ID is required'}), 400
        
        # Unlike the game
        success = supabase_manager.unlike_game(str(game_id), str(session['user_id']))
        
        if success:
            return jsonify({'success': True, 'message': 'Game unliked successfully'})
        else:
            return jsonify({'error': 'Failed to unlike game'}), 500
            
    except Exception as e:
        logger.error(f"Error unliking game: {e}")
        return jsonify({'error': 'Error unliking game'}), 500

@app.route('/toggle_like_game', methods=['POST'])
def toggle_like_game():
    """Toggle like status for a game - requires authentication"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        game_id = data.get('game_id')
        
        if not game_id:
            return jsonify({'error': 'Game ID is required'}), 400
        
        # Check current like status
        is_liked = supabase_manager.is_game_liked_by_user(str(game_id), str(session['user_id']))
        
        if is_liked:
            # Unlike the game
            success = supabase_manager.unlike_game(str(game_id), str(session['user_id']))
            action = 'unliked'
        else:
            # Like the game
            success = supabase_manager.like_game(str(game_id), str(session['user_id']))
            action = 'liked'
        
        if success:
            return jsonify({
                'success': True, 
                'action': action,
                'is_liked': not is_liked,
                'message': f'Game {action} successfully'
            })
        else:
            return jsonify({'error': f'Failed to {action.replace("ed", "")} game'}), 500
            
    except Exception as e:
        logger.error(f"Error toggling like for game: {e}")
        return jsonify({'error': 'Error updating like status'}), 500

# AI Game Generation API Endpoints
@app.route('/api/generate-game', methods=['POST'])
def api_generate_game():
    """Generate a new game using AI"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        prompt = (data.get('prompt') or '').strip()
        obfuscated_model = data.get('model', 'PE')  # Default to PE (gpt-5) if not specified
        model = map_obfuscated_model(obfuscated_model)  # Convert to actual model name
        
        if not prompt:
            return jsonify({'error': 'Game prompt is required'}), 400
        
        # Define model pricing
        model_prices = {
            'QP': 1,  # Quick Prototype - 1 credit
            'PG': 2,  # Polished Game - 2 credits
            'PE': 6   # Premium Experience - 6 credits
        }
        
        # Check if user has enough credits
        required_credits = model_prices.get(obfuscated_model, 6)
        user_credits = supabase_manager.get_user_credits(str(session['user_id']))
        
        if user_credits < required_credits:
            return jsonify({
                'error': f'Insufficient credits. You need {required_credits} credits but only have {user_credits}.',
                'error_type': 'insufficient_credits',
                'required_credits': required_credits,
                'current_credits': user_credits
            }), 400
        
        # Deduct credits FIRST before generating the game
        deduction_success = supabase_manager.deduct_credits(str(session['user_id']), required_credits)
        if not deduction_success:
            return jsonify({
                'error': f'Failed to deduct credits. You need {required_credits} credits but only have {user_credits}.',
                'error_type': 'insufficient_credits',
                'required_credits': required_credits,
                'current_credits': user_credits
            }), 400
        
        # Generate game with AI
        game_data = generate_game_with_ai(prompt, model)
        
        if game_data:
            # Get remaining credits after successful generation
            remaining_credits = supabase_manager.get_user_credits(str(session['user_id']))
            
            return jsonify({
                'success': True,
                'title': game_data['title'],
                'html': game_data['html'],
                'credits_deducted': required_credits,
                'remaining_credits': remaining_credits
            })
        else:
            # If generation fails, refund the credits
            supabase_manager.add_credits(str(session['user_id']), required_credits)
            return jsonify({
                'error': 'Failed to generate game content. Credits have been refunded. Please try again.'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in game generation API: {e}")
        # If we deducted credits but hit an error, refund them
        try:
            data = request.get_json()
            obfuscated_model = data.get('model', 'PE')
            model_prices = {
                'QP': 1, 'PG': 2, 'PE': 6
            }
            required_credits = model_prices.get(obfuscated_model, 6)
            supabase_manager.add_credits(str(session['user_id']), required_credits)
        except:
            pass  # If we can't refund, just log the error
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/refine-game', methods=['POST'])
def api_refine_game():
    """Refine an existing game using AI"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        instruction = (data.get('instruction') or '').strip()
        current_html = (data.get('current_html') or '').strip()
        obfuscated_model = data.get('model', 'PE')  # Default to PE (gpt-5) if not specified
        model = map_obfuscated_model(obfuscated_model)  # Convert to actual model name
        
        if not instruction:
            return jsonify({'error': 'Refinement instruction is required'}), 400
        
        if not current_html:
            return jsonify({'error': 'Current game HTML is required'}), 400
        
        # Define model pricing (same as generation)
        model_prices = {
            'QP': 1,  # Quick Prototype - 1 credit
            'PG': 2,  # Polished Game - 2 credits
            'PE': 6   # Premium Experience - 6 credits
        }
        
        # Check if user has enough credits
        required_credits = model_prices.get(obfuscated_model, 6)
        user_credits = supabase_manager.get_user_credits(str(session['user_id']))
        
        if user_credits < required_credits:
            return jsonify({
                'error': f'Insufficient credits. You need {required_credits} credits but only have {user_credits}.',
                'error_type': 'insufficient_credits',
                'required_credits': required_credits,
                'current_credits': user_credits
            }), 400
        
        # Deduct credits FIRST before refining the game
        deduction_success = supabase_manager.deduct_credits(str(session['user_id']), required_credits)
        if not deduction_success:
            return jsonify({
                'error': f'Failed to deduct credits. You need {required_credits} credits but only have {user_credits}.',
                'error_type': 'insufficient_credits',
                'required_credits': required_credits,
                'current_credits': user_credits
            }), 400
        
        # Refine game with AI
        refined_html = refine_game_with_ai(instruction, current_html, model)
        
        if refined_html:
            # Get remaining credits after successful refinement
            remaining_credits = supabase_manager.get_user_credits(str(session['user_id']))
            
            return jsonify({
                'success': True,
                'html': refined_html,
                'credits_deducted': required_credits,
                'remaining_credits': remaining_credits
            })
        else:
            # If refinement fails, refund the credits
            supabase_manager.add_credits(str(session['user_id']), required_credits)
            return jsonify({
                'error': 'Failed to refine game content. Credits have been refunded. Please try again.'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in game refinement API: {e}")
        # If we deducted credits but hit an error, refund them
        try:
            data = request.get_json()
            obfuscated_model = data.get('model', 'PE')
            model_prices = {
                'QP': 1, 'PG': 2, 'PE': 6
            }
            required_credits = model_prices.get(obfuscated_model, 6)
            supabase_manager.add_credits(str(session['user_id']), required_credits)
        except:
            pass  # If we can't refund, just log the error
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/publish-game', methods=['POST'])
def api_publish_game():
    """Publish AI-generated game to community"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        logger.info(f"Received publish data: {data}")
        title = (data.get('title') or '').strip()
        description = (data.get('description') or '').strip()
        html_content = (data.get('html_content') or '').strip()
        logger.info(f"Processed values - title: '{title}', description: '{description}', html_content length: {len(html_content)}")
        
        if not title:
            return jsonify({'error': 'Game title is required'}), 400
        
        if not description:
            return jsonify({'error': 'Game description is required'}), 400
        
        if not html_content:
            return jsonify({'error': 'Game HTML content is required'}), 400
        
        if not supabase_manager.is_connected():
            return jsonify({'error': 'Storage service not available'}), 500
        
        # Generate thumbnail for the AI-generated game with 3 attempts
        logger.info(f"Generating thumbnail for AI-generated game: {title}")
        thumbnail_path = generate_game_thumbnail_with_multiple_attempts(html_content, title)
        
        # Create a filename based on title
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title.replace(' ', '_').lower()}.html"
        
        # Save game to Supabase storage and create user_data record
        result = supabase_manager.save_user_file(
            user_id=str(session['user_id']),
            file_content=html_content.encode('utf-8'),
            filename=filename,
            content_type='text/html',
            title=title,
            description=description,
            thumbnail_path=thumbnail_path
        )
        
        if result:
            logger.info(f"AI-generated game published successfully for user {session['user_id']}")
            return jsonify({
                'success': True,
                'message': 'Game published successfully to the community',
                'game_id': result.get('id')
            })
        else:
            return jsonify({'error': 'Failed to publish game'}), 500
            
    except Exception as e:
        logger.error(f"Error publishing AI game: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/edit-game/<game_id>')
def edit_game(game_id):
    """Edit existing game page - requires authentication and ownership"""
    if 'user_id' not in session:
        flash('Please log in to edit games.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Get the specific game data by ID
        game = supabase_manager.get_game_by_id(str(game_id))
        
        if not game:
            flash('Game not found.', 'error')
            return redirect(url_for('my_games'))
        
        # Check if user owns this game
        if str(game.get('user_id')) != str(session['user_id']):
            flash('You can only edit your own games.', 'error')
            return redirect(url_for('my_games'))
        
        # Get user's current credits
        user_credits = 0
        if supabase_manager.is_connected():
            user_credits = supabase_manager.get_user_credits(str(session['user_id']))
        
        # Define model pricing
        model_prices = {
            'QP': 1,  # Quick Prototype - 1 credit
            'PG': 2,  # Polished Game - 2 credits
            'PE': 6   # Premium Experience - 6 credits
        }
        
        # Fetch the HTML content from the storage URL
        import requests
        try:
            response = requests.get(game['data_content'], timeout=10)
            if response.status_code == 200:
                html_content = response.text
                # Fix encoding issues
                html_content = fix_text_encoding(html_content)
                
                authenticated = 'user_id' in session
                return render_template('edit_game.html', 
                                     game=game, 
                                     html_content=html_content, 
                                     authenticated=authenticated,
                                     user_credits=user_credits,
                                     model_prices=model_prices)
            else:
                flash('Error loading game content.', 'error')
                return redirect(url_for('my_games'))
        except requests.RequestException as e:
            logger.error(f"Error fetching game content: {e}")
            flash('Error loading game content.', 'error')
            return redirect(url_for('my_games'))
        
    except Exception as e:
        logger.error(f"Error loading game for editing: {e}")
        flash('Error loading game. Please try again.', 'error')
        return redirect(url_for('my_games'))

@app.route('/api/update-game', methods=['POST'])
def api_update_game():
    """Update existing game with new version"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        game_id = data.get('game_id')
        title = (data.get('title') or '').strip()
        description = (data.get('description') or '').strip()
        html_content = (data.get('html_content') or '').strip()
        
        if not game_id:
            return jsonify({'error': 'Game ID is required'}), 400
        
        if not title:
            return jsonify({'error': 'Game title is required'}), 400
        
        if not description:
            return jsonify({'error': 'Game description is required'}), 400
        
        if not html_content:
            return jsonify({'error': 'Game HTML content is required'}), 400
        
        # Verify game exists and user owns it
        game = supabase_manager.get_game_by_id(str(game_id))
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        if str(game.get('user_id')) != str(session['user_id']):
            return jsonify({'error': 'You can only update your own games'}), 403
        
        if not supabase_manager.is_connected():
            return jsonify({'error': 'Storage service not available'}), 500
        
        # Generate new thumbnail for the updated game
        logger.info(f"Generating new thumbnail for updated game: {title}")
        try:
            thumbnail_path = generate_game_thumbnail_with_multiple_attempts(html_content, title)
            logger.info(f"Thumbnail generation result: {thumbnail_path}")
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            thumbnail_path = None
        
        # Update the game in Supabase
        logger.info(f"Attempting to update game {game_id} for user {session['user_id']}")
        logger.info(f"Title: {title}, Description: {description[:100]}..., HTML length: {len(html_content)}")
        
        result = supabase_manager.update_user_file(
            data_id=str(game_id),
            user_id=str(session['user_id']),
            file_content=html_content.encode('utf-8'),
            title=title,
            description=description,
            thumbnail_path=thumbnail_path
        )
        
        logger.info(f"Update result: {result}")
        
        if result:
            logger.info(f"Game updated successfully for user {session['user_id']}")
            return jsonify({
                'success': True,
                'message': 'Game updated successfully',
                'game_id': game_id
            })
        else:
            logger.error(f"Failed to update game {game_id} - update_user_file returned None")
            return jsonify({'error': 'Failed to update game'}), 500
            
    except Exception as e:
        logger.error(f"Error updating game: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ============ CREDITS SYSTEM API ENDPOINTS ============

@app.route('/api/user-credits', methods=['GET'])
def api_get_user_credits():
    """Get current user's credits"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        if not supabase_manager.is_connected():
            return jsonify({'error': 'Database not available'}), 500
        
        credits = supabase_manager.get_user_credits(str(session['user_id']))
        return jsonify({
            'success': True,
            'credits': credits
        })
        
    except Exception as e:
        logger.error(f"Error getting user credits: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Check Supabase connection
    if supabase_manager.is_connected():
        logger.info("✅ Supabase connected")
    else:
        logger.warning("⚠️  Supabase not connected. Check .env settings")
    
    port = app.config.get('PORT', 5000)
    app.run(debug=True, host='0.0.0.0', port=port)