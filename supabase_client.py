"""
Supabase Client Module
"""
import os
from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class SupabaseManager:
    """Class for managing Supabase connection"""
    
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.client: Optional[Client] = None
        
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                logger.info("Supabase client successfully initialized")
            except Exception as e:
                logger.error(f"Error initializing Supabase client: {e}")
        else:
            logger.warning("Supabase URL or key not configured")
    
    def is_connected(self) -> bool:
        """Checks if client is connected to Supabase"""
        return self.client is not None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Gets current authenticated user
        
        Returns:
            Dictionary with user data or None
        """
        if not self.is_connected():
            return None
        
        try:
            user = self.client.auth.get_user()
            return user.user if user else None
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None
    
    def save_user_data(self, user_id: str, data_type: str, data_content: str, filename: str = None) -> Optional[Dict[str, Any]]:
        """
        Saves user data to Supabase
        
        Args:
            user_id: User ID
            data_type: Data type
            data_content: Data content
            filename: File name (optional)
            
        Returns:
            Dictionary with saved record data or None on error
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
