-- Схема базы данных для Supabase
-- Выполните эти команды в SQL Editor в Supabase
-- Используем только auth.users (встроенная аутентификация Supabase)
-- Пользователи регистрируются и входят только по email + password

-- Удаляем таблицу profiles если она существует (больше не нужна)
DROP TABLE IF EXISTS profiles CASCADE;

-- 1. Создание таблицы данных пользователей
CREATE TABLE IF NOT EXISTS user_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    data_type VARCHAR(50) NOT NULL,
    data_content TEXT NOT NULL,
    filename VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_user_data_user_id ON user_data(user_id);
CREATE INDEX IF NOT EXISTS idx_user_data_created_at ON user_data(created_at DESC);

-- 3. Включение Row Level Security (RLS)
ALTER TABLE user_data ENABLE ROW LEVEL SECURITY;

-- 4. Политики безопасности для таблицы user_data
DROP POLICY IF EXISTS "Users can view own data" ON user_data;
CREATE POLICY "Users can view own data" ON user_data
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own data" ON user_data;
CREATE POLICY "Users can insert own data" ON user_data
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own data" ON user_data;
CREATE POLICY "Users can update own data" ON user_data
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own data" ON user_data;
CREATE POLICY "Users can delete own data" ON user_data
    FOR DELETE USING (auth.uid() = user_id);

-- 5. Функция для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 6. Триггер для автоматического обновления updated_at
DROP TRIGGER IF EXISTS update_user_data_updated_at ON user_data;
CREATE TRIGGER update_user_data_updated_at
    BEFORE UPDATE ON user_data
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();
