#!/usr/bin/env python3
"""
Скрипт для установки зависимостей и настройки проекта
"""
import os
import sys
import subprocess
import shutil

def run_command(command, description):
    """Выполняет команду и выводит результат"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ошибка:")
        print(f"   {e.stderr}")
        return False

def check_python_version():
    """Проверяет версию Python"""
    print("🐍 Проверка версии Python...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Требуется Python 3.8+, текущая версия: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def create_virtual_environment():
    """Создает виртуальное окружение"""
    if os.path.exists('venv'):
        print("📁 Виртуальное окружение уже существует")
        return True
    
    return run_command('python3 -m venv venv', 'Создание виртуального окружения')

def install_dependencies():
    """Устанавливает зависимости"""
    # Определяем команду pip в зависимости от ОС
    if os.name == 'nt':  # Windows
        pip_cmd = 'venv\\Scripts\\pip'
    else:  # Unix/Linux/macOS
        pip_cmd = 'venv/bin/pip'
    
    # Обновляем pip
    if not run_command(f'{pip_cmd} install --upgrade pip', 'Обновление pip'):
        return False
    
    # Устанавливаем зависимости
    return run_command(f'{pip_cmd} install -r requirements.txt', 'Установка зависимостей')

def create_env_file():
    """Создает файл .env если его нет"""
    if os.path.exists('.env'):
        print("📄 Файл .env уже существует")
        return True
    
    if os.path.exists('.env.example'):
        try:
            shutil.copy('.env.example', '.env')
            print("✅ Файл .env создан на основе .env.example")
            print("⚠️  Не забудьте отредактировать .env и заполнить необходимые переменные")
            return True
        except Exception as e:
            print(f"❌ Ошибка при создании .env: {e}")
            return False
    else:
        print("⚠️  Файл .env.example не найден")
        return False

def create_directories():
    """Создает необходимые директории"""
    directories = ['uploads', 'logs', 'static/uploads']
    
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"📁 Создана директория: {directory}")
            except Exception as e:
                print(f"❌ Ошибка при создании директории {directory}: {e}")
                return False
    
    return True

def main():
    """Основная функция установки"""
    print("🚀 Установка и настройка Flask приложения")
    print("=" * 50)
    
    # Проверяем версию Python
    if not check_python_version():
        sys.exit(1)
    
    print()
    
    # Создаем виртуальное окружение
    if not create_virtual_environment():
        sys.exit(1)
    
    print()
    
    # Устанавливаем зависимости
    if not install_dependencies():
        sys.exit(1)
    
    print()
    
    # Создаем файл .env
    create_env_file()
    
    print()
    
    # Создаем необходимые директории
    if not create_directories():
        sys.exit(1)
    
    print()
    print("🎉 Установка завершена успешно!")
    print("=" * 50)
    print("📋 Следующие шаги:")
    print("1. Отредактируйте файл .env и заполните необходимые переменные")
    print("2. Настройте Supabase (опционально)")
    print("3. Настройте Stripe (опционально)")
    print("4. Запустите приложение: python run.py")
    print()
    print("💡 Для активации виртуального окружения:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("   source venv/bin/activate")

if __name__ == '__main__':
    main()
