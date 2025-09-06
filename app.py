from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import os
import logging
import json
import tempfile
from config import config
from supabase_client import supabase_manager
from stripe_client import stripe_manager
from html_preview_generator import HTMLPreviewGenerator
import openai

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

def get_default_model():
    """Get the default OpenAI model"""
    return "gpt-5"

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

def generate_game_thumbnail(html_content: str, game_title: str) -> str:
    """
    Generate a thumbnail for a game using the HTML preview generator
    
    Args:
        html_content: The HTML content of the game
        game_title: The title of the game
        
    Returns:
        Path to the generated thumbnail file, or None if failed
    """
    try:
        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(html_content)
            temp_html_path = temp_file.name
        
        # Generate thumbnail using HTMLPreviewGenerator
        generator = HTMLPreviewGenerator(headless=True, window_size=(800, 600))
        
        try:
            # Generate the thumbnail
            thumbnail_path = generator.generate_preview(
                html_file_path=temp_html_path,
                wait_time=5  # Wait longer for games to load
            )
            
            if thumbnail_path and os.path.exists(thumbnail_path):
                logger.info(f"Thumbnail generated successfully: {thumbnail_path}")
                return thumbnail_path
            else:
                logger.error("Failed to generate thumbnail")
                return None
                
        finally:
            generator.close()
            
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        return None
    finally:
        # Clean up temporary HTML file
        try:
            if 'temp_html_path' in locals() and os.path.exists(temp_html_path):
                os.unlink(temp_html_path)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file: {e}")

# Game generation system instructions
SYSTEM_INSTRUCTIONS_ONE_CALL = """
You are a senior front-end engineer and compact game designer.
From a free-form idea, produce:
- a SINGLE-FILE HTML game (inline CSS + vanilla JS only).

HARD CONSTRAINTS
- One HTML file only (no external assets, no web requests, no CDNs, no fonts).
- Mobile-first, accessible (focus-visible, high contrast, large tap target, respects prefers-reduced-motion).
- Must run offline in a modern browser (Chrome/Safari/Firefox).
- No console errors; concise JS; include a tiny inline help/about section.
- If you use persistence, use localStorage safely and offer a Reset.

RETURN ONLY strict JSON (no markdown) of shape:
{
  "title": str,
  "html": "<!doctype html>... full self-contained document ..."
}
"""

def build_user_message(user_prompt: str) -> str:
    """Build user message for game generation"""
    return (
        "Create a complete, playable browser game from this idea. "
        "Choose the most fitting genre/mechanics based on the prompt. "
        "Keep it self-contained (inline CSS/JS) and accessible. "
        "Return STRICT JSON as per schema.\n\n"
        f"USER_IDEA:\n{user_prompt}"
    )

def generate_game_with_ai(user_prompt: str):
    """Generate a game using OpenAI API"""
    if not client:
        logger.error("OpenAI client not initialized. Please check OPENAI_API_KEY.")
        return None
        
    try:
        logger.info(f"Generating game with prompt: {user_prompt[:100]}...")
        
        response = client.chat.completions.create(
            model=get_default_model(),
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS_ONE_CALL},
                {"role": "user", "content": build_user_message(user_prompt)},
            ]
        )
        
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

def refine_game_with_ai(instruction: str, current_html: str):
    """Refine existing game using OpenAI API"""
    if not client:
        logger.error("OpenAI client not initialized. Please check OPENAI_API_KEY.")
        return None
        
    try:
        logger.info(f"Refining game with instruction: {instruction[:100]}...")
        
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

        response = client.chat.completions.create(
            model=get_default_model(),
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": USER},
            ]
        )
        
        new_html = (response.choices[0].message.content or "").strip()
        logger.info(f"Game refinement completed, HTML length: {len(new_html)}")
        
        if new_html and new_html.startswith("<!"):
            # Fix encoding issues in the refined HTML content
            new_html = fix_text_encoding(new_html)
            return new_html
        else:
            logger.error("Invalid HTML returned from refinement")
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
            # Get top 3 trending games ordered by likes
            uploaded_games_raw = supabase_manager.get_games_with_stats(limit=3, order_by='likes_count')
            
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
                    'thumbnail_url': game.get('thumbnail_url')
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
    
    try:
        if supabase_manager.is_connected():
            # Get games with statistics (likes, plays) ordered by likes count (trending)
            uploaded_games_raw = supabase_manager.get_games_with_stats(order_by='likes_count')
            
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
                    'thumbnail_url': game.get('thumbnail_url')
                })
    except Exception as e:
        logger.error(f"Error fetching uploaded games: {e}")
    
    authenticated = 'user_id' in session
    return render_template('games.html', games=uploaded_games, authenticated=authenticated)

@app.route('/create-game')
def create_game():
    """Create game page - requires authentication"""
    if 'user_id' not in session:
        flash('Please log in to create a game.', 'error')
        return redirect(url_for('index'))
    
    authenticated = 'user_id' in session
    return render_template('create_game.html', authenticated=authenticated)

@app.route('/upload-game', methods=['POST'])
def upload_game():
    """Handle HTML game file upload to Supabase storage"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        game_file = request.files.get('game_file')
        
        # Validate input
        if not title:
            return jsonify({'error': 'Game title is required'}), 400
        
        if not description:
            return jsonify({'error': 'Game description is required'}), 400
        
        if not game_file or game_file.filename == '':
            return jsonify({'error': 'HTML file is required'}), 400
        
        # Validate file type
        if not (game_file.filename.lower().endswith('.html') or game_file.filename.lower().endswith('.htm')):
            return jsonify({'error': 'Only HTML files are allowed'}), 400
        
        # Validate file size (16MB limit)
        if len(game_file.read()) > 16 * 1024 * 1024:
            return jsonify({'error': 'File size must be less than 16MB'}), 400
        
        # Reset file pointer
        game_file.seek(0)
        
        # Read file content
        file_content = game_file.read()
        html_content = file_content.decode('utf-8')
        
        if not supabase_manager.is_connected():
            return jsonify({'error': 'Storage service not available'}), 500
        
        # Generate thumbnail for the game
        logger.info(f"Generating thumbnail for game: {title}")
        thumbnail_path = generate_game_thumbnail(html_content, title)
        
        # Save file to Supabase storage and create user_data record
        result = supabase_manager.save_user_file(
            user_id=str(session['user_id']),
            file_content=file_content,
            filename=game_file.filename,
            content_type='text/html',
            title=title,
            description=description,
            thumbnail_path=thumbnail_path
        )
        
        if result:
            logger.info(f"Game file uploaded successfully for user {session['user_id']}")
            return jsonify({
                'success': True, 
                'message': 'Game uploaded successfully',
                'file_id': result.get('id')
            })
        else:
            return jsonify({'error': 'Failed to upload game file'}), 500
            
    except Exception as e:
        logger.error(f"Error uploading game file: {e}")
        return jsonify({'error': 'Upload failed. Please try again.'}), 500

@app.route('/my-games')
def my_games():
    """View user's uploaded games - requires authentication"""
    if 'user_id' not in session:
        flash('Please log in to view your games.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Get user's uploaded games from Supabase
        user_games = supabase_manager.get_user_data(str(session['user_id']))
        
        # Filter for HTML games
        html_games = [game for game in user_games if game.get('data_type') == 'html_game']
        
        authenticated = 'user_id' in session
        return render_template('my_games.html', games=html_games, authenticated=authenticated)
        
    except Exception as e:
        logger.error(f"Error fetching user games: {e}")
        flash('Error loading your games. Please try again.', 'error')
        return redirect(url_for('index'))


@app.route('/play-uploaded/<game_id>')
def play_uploaded_game(game_id):
    """Play any user's uploaded HTML game - accessible to all users"""
    try:
        # Get the specific game data by ID (from any user)
        game = supabase_manager.get_game_by_id(str(game_id))
        
        if not game:
            flash('Game not found.', 'error')
            return redirect(url_for('games'))
        
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

# Stripe integration stub
@app.route('/payment')
def payment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if stripe_manager.is_configured():
        # TODO: Implement full Stripe integration
        flash('Stripe integration configured, but payment functionality is in development', 'info')
    else:
        flash('Stripe not configured. Payment feature will be available after setup', 'warning')
    
    return redirect(url_for('index'))

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
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({'error': 'Game prompt is required'}), 400
        
        # Generate game with AI
        game_data = generate_game_with_ai(prompt)
        
        if game_data:
            return jsonify({
                'success': True,
                'title': game_data['title'],
                'html': game_data['html']
            })
        else:
            return jsonify({'error': 'Failed to generate game. Please try again.'}), 500
            
    except Exception as e:
        logger.error(f"Error in game generation API: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/refine-game', methods=['POST'])
def api_refine_game():
    """Refine an existing game using AI"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        instruction = data.get('instruction', '').strip()
        current_html = data.get('current_html', '').strip()
        
        if not instruction:
            return jsonify({'error': 'Refinement instruction is required'}), 400
        
        if not current_html:
            return jsonify({'error': 'Current game HTML is required'}), 400
        
        # Refine game with AI
        refined_html = refine_game_with_ai(instruction, current_html)
        
        if refined_html:
            return jsonify({
                'success': True,
                'html': refined_html
            })
        else:
            return jsonify({'error': 'Failed to refine game. Please try again.'}), 500
            
    except Exception as e:
        logger.error(f"Error in game refinement API: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/publish-game', methods=['POST'])
def api_publish_game():
    """Publish AI-generated game to community"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        html_content = data.get('html_content', '').strip()
        
        if not title:
            return jsonify({'error': 'Game title is required'}), 400
        
        if not description:
            return jsonify({'error': 'Game description is required'}), 400
        
        if not html_content:
            return jsonify({'error': 'Game HTML content is required'}), 400
        
        if not supabase_manager.is_connected():
            return jsonify({'error': 'Storage service not available'}), 500
        
        # Generate thumbnail for the AI-generated game
        logger.info(f"Generating thumbnail for AI-generated game: {title}")
        thumbnail_path = generate_game_thumbnail(html_content, title)
        
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

if __name__ == '__main__':
    # Check Supabase connection
    if supabase_manager.is_connected():
        logger.info("✅ Supabase connected")
    else:
        logger.warning("⚠️  Supabase not connected. Check .env settings")
    
    port = app.config.get('PORT', 5000)
    app.run(debug=True, host='0.0.0.0', port=port)