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
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Получает текущего аутентифицированного пользователя
        
        Returns:
            Словарь с данными пользователя или None
        """
        if not self.is_connected():
            return None
        
        try:
            user = self.client.auth.get_user()
            return user.user if user else None
        except Exception as e:
            logger.error(f"Ошибка при получении текущего пользователя: {e}")
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
