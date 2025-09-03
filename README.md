# Клиент-серверное приложение на Flask

Веб-приложение для регистрации пользователей, хранения данных и интеграции с облачными сервисами.

## Возможности

- ✅ Регистрация и авторизация пользователей
- ✅ Хранение пользовательских данных только в Supabase (облачная БД)
- ✅ Современный веб-интерфейс с Bootstrap 5
- ✅ Полная интеграция с Supabase (без локальной БД)
- 🔄 Интеграция со Stripe (платежи) - в разработке
- ✅ Адаптивный дизайн
- ✅ Безопасное хранение паролей

## Технологии

- **Backend**: Flask, Werkzeug
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **База данных**: Supabase (облачная PostgreSQL)
- **Платежи**: Stripe (планируется)
- **Безопасность**: bcrypt для хеширования паролей

## Установка и запуск

### 1. Клонирование и настройка окружения

```bash
# Перейдите в папку проекта
cd /Users/agmac/Desktop/app

# Создайте виртуальное окружение (если еще не создано)
python3 -m venv venv

# Активируйте виртуальное окружение
source venv/bin/activate  # На macOS/Linux
# или
venv\Scripts\activate     # На Windows

# Установите зависимости
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта на основе `.env.example`:

```bash
cp .env.example .env
```

Отредактируйте файл `.env` и заполните необходимые переменные:

```env
# Основные настройки
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# База данных (не используется - только Supabase)
# DATABASE_URL=sqlite:///app.db

# Supabase (получите на https://supabase.com)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Stripe (получите на https://stripe.com)
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 3. Настройка Supabase

1. Создайте проект на [supabase.com](https://supabase.com)
2. В SQL Editor выполните следующие команды для создания таблиц:

```sql
-- Таблица пользователей (профили)
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица данных пользователей
CREATE TABLE user_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    data_type VARCHAR(50) NOT NULL,
    data_content TEXT NOT NULL,
    filename VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для оптимизации
CREATE INDEX idx_user_data_user_id ON user_data(user_id);
CREATE INDEX idx_user_data_created_at ON user_data(created_at DESC);
```

**Важно**: Полную схему с триггерами и политиками безопасности смотрите в файле `supabase_schema.sql`

3. Включите Row Level Security (RLS) для безопасности:

```sql
-- Включаем RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_data ENABLE ROW LEVEL SECURITY;

-- Политики для users
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Политики для user_data
CREATE POLICY "Users can view own data" ON user_data
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own data" ON user_data
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own data" ON user_data
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own data" ON user_data
    FOR DELETE USING (auth.uid() = user_id);
```

### 4. Запуск приложения

```bash
# Активируйте виртуальное окружение
source venv/bin/activate

# Запустите приложение
python app.py
```

Приложение будет доступно по адресу: http://localhost:5000

## Структура проекта

```
app/
├── app.py                 # Основное Flask приложение
├── config.py             # Конфигурация приложения
├── supabase_client.py    # Интеграция с Supabase
├── stripe_client.py      # Интеграция со Stripe
├── requirements.txt      # Зависимости Python
├── README.md            # Документация
├── templates/           # HTML шаблоны
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   └── dashboard.html
└── static/              # Статические файлы
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

## Использование

### Регистрация пользователя

1. Перейдите на главную страницу
2. Нажмите "Регистрация"
3. Заполните форму (имя пользователя, email, пароль)
4. Нажмите "Зарегистрироваться"

### Вход в систему

1. Нажмите "Войти"
2. Введите имя пользователя и пароль
3. Нажмите "Войти"

### Работа с данными

1. После входа вы попадете в панель управления
2. В левой панели можете добавлять новые данные:
   - Выберите тип данных (текст, файл, JSON, заметка)
   - Укажите имя файла (опционально)
   - Введите содержимое
   - Нажмите "Сохранить"
3. В правой панели отображаются все ваши данные
4. Можете просматривать и удалять данные

## API Endpoints

- `GET /` - Главная страница
- `GET /register` - Страница регистрации
- `POST /register` - Обработка регистрации
- `GET /login` - Страница входа
- `POST /login` - Обработка входа
- `GET /logout` - Выход из системы
- `GET /dashboard` - Панель управления
- `POST /save_data` - Сохранение данных
- `POST /delete_data/<id>` - Удаление данных
- `GET /payment` - Страница оплаты (заглушка)

## Безопасность

- Пароли хешируются с помощью bcrypt
- Используются сессии для аутентификации
- Настроена защита от CSRF атак
- Данные пользователей изолированы через RLS в Supabase

## Разработка

### Добавление новых функций

1. Создайте новый маршрут в `app.py`
2. Добавьте соответствующий HTML шаблон в `templates/`
3. Обновите навигацию в `base.html`
4. Добавьте стили в `static/css/style.css` при необходимости

### Тестирование

```bash
# Запуск тестов (когда будут добавлены)
python -m pytest
```

## Развертывание

### Локальное развертывание

```bash
# Установите gunicorn для продакшена
pip install gunicorn

# Запустите с gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Облачное развертывание

Приложение готово для развертывания на:
- Heroku
- Railway
- DigitalOcean App Platform
- AWS Elastic Beanstalk

## Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте логи приложения
2. Убедитесь, что все переменные окружения настроены
3. Проверьте подключение к Supabase
4. Создайте issue в репозитории

## Лицензия

MIT License

## Планы развития

- [ ] Полная интеграция со Stripe
- [ ] API для мобильных приложений
- [ ] Система уведомлений
- [ ] Экспорт/импорт данных
- [ ] Двухфакторная аутентификация
- [ ] Административная панель
