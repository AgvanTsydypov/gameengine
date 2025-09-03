from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
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

# Функции для работы с пользователями через Supabase
def create_user(email, password):
    """Создает нового пользователя в Supabase Auth"""
    if not supabase_manager.is_connected():
        logger.error("Supabase не подключен для создания пользователя")
        return None
    
    try:
        logger.info(f"Создание пользователя: email={email}")
        
        # Создаем пользователя в auth.users только с email и паролем
        auth_response = supabase_manager.client.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if auth_response.user:
            logger.info(f"Пользователь {email} успешно создан в auth.users с ID: {auth_response.user.id}")
            
            return {
                'user': auth_response.user,
                'user_id': auth_response.user.id
            }
        
        logger.error("Не удалось создать пользователя в auth.users")
        return None
        
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя: {e}")
        return None

def authenticate_user(email, password):
    """Аутентифицирует пользователя через Supabase Auth"""
    if not supabase_manager.is_connected():
        logger.error("Supabase не подключен")
        return None
    
    try:
        logger.info(f"Попытка аутентификации пользователя: {email}")
        
        auth_response = supabase_manager.client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if auth_response.user:
            logger.info(f"Успешная аутентификация для {email}")
            return {
                'user': auth_response.user,
                'email': auth_response.user.email
            }
        
        logger.warning(f"Неверный пароль для {email}")
        return None
        
    except Exception as e:
        logger.error(f"Ошибка при аутентификации {email}: {e}")
        return None

# Маршруты
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Валидация
        if password != confirm_password:
            flash('Пароли не совпадают!', 'error')
            return render_template('register.html')
        
        # Создание нового пользователя в Supabase
        try:
            result = create_user(email, password)
            if result:
                flash('Регистрация прошла успешно! Теперь вы можете войти в систему.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Произошла ошибка при регистрации. Возможно, пользователь с таким email уже существует.', 'error')
        except Exception as e:
            logger.error(f"Ошибка при регистрации: {e}")
            flash('Произошла ошибка при регистрации. Попробуйте еще раз.', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Аутентифицируем пользователя
        auth_result = authenticate_user(email, password)
        
        if auth_result:
            session['user_id'] = auth_result['user'].id
            session['email'] = auth_result['user'].email
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный email или пароль!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Выходим из Supabase Auth
    if supabase_manager.is_connected():
        try:
            supabase_manager.client.auth.sign_out()
        except Exception as e:
            logger.error(f"Ошибка при выходе из Supabase Auth: {e}")
    
    # Очищаем сессию Flask
    session.clear()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Получаем данные пользователя из Supabase
    user_data_list = supabase_manager.get_user_data(session['user_id'])
    
    # Создаем объект пользователя для шаблона
    user = {
        'id': session['user_id'],
        'email': session['email']
    }
    
    return render_template('dashboard.html', user=user, user_data=user_data_list)

@app.route('/save_data', methods=['POST'])
def save_data():
    if 'user_id' not in session:
        return jsonify({'error': 'Необходима авторизация'}), 401
    
    data_type = request.form.get('data_type', 'text')
    data_content = request.form.get('data_content', '')
    filename = request.form.get('filename', '')
    
    if not data_content:
        return jsonify({'error': 'Содержимое не может быть пустым'}), 400
    
    if not supabase_manager.is_connected():
        return jsonify({'error': 'Supabase не подключен. Проверьте настройки.'}), 500
    
    try:
        # Сохраняем только в Supabase
        result = supabase_manager.save_user_data(
            user_id=str(session['user_id']),
            data_type=data_type,
            data_content=data_content,
            filename=filename
        )
        
        if result:
            logger.info("Данные сохранены в Supabase")
            return jsonify({'success': True, 'message': 'Данные сохранены успешно'})
        else:
            return jsonify({'error': 'Ошибка при сохранении данных в Supabase'}), 500
            
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных: {e}")
        return jsonify({'error': 'Ошибка при сохранении данных'}), 500

@app.route('/delete_data/<data_id>', methods=['POST'])
def delete_data(data_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Необходима авторизация'}), 401
    
    if not supabase_manager.is_connected():
        return jsonify({'error': 'Supabase не подключен. Проверьте настройки.'}), 500
    
    try:
        # Удаляем только из Supabase
        result = supabase_manager.delete_user_data(
            data_id=str(data_id),
            user_id=str(session['user_id'])
        )
        
        if result:
            logger.info("Данные удалены из Supabase")
            return jsonify({'success': True, 'message': 'Данные удалены успешно'})
        else:
            return jsonify({'error': 'Данные не найдены или ошибка при удалении'}), 404
            
    except Exception as e:
        logger.error(f"Ошибка при удалении данных: {e}")
        return jsonify({'error': 'Ошибка при удалении данных'}), 500

# Заглушка для Stripe интеграции
@app.route('/payment')
def payment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
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
        
        # Получаем email из сессии
        user_email = session.get('email')
        if not user_email:
            return jsonify({'error': 'Email пользователя не найден в сессии'}), 400
        
        # Создаем или получаем клиента Stripe
        customer = stripe_manager.get_customer_by_email(user_email)
        if not customer:
            customer = stripe_manager.create_customer(user_email, user_email)
        
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
    # Проверяем подключение к Supabase
    if supabase_manager.is_connected():
        logger.info("✅ Supabase подключен")
    else:
        logger.warning("⚠️  Supabase не подключен. Проверьте настройки в .env")
    
    port = app.config.get('PORT', 5000)
    app.run(debug=True, host='0.0.0.0', port=port)
