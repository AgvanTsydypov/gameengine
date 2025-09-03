"""
Модуль для работы с Supabase
"""
import os
from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class SupabaseManager:
    """Класс для управления подключением к Supabase"""
    
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.client: Optional[Client] = None
        
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                logger.info("Supabase клиент успешно инициализирован")
            except Exception as e:
                logger.error(f"Ошибка при инициализации Supabase клиента: {e}")
        else:
            logger.warning("Supabase URL или ключ не настроены")
    
    def is_connected(self) -> bool:
        """Проверяет, подключен ли клиент к Supabase"""
        return self.client is not None
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Создает нового пользователя в Supabase
        
        Args:
            user_data: Словарь с данными пользователя
            
        Returns:
            Словарь с данными созданного пользователя или None при ошибке
        """
        if not self.is_connected():
            logger.error("Supabase клиент не подключен")
            return None
        
        try:
            # Создаем пользователя в auth.users
            auth_response = self.client.auth.sign_up({
                "email": user_data.get('email'),
                "password": user_data.get('password'),
                "options": {
                    "data": {
                        "username": user_data.get('username'),
                        "full_name": user_data.get('full_name', '')
                    }
                }
            })
            
            if auth_response.user:
                # Создаем профиль пользователя в public.users
                profile_data = {
                    "id": auth_response.user.id,
                    "username": user_data.get('username'),
                    "email": user_data.get('email'),
                    "created_at": "now()"
                }
                
                profile_response = self.client.table('users').insert(profile_data).execute()
                
                if profile_response.data:
                    logger.info(f"Пользователь {user_data.get('username')} успешно создан")
                    return {
                        'user': auth_response.user,
                        'profile': profile_response.data[0]
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Получает пользователя по email
        
        Args:
            email: Email пользователя
            
        Returns:
            Словарь с данными пользователя или None
        """
        if not self.is_connected():
            return None
        
        try:
            response = self.client.table('users').select('*').eq('email', email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя по email: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Получает пользователя по имени пользователя
        
        Args:
            username: Имя пользователя
            
        Returns:
            Словарь с данными пользователя или None
        """
        if not self.is_connected():
            return None
        
        try:
            response = self.client.table('users').select('*').eq('username', username).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя по username: {e}")
            return None
    
    def save_user_data(self, user_id: str, data_type: str, data_content: str, filename: str = None) -> Optional[Dict[str, Any]]:
        """
        Сохраняет данные пользователя в Supabase
        
        Args:
            user_id: ID пользователя
            data_type: Тип данных
            data_content: Содержимое данных
            filename: Имя файла (опционально)
            
        Returns:
            Словарь с данными сохраненной записи или None при ошибке
        """
        if not self.is_connected():
            return None
        
        try:
            data = {
                "user_id": user_id,
                "data_type": data_type,
                "data_content": data_content,
                "filename": filename,
                "created_at": "now()",
                "updated_at": "now()"
            }
            
            response = self.client.table('user_data').insert(data).execute()
            
            if response.data:
                logger.info(f"Данные пользователя {user_id} успешно сохранены")
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных пользователя: {e}")
            return None
    
    def get_user_data(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Получает все данные пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список словарей с данными пользователя
        """
        if not self.is_connected():
            return []
        
        try:
            response = self.client.table('user_data').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Ошибка при получении данных пользователя: {e}")
            return []
    
    def delete_user_data(self, data_id: str, user_id: str) -> bool:
        """
        Удаляет данные пользователя
        
        Args:
            data_id: ID записи данных
            user_id: ID пользователя
            
        Returns:
            True если удаление прошло успешно, False в противном случае
        """
        if not self.is_connected():
            return False
        
        try:
            response = self.client.table('user_data').delete().eq('id', data_id).eq('user_id', user_id).execute()
            logger.info(f"Данные {data_id} пользователя {user_id} успешно удалены")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении данных пользователя: {e}")
            return False
    
    def update_user_data(self, data_id: str, user_id: str, data_content: str, filename: str = None) -> Optional[Dict[str, Any]]:
        """
        Обновляет данные пользователя
        
        Args:
            data_id: ID записи данных
            user_id: ID пользователя
            data_content: Новое содержимое данных
            filename: Новое имя файла (опционально)
            
        Returns:
            Словарь с обновленными данными или None при ошибке
        """
        if not self.is_connected():
            return None
        
        try:
            update_data = {
                "data_content": data_content,
                "updated_at": "now()"
            }
            
            if filename:
                update_data["filename"] = filename
            
            response = self.client.table('user_data').update(update_data).eq('id', data_id).eq('user_id', user_id).execute()
            
            if response.data:
                logger.info(f"Данные {data_id} пользователя {user_id} успешно обновлены")
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении данных пользователя: {e}")
            return None

# Глобальный экземпляр менеджера Supabase
supabase_manager = SupabaseManager()
