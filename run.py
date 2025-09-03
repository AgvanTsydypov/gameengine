#!/usr/bin/env python3
"""
Скрипт для запуска Flask приложения
"""
import os
import sys
from app import app, db

def create_tables():
    """Создает таблицы в базе данных"""
    with app.app_context():
        try:
            db.create_all()
            print("✅ Таблицы базы данных созданы успешно")
        except Exception as e:
            print(f"❌ Ошибка при создании таблиц: {e}")
            sys.exit(1)

def check_environment():
    """Проверяет настройки окружения"""
    print("🔍 Проверка настроек окружения...")
    
    # Проверяем основные переменные
    required_vars = ['SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        print("💡 Создайте файл .env на основе .env.example")
    else:
        print("✅ Основные переменные окружения настроены")
    
    # Проверяем Supabase
    if os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_KEY'):
        print("✅ Supabase настроен")
    else:
        print("⚠️  Supabase не настроен (опционально)")
    
    # Проверяем Stripe
    if os.getenv('STRIPE_SECRET_KEY') and os.getenv('STRIPE_PUBLISHABLE_KEY'):
        print("✅ Stripe настроен")
    else:
        print("⚠️  Stripe не настроен (опционально)")

def main():
    """Основная функция запуска"""
    print("🚀 Запуск Flask приложения...")
    print("=" * 50)
    
    # Проверяем окружение
    check_environment()
    print()
    
    # Создаем таблицы
    print("📊 Создание таблиц базы данных...")
    create_tables()
    print()
    
    # Запускаем приложение
    port = app.config.get('PORT', 5000)
    print(f"🌐 Приложение доступно по адресу: http://localhost:{port}")
    print("📝 Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    try:
        port = app.config.get('PORT', 5000)
        app.run(
            debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true',
            host='0.0.0.0',
            port=port
        )
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено")
    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
