from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import logging
from config import config
from supabase_client import supabase_manager
from stripe_client import stripe_manager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Загружаем конфигурацию
config_name = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

# Инициализация расширений
db = SQLAlchemy(app)

# Модели базы данных
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data_type = db.Column(db.String(50), nullable=False)  # 'file', 'text', 'json', etc.
    data_content = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('user_data', lazy=True))

# Маршруты
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Валидация
        if password != confirm_password:
            flash('Пароли не совпадают!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует!', 'error')
            return render_template('register.html')
        
        # Создание нового пользователя
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Регистрация прошла успешно! Теперь вы можете войти в систему.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Произошла ошибка при регистрации. Попробуйте еще раз.', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    user_data = UserData.query.filter_by(user_id=user.id).order_by(UserData.created_at.desc()).all()
    
    return render_template('dashboard.html', user=user, user_data=user_data)

@app.route('/save_data', methods=['POST'])
def save_data():
    if 'user_id' not in session:
        return jsonify({'error': 'Необходима авторизация'}), 401
    
    data_type = request.form.get('data_type', 'text')
    data_content = request.form.get('data_content', '')
    filename = request.form.get('filename', '')
    
    if not data_content:
        return jsonify({'error': 'Содержимое не может быть пустым'}), 400
    
    try:
        # Сохраняем в локальную базу данных
        user_data = UserData(
            user_id=session['user_id'],
            data_type=data_type,
            data_content=data_content,
            filename=filename
        )
        
        db.session.add(user_data)
        db.session.commit()
        
        # Также сохраняем в Supabase, если подключен
        if supabase_manager.is_connected():
            supabase_result = supabase_manager.save_user_data(
                user_id=str(session['user_id']),
                data_type=data_type,
                data_content=data_content,
                filename=filename
            )
            if supabase_result:
                logger.info("Данные также сохранены в Supabase")
        
        return jsonify({'success': True, 'message': 'Данные сохранены успешно'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при сохранении данных: {e}")
        return jsonify({'error': 'Ошибка при сохранении данных'}), 500

@app.route('/delete_data/<int:data_id>', methods=['POST'])
def delete_data(data_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Необходима авторизация'}), 401
    
    user_data = UserData.query.filter_by(id=data_id, user_id=session['user_id']).first()
    
    if not user_data:
        return jsonify({'error': 'Данные не найдены'}), 404
    
    try:
        # Удаляем из локальной базы данных
        db.session.delete(user_data)
        db.session.commit()
        
        # Также удаляем из Supabase, если подключен
        if supabase_manager.is_connected():
            supabase_result = supabase_manager.delete_user_data(
                data_id=str(data_id),
                user_id=str(session['user_id'])
            )
            if supabase_result:
                logger.info("Данные также удалены из Supabase")
        
        return jsonify({'success': True, 'message': 'Данные удалены успешно'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении данных: {e}")
        return jsonify({'error': 'Ошибка при удалении данных'}), 500

# Заглушка для Stripe интеграции
@app.route('/payment')
def payment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if stripe_manager.is_configured():
        # TODO: Реализовать полную интеграцию со Stripe
        flash('Интеграция со Stripe настроена, но функционал оплаты еще в разработке', 'info')
    else:
        flash('Stripe не настроен. Функция оплаты будет доступна после настройки', 'warning')
    
    return redirect(url_for('dashboard'))

@app.route('/create_payment_intent', methods=['POST'])
def create_payment_intent():
    """Создает намерение платежа через Stripe"""
    if 'user_id' not in session:
        return jsonify({'error': 'Необходима авторизация'}), 401
    
    if not stripe_manager.is_configured():
        return jsonify({'error': 'Stripe не настроен'}), 400
    
    try:
        amount = int(request.json.get('amount', 1000))  # По умолчанию $10.00
        currency = request.json.get('currency', 'usd')
        
        user = User.query.get(session['user_id'])
        
        # Создаем или получаем клиента Stripe
        customer = stripe_manager.get_customer_by_email(user.email)
        if not customer:
            customer = stripe_manager.create_customer(user.email, user.username)
        
        if customer:
            # Создаем намерение платежа
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
        
        return jsonify({'error': 'Не удалось создать намерение платежа'}), 500
        
    except Exception as e:
        logger.error(f"Ошибка при создании намерения платежа: {e}")
        return jsonify({'error': 'Ошибка при создании платежа'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = app.config.get('PORT', 5000)
    app.run(debug=True, host='0.0.0.0', port=port)
