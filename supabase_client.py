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
            
            # Use service role key for server-side operations to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                response = service_client.table('user_data').insert(data).execute()
            else:
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
            # Use service role key for server-side operations to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                response = service_client.table('user_data').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            else:
                response = self.client.table('user_data').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Ошибка при получении данных пользователя: {e}")
            return []
    
    def get_all_uploaded_games(self) -> List[Dict[str, Any]]:
        """
        Gets all uploaded HTML games from all users
        
        Returns:
            List of dictionaries with game data for all users
        """
        if not self.is_connected():
            return []
        
        try:
            # Use service role key for server-side operations to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                response = service_client.table('user_data').select('*').eq('data_type', 'html_game').order('created_at', desc=True).execute()
            else:
                response = self.client.table('user_data').select('*').eq('data_type', 'html_game').order('created_at', desc=True).execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting all uploaded games: {e}")
            return []
    
    def get_game_by_id(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets a specific game by its ID from any user
        
        Args:
            game_id: ID of the game
            
        Returns:
            Dictionary with game data or None if not found
        """
        if not self.is_connected():
            return None
        
        try:
            # Use service role key for server-side operations to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                response = service_client.table('user_data').select('*').eq('id', game_id).eq('data_type', 'html_game').execute()
            else:
                response = self.client.table('user_data').select('*').eq('id', game_id).eq('data_type', 'html_game').execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting game by ID {game_id}: {e}")
            return None
    
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
            # Use service role key for server-side operations to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                response = service_client.table('user_data').delete().eq('id', data_id).eq('user_id', user_id).execute()
            else:
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
    
    def upload_file_to_storage(self, bucket_name: str, file_path: str, file_content: bytes, content_type: str = None) -> Optional[str]:
        """
        Загружает файл в Supabase Storage
        
        Args:
            bucket_name: Имя bucket'а
            file_path: Путь к файлу в bucket'е
            file_content: Содержимое файла в байтах
            content_type: MIME тип файла
            
        Returns:
            URL загруженного файла или None при ошибке
        """
        if not self.is_connected():
            return None
        
        try:
            # Загружаем файл в storage
            response = self.client.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": content_type} if content_type else None
            )
            
            if response:
                # Получаем публичный URL файла
                public_url = self.client.storage.from_(bucket_name).get_public_url(file_path)
                logger.info(f"Файл {file_path} успешно загружен в bucket {bucket_name}")
                return public_url
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла в storage: {e}")
            return None
    
    def delete_file_from_storage(self, bucket_name: str, file_path: str) -> bool:
        """
        Удаляет файл из Supabase Storage
        
        Args:
            bucket_name: Имя bucket'а
            file_path: Путь к файлу в bucket'е
            
        Returns:
            True если удаление прошло успешно, False в противном случае
        """
        if not self.is_connected():
            return False
        
        try:
            response = self.client.storage.from_(bucket_name).remove([file_path])
            logger.info(f"Файл {file_path} успешно удален из bucket {bucket_name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при удалении файла из storage: {e}")
            return False
    
    def save_user_file(self, user_id: str, file_content: bytes, filename: str, content_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Сохраняет файл пользователя в storage и создает запись в user_data
        
        Args:
            user_id: ID пользователя
            file_content: Содержимое файла в байтах
            filename: Имя файла
            content_type: MIME тип файла
            
        Returns:
            Словарь с данными сохраненного файла или None при ошибке
        """
        if not self.is_connected():
            return None
        
        try:
            # Создаем уникальный путь для файла
            import uuid
            file_id = str(uuid.uuid4())
            file_extension = filename.split('.')[-1] if '.' in filename else 'html'
            storage_path = f"games/{user_id}/{file_id}.{file_extension}"
            
            # Загружаем файл в storage используя service role key для обхода RLS
            file_url = self.upload_file_to_storage_with_service_role(
                bucket_name="game-files",
                file_path=storage_path,
                file_content=file_content,
                content_type=content_type
            )
            
            if not file_url:
                logger.error("Не удалось загрузить файл в storage")
                return None
            
            # Сохраняем информацию о файле в user_data
            result = self.save_user_data(
                user_id=user_id,
                data_type="html_game",
                data_content=file_url,  # URL файла в storage
                filename=filename
            )
            
            if result:
                logger.info(f"Файл {filename} пользователя {user_id} успешно сохранен")
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении файла пользователя: {e}")
            return None
    
    def upload_file_to_storage_with_service_role(self, bucket_name: str, file_path: str, file_content: bytes, content_type: str = None) -> Optional[str]:
        """
        Загружает файл в Supabase Storage используя service role key
        
        Args:
            bucket_name: Имя bucket'а
            file_path: Путь к файлу в bucket'е
            file_content: Содержимое файла в байтах
            content_type: MIME тип файла
            
        Returns:
            URL загруженного файла или None при ошибке
        """
        if not self.service_role_key:
            logger.error("Service role key not configured")
            return None
        
        try:
            # Создаем клиент с service role key для обхода RLS
            from supabase import create_client
            service_client = create_client(self.url, self.service_role_key)
            
            # Загружаем файл в storage
            response = service_client.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": content_type} if content_type else None
            )
            
            if response:
                # Получаем публичный URL файла
                public_url = service_client.storage.from_(bucket_name).get_public_url(file_path)
                logger.info(f"Файл {file_path} успешно загружен в bucket {bucket_name}")
                return public_url
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла в storage: {e}")
            return None

# Глобальный экземпляр менеджера Supabase
supabase_manager = SupabaseManager()
