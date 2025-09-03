# Настройка Supabase

## 🚀 Пошаговая инструкция

### 1. Создание проекта Supabase

1. Перейдите на [supabase.com](https://supabase.com)
2. Нажмите "Start your project"
3. Войдите в аккаунт или создайте новый
4. Нажмите "New project"
5. Заполните данные:
   - **Name**: `my-flask-app` (или любое другое имя)
   - **Database Password**: создайте надежный пароль
   - **Region**: выберите ближайший регион
6. Нажмите "Create new project"

### 2. Получение ключей API

1. В панели управления проекта перейдите в **Settings** → **API**
2. Скопируйте следующие значения:
   - **Project URL** (например: `https://abcdefgh.supabase.co`)
   - **anon public** ключ
   - **service_role** ключ (секретный!)

### 3. Настройка переменных окружения

Создайте или обновите файл `.env`:

```env
# Supabase настройки
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

### 4. Создание таблиц в базе данных

1. В панели Supabase перейдите в **SQL Editor**
2. Создайте новый запрос
3. Скопируйте и выполните код из файла `supabase_schema.sql`

Или выполните команды по частям:

```sql
-- 1. Создание таблицы пользователей
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Создание таблицы данных пользователей
CREATE TABLE user_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    data_type VARCHAR(50) NOT NULL,
    data_content TEXT NOT NULL,
    filename VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Создание индексов
CREATE INDEX idx_user_data_user_id ON user_data(user_id);
CREATE INDEX idx_user_data_created_at ON user_data(created_at DESC);

-- 4. Включение RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_data ENABLE ROW LEVEL SECURITY;
```

### 5. Настройка политик безопасности (RLS)

```sql
-- Политики для users
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON users
    FOR INSERT WITH CHECK (auth.uid() = id);

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

### 6. Создание триггеров

```sql
-- Функция для автоматического создания профиля
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, username, email)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'username', NEW.email),
        NEW.email
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Триггер для автоматического создания профиля
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- Функция для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для автоматического обновления updated_at
CREATE TRIGGER update_user_data_updated_at
    BEFORE UPDATE ON user_data
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();
```

### 7. Настройка аутентификации

1. В панели Supabase перейдите в **Authentication** → **Settings**
2. В разделе **Site URL** добавьте: `http://localhost:5000`
3. В разделе **Redirect URLs** добавьте: `http://localhost:5000/**`
4. Сохраните изменения

### 8. Проверка настройки

Запустите приложение:

```bash
source venv/bin/activate
python run.py
```

Вы должны увидеть:
```
✅ Подключение к Supabase установлено
```

## 🔧 Устранение проблем

### Ошибка "Could not find the 'password_hash' column"

**Решение**: Убедитесь, что в таблице `users` нет колонки `password_hash`. Пароли хранятся в `auth.users`.

### Ошибка "Row Level Security"

**Решение**: Убедитесь, что RLS включен и политики созданы правильно.

### Ошибка подключения

**Решение**: Проверьте правильность URL и ключей в файле `.env`.

## 📊 Структура данных

### Таблица `auth.users` (автоматическая)
- `id` - UUID пользователя
- `email` - Email пользователя
- `encrypted_password` - Зашифрованный пароль
- `raw_user_meta_data` - Метаданные (username)

### Таблица `public.users` (профили)
- `id` - UUID (ссылка на auth.users.id)
- `username` - Имя пользователя
- `email` - Email пользователя
- `created_at` - Дата создания

### Таблица `public.user_data` (данные пользователей)
- `id` - UUID записи
- `user_id` - UUID пользователя
- `data_type` - Тип данных
- `data_content` - Содержимое данных
- `filename` - Имя файла
- `created_at` - Дата создания
- `updated_at` - Дата обновления

## ✅ Готово!

После выполнения всех шагов ваше приложение будет полностью интегрировано с Supabase!
