import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Config:
    """Базовая конфигурация приложения"""
    
    # Основные настройки
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # База данных (удалено - используем только Supabase)
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Supabase настройки
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    
    # Stripe настройки
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    
    # OpenAI настройки
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # DeepSeek настройки
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    
    # Настройки безопасности
    BCRYPT_LOG_ROUNDS = int(os.getenv('BCRYPT_LOG_ROUNDS', 12))
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    
    # Увеличиваем время жизни сессии для лучшей совместимости с платежными redirects
    PERMANENT_SESSION_LIFETIME = int(os.getenv('SESSION_LIFETIME', 3600))  # 1 час
    
    # Настройки загрузки файлов
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'txt,pdf,png,jpg,jpeg,gif,doc,docx,xls,xlsx,json,xml,csv').split(','))
    
    # Настройки логирования
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    
    # Порт приложения
    PORT = int(os.getenv('PORT', 8888))
    
    # Базовый URL для редиректов (для email подтверждения)
    # Динамически определяется на основе FLASK_ENV
    @property
    def BASE_URL(self):
        flask_env = os.getenv('FLASK_ENV', 'development')
        
        # FLASK_ENV takes priority - if development, always use localhost
        if flask_env == 'development':
            return 'http://localhost:8888'
        elif flask_env == 'production':
            return 'https://glitchpeach.com'
        else:
            # Fallback: check BASE_URL environment variable
            base_url = os.getenv('BASE_URL', '')
            if base_url and base_url.strip():
                return base_url.strip()
            else:
                return 'http://localhost:8888'  # Default to development

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app_dev.db')

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    # BASE_URL наследуется от базового класса и динамически определяется
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/app_prod')

class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Словарь конфигураций
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
