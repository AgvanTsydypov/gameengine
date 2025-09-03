from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import os
import logging
from config import config
from supabase_client import supabase_manager
from stripe_client import stripe_manager

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load configuration
config_name = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

# User management functions via Supabase
def create_user(email, password):
    """Creates a new user in Supabase Auth"""
    if not supabase_manager.is_connected():
        logger.error("Supabase not connected for user creation")
        return None
    
    try:
        logger.info(f"Creating user: email={email}")
        
        # Create user in auth.users with email and password only
        auth_response = supabase_manager.client.auth.sign_up({
            "email": email,
            "password": password
        })
        
        logger.info(f"Auth response: {auth_response}")
        
        if auth_response.user:
            logger.info(f"User {email} successfully created in auth.users with ID: {auth_response.user.id}")
            
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
        
        auth_response = supabase_manager.client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        logger.info(f"Auth response: {auth_response}")
        
        if auth_response.user:
            logger.info(f"Successful authentication for {email}")
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
    return render_template('index.html', authenticated=authenticated)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if password != confirm_password:
            error_msg = 'Passwords do not match!'
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
    # Sign out from Supabase Auth
    if supabase_manager.is_connected():
        try:
            supabase_manager.client.auth.sign_out()
        except Exception as e:
            logger.error(f"Supabase Auth logout error: {e}")
    
    # Clear Flask session
    session.clear()
    flash('Successfully logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/games')
def games():
    """Trending games page - accessible without login"""
    # Mock games data
    mock_games = [
        {
            'id': 1,
            'title': 'PIXEL ODYSSEY',
            'category': 'ARCADE',
            'plays': '3.4K',
            'rating': 4.8,
            'description': 'An epic pixel adventure through space and time'
        },
        {
            'id': 2,
            'title': 'COSMIC INVADERS',
            'category': 'SHOOTER',
            'plays': '5.1K',
            'rating': 4.7,
            'description': 'Defend Earth from alien invaders in this retro shooter'
        },
        {
            'id': 3,
            'title': 'NEON QUEST',
            'category': 'ADVENTURE',
            'plays': '2.0K',
            'rating': 4.6,
            'description': 'Navigate through neon-lit cyberpunk worlds'
        },
        {
            'id': 4,
            'title': 'RETRO RACER',
            'category': 'RACING',
            'plays': '4.2K',
            'rating': 4.5,
            'description': 'High-speed pixel racing action'
        },
        {
            'id': 5,
            'title': 'STARSHIP COMMANDER',
            'category': 'STRATEGY',
            'plays': '1.8K',
            'rating': 4.9,
            'description': 'Command your fleet in epic space battles'
        },
        {
            'id': 6,
            'title': 'PIXEL PLATFORMER',
            'category': 'PLATFORM',
            'plays': '3.7K',
            'rating': 4.4,
            'description': 'Classic platforming with modern pixel art'
        }
    ]
    
    authenticated = 'user_id' in session
    return render_template('games.html', games=mock_games, authenticated=authenticated)

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
        
        if not supabase_manager.is_connected():
            return jsonify({'error': 'Storage service not available'}), 500
        
        # Save file to Supabase storage and create user_data record
        result = supabase_manager.save_user_file(
            user_id=str(session['user_id']),
            file_content=file_content,
            filename=game_file.filename,
            content_type='text/html'
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

@app.route('/play/<int:game_id>')
def play_game(game_id):
    """Play a specific game - mock for now"""
    # Mock game data
    mock_games = {
        1: {'title': 'PIXEL ODYSSEY', 'category': 'ARCADE'},
        2: {'title': 'COSMIC INVADERS', 'category': 'SHOOTER'},
        3: {'title': 'NEON QUEST', 'category': 'ADVENTURE'},
        4: {'title': 'RETRO RACER', 'category': 'RACING'},
        5: {'title': 'STARSHIP COMMANDER', 'category': 'STRATEGY'},
        6: {'title': 'PIXEL PLATFORMER', 'category': 'PLATFORM'}
    }
    
    game = mock_games.get(game_id)
    if not game:
        flash('Game not found.', 'error')
        return redirect(url_for('games'))
    
    authenticated = 'user_id' in session
    return render_template('play_game.html', game=game, game_id=game_id, authenticated=authenticated)

@app.route('/play-uploaded/<game_id>')
def play_uploaded_game(game_id):
    """Play a user's uploaded HTML game"""
    if 'user_id' not in session:
        flash('Please log in to play games.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Get the specific game data
        user_games = supabase_manager.get_user_data(str(session['user_id']))
        game = next((g for g in user_games if g.get('id') == game_id and g.get('data_type') == 'html_game'), None)
        
        if not game:
            flash('Game not found.', 'error')
            return redirect(url_for('my_games'))
        
        authenticated = 'user_id' in session
        return render_template('play_uploaded_game.html', game=game, authenticated=authenticated)
        
    except Exception as e:
        logger.error(f"Error loading uploaded game: {e}")
        flash('Error loading game. Please try again.', 'error')
        return redirect(url_for('my_games'))

@app.route('/game-content/<game_id>')
def get_game_content(game_id):
    """Serve the HTML content of a game directly"""
    if 'user_id' not in session:
        return "Authentication required", 401
    
    try:
        # Get the specific game data
        user_games = supabase_manager.get_user_data(str(session['user_id']))
        game = next((g for g in user_games if g.get('id') == game_id and g.get('data_type') == 'html_game'), None)
        
        if not game:
            return "Game not found", 404
        
        # Fetch the HTML content from the storage URL
        import requests
        try:
            response = requests.get(game['data_content'], timeout=10)
            if response.status_code == 200:
                # Return the HTML content with proper headers
                return response.text, 200, {
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

if __name__ == '__main__':
    # Check Supabase connection
    if supabase_manager.is_connected():
        logger.info("✅ Supabase connected")
    else:
        logger.warning("⚠️  Supabase not connected. Check .env settings")
    
    port = app.config.get('PORT', 5000)
    app.run(debug=True, host='0.0.0.0', port=port)