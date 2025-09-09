"""
Supabase Client Module
"""
import os
import uuid
from datetime import datetime
from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    
    def save_user_data(self, user_id: str, data_type: str, data_content: str, filename: str = None, title: str = None, description: str = None, thumbnail_url: str = None) -> Optional[Dict[str, Any]]:
        """
        Saves user data to Supabase
        
        Args:
            user_id: User ID
            data_type: Data type
            data_content: Data content
            filename: File name (optional)
            title: Game title (optional)
            description: Game description (optional)
            thumbnail_url: Thumbnail URL (optional)
            
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
            
            # Add title, description, and thumbnail_url if provided
            if title:
                data["title"] = title
            if description:
                data["description"] = description
            if thumbnail_url:
                data["thumbnail_url"] = thumbnail_url
            
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
    
    def get_user_data_by_id(self, data_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает конкретную запись данных пользователя по ID
        
        Args:
            data_id: ID записи
            user_id: ID пользователя
            
        Returns:
            Словарь с данными записи или None если не найдена
        """
        if not self.is_connected():
            return None
        
        try:
            # Use service role key for server-side operations to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                response = service_client.table('user_data').select('*').eq('id', data_id).eq('user_id', user_id).eq('data_type', 'html_game').execute()
            else:
                response = self.client.table('user_data').select('*').eq('id', data_id).eq('user_id', user_id).eq('data_type', 'html_game').execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Ошибка при получении записи пользователя по ID: {e}")
            return None
    
    def get_all_uploaded_games(self) -> List[Dict[str, Any]]:
        """
        Gets all uploaded HTML games from all users
        
        Returns:
            List of dictionaries with game data for all users
        """
        if not self.is_connected():
            return []
        
        try:
            # ALWAYS use service role key to bypass RLS for public community games access
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                response = service_client.table('user_data').select('*').eq('data_type', 'html_game').order('created_at', desc=True).execute()
                return response.data if response.data else []
            else:
                # If no service role key is configured, we cannot provide public access to all games
                logger.error("Service role key not configured - cannot bypass RLS for public games access")
                return []
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
            # ALWAYS use service role key to bypass RLS for public game access
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                response = service_client.table('user_data').select('*').eq('id', game_id).eq('data_type', 'html_game').execute()
                if response.data and len(response.data) > 0:
                    return response.data[0]
                return None
            else:
                # If no service role key is configured, we cannot provide public access to games
                logger.error("Service role key not configured - cannot bypass RLS for public game access")
                return None
        except Exception as e:
            logger.error(f"Error getting game by ID {game_id}: {e}")
            return None
    
    def delete_user_data(self, data_id: str, user_id: str) -> bool:
        """
        Удаляет данные пользователя и связанные файлы из storage
        
        Args:
            data_id: ID записи данных
            user_id: ID пользователя
            
        Returns:
            True если удаление прошло успешно, False в противном случае
        """
        if not self.is_connected():
            return False
        
        try:
            # First, get the data record to extract file paths before deleting
            game_data = None
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                response = service_client.table('user_data').select('*').eq('id', data_id).eq('user_id', user_id).execute()
                if response.data:
                    game_data = response.data[0]
            else:
                response = self.client.table('user_data').select('*').eq('id', data_id).eq('user_id', user_id).execute()
                if response.data:
                    game_data = response.data[0]
            
            if not game_data:
                logger.warning(f"Game data {data_id} not found for user {user_id}")
                return False
            
            # Extract file paths from the data
            data_content = game_data.get('data_content')  # This contains the main file URL
            thumbnail_url = game_data.get('thumbnail_url')
            
            logger.info(f"Game data URLs - data_content: {data_content}")
            logger.info(f"Game data URLs - thumbnail_url: {thumbnail_url}")
            
            # Delete files from storage if they exist
            files_deleted = []
            
            # Delete main game file
            if data_content and 'game-files/' in data_content:
                try:
                    # Extract file path from data_content URL
                    # URL format: https://xxx.supabase.co/storage/v1/object/public/game-files/games/user_id/file_id.html
                    if 'games/' in data_content:
                        file_path = data_content.split('games/')[1]
                        # Remove query parameters if present
                        file_path = file_path.split('?')[0]
                        if self.delete_file_from_storage('game-files', f"games/{file_path}"):
                            files_deleted.append(f"Main file: games/{file_path}")
                            logger.info(f"Deleted main game file: games/{file_path}")
                        else:
                            logger.warning(f"Failed to delete main game file: games/{file_path}")
                except Exception as e:
                    logger.error(f"Error deleting main game file: {e}")
            
            # Delete thumbnail file
            if thumbnail_url and 'game-files/' in thumbnail_url:
                try:
                    # Extract file path from thumbnail URL
                    # URL format: https://xxx.supabase.co/storage/v1/object/public/game-files/thumbnails/user_id/thumbnail_id.png
                    if 'thumbnails/' in thumbnail_url:
                        thumbnail_path = thumbnail_url.split('thumbnails/')[1]
                        # Remove query parameters if present
                        thumbnail_path = thumbnail_path.split('?')[0]
                        if self.delete_file_from_storage('game-files', f"thumbnails/{thumbnail_path}"):
                            files_deleted.append(f"Thumbnail: thumbnails/{thumbnail_path}")
                            logger.info(f"Deleted thumbnail file: thumbnails/{thumbnail_path}")
                        else:
                            logger.warning(f"Failed to delete thumbnail file: thumbnails/{thumbnail_path}")
                except Exception as e:
                    logger.error(f"Error deleting thumbnail file: {e}")
            
            # Delete related likes for this game
            try:
                if self.service_role_key:
                    from supabase import create_client
                    service_client = create_client(self.url, self.service_role_key)
                    likes_response = service_client.table('game_likes').delete().eq('game_id', data_id).execute()
                else:
                    likes_response = self.client.table('game_likes').delete().eq('game_id', data_id).execute()
                
                logger.info(f"Deleted likes for game {data_id}")
            except Exception as e:
                logger.warning(f"Failed to delete likes for game {data_id}: {e}")
            
            # Now delete the database record
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                response = service_client.table('user_data').delete().eq('id', data_id).eq('user_id', user_id).execute()
            else:
                response = self.client.table('user_data').delete().eq('id', data_id).eq('user_id', user_id).execute()
            
            logger.info(f"Game data {data_id} for user {user_id} successfully deleted from database")
            if files_deleted:
                logger.info(f"Files deleted from storage: {', '.join(files_deleted)}")
            
            return True
        except Exception as e:
            logger.error(f"Error deleting user data: {e}")
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
            # Use service role key for server-side operations to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                response = service_client.storage.from_(bucket_name).remove([file_path])
            else:
                response = self.client.storage.from_(bucket_name).remove([file_path])
            
            logger.info(f"Файл {file_path} успешно удален из bucket {bucket_name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при удалении файла из storage: {e}")
            return False
    
    def save_user_file(self, user_id: str, file_content: bytes, filename: str, content_type: str = None, title: str = None, description: str = None, thumbnail_path: str = None) -> Optional[Dict[str, Any]]:
        """
        Сохраняет файл пользователя в storage и создает запись в user_data
        
        Args:
            user_id: ID пользователя
            file_content: Содержимое файла в байтах
            filename: Имя файла
            content_type: MIME тип файла
            title: Заголовок игры
            description: Описание игры
            thumbnail_path: Путь к файлу превью
            
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
            
            # Track uploaded files for cleanup in case of failure
            uploaded_files = [storage_path]
            
            # Upload thumbnail if provided
            thumbnail_url = None
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    # Validate thumbnail file
                    file_size = os.path.getsize(thumbnail_path)
                    if file_size == 0:
                        logger.error(f"Thumbnail file is empty: {thumbnail_path}")
                    else:
                        # Create thumbnail path in storage
                        thumbnail_id = str(uuid.uuid4())
                        thumbnail_storage_path = f"thumbnails/{user_id}/{thumbnail_id}.png"
                        
                        logger.info(f"Attempting to upload thumbnail: {thumbnail_path}")
                        logger.info(f"Thumbnail size: {file_size} bytes")
                        logger.info(f"Storage path: {thumbnail_storage_path}")
                        
                        # Read thumbnail file
                        with open(thumbnail_path, 'rb') as thumb_file:
                            thumbnail_content = thumb_file.read()
                        
                        logger.info(f"Read thumbnail content: {len(thumbnail_content)} bytes")
                        
                        # Upload thumbnail to storage (without content type to avoid MIME type restrictions)
                        thumbnail_url = self.upload_file_to_storage_with_service_role(
                            bucket_name="game-files",
                            file_path=thumbnail_storage_path,
                            file_content=thumbnail_content,
                            content_type=None  # Remove content type to avoid MIME type restrictions
                        )
                        
                        if thumbnail_url:
                            logger.info(f"Thumbnail uploaded successfully: {thumbnail_url}")
                            uploaded_files.append(thumbnail_storage_path)
                        else:
                            logger.warning("Failed to upload thumbnail, continuing without it")
                except Exception as e:
                    logger.error(f"Error uploading thumbnail: {e}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    # Continue without thumbnail
            else:
                if thumbnail_path:
                    logger.warning(f"Thumbnail file does not exist: {thumbnail_path}")
                else:
                    logger.info("No thumbnail path provided")
            
            # Сохраняем информацию о файле в user_data
            result = self.save_user_data(
                user_id=user_id,
                data_type="html_game",
                data_content=file_url,  # URL файла в storage
                filename=filename,
                title=title,
                description=description,
                thumbnail_url=thumbnail_url
            )
            
            if result:
                logger.info(f"Файл {filename} пользователя {user_id} успешно сохранен")
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении файла пользователя: {e}")
            # Clean up uploaded files in case of failure
            if 'uploaded_files' in locals():
                for file_path in uploaded_files:
                    try:
                        self.delete_file_from_storage("game-files", file_path)
                        logger.info(f"Cleaned up failed upload: {file_path}")
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to clean up file {file_path}: {cleanup_error}")
            return None
        finally:
            # Clean up thumbnail file if it was created locally
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    os.unlink(thumbnail_path)
                    logger.info(f"Cleaned up temporary thumbnail file: {thumbnail_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up thumbnail file: {e}")
    
    def update_user_file(self, data_id: str, user_id: str, file_content: bytes, title: str = None, description: str = None, thumbnail_path: str = None) -> Optional[Dict[str, Any]]:
        """
        Обновляет существующий файл пользователя в storage и обновляет запись в user_data
        
        Args:
            data_id: ID записи в user_data
            user_id: ID пользователя
            file_content: Новое содержимое файла в байтах
            title: Новый заголовок игры
            description: Новое описание игры
            thumbnail_path: Путь к новому файлу превью
            
        Returns:
            Словарь с данными обновленного файла или None при ошибке
        """
        if not self.is_connected():
            return None
        
        try:
            # Получаем текущую запись
            current_data = self.get_user_data_by_id(data_id, user_id)
            if not current_data:
                logger.error(f"Record {data_id} not found for user {user_id}")
                return None
            
            # Создаем новый уникальный путь для файла
            import uuid
            file_id = str(uuid.uuid4())
            filename = current_data.get('filename', 'game.html')
            file_extension = filename.split('.')[-1] if '.' in filename else 'html'
            storage_path = f"games/{user_id}/{file_id}.{file_extension}"
            
            # Загружаем новый файл в storage
            file_url = self.upload_file_to_storage_with_service_role(
                bucket_name="game-files",
                file_path=storage_path,
                file_content=file_content,
                content_type='text/html'
            )
            
            if not file_url:
                logger.error("Не удалось загрузить обновленный файл в storage")
                return None
            
            # Track uploaded files for cleanup in case of failure
            uploaded_files = [storage_path]
            
            # Upload new thumbnail if provided
            thumbnail_url = current_data.get('thumbnail_url')  # Keep existing thumbnail by default
            thumbnail_storage_path = None
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    # Validate thumbnail file
                    file_size = os.path.getsize(thumbnail_path)
                    if file_size == 0:
                        logger.error(f"Thumbnail file is empty: {thumbnail_path}")
                    else:
                        # Create new thumbnail path in storage
                        thumbnail_id = str(uuid.uuid4())
                        thumbnail_storage_path = f"thumbnails/{user_id}/{thumbnail_id}.png"
                        
                        logger.info(f"Attempting to upload new thumbnail: {thumbnail_path}")
                        logger.info(f"Thumbnail size: {file_size} bytes")
                        logger.info(f"Storage path: {thumbnail_storage_path}")
                        
                        # Read thumbnail file
                        with open(thumbnail_path, 'rb') as thumb_file:
                            thumbnail_content = thumb_file.read()
                        
                        logger.info(f"Read thumbnail content: {len(thumbnail_content)} bytes")
                        
                        # Upload new thumbnail to storage
                        thumbnail_url = self.upload_file_to_storage_with_service_role(
                            bucket_name="game-files",
                            file_path=thumbnail_storage_path,
                            file_content=thumbnail_content,
                            content_type=None
                        )
                        
                        if thumbnail_url:
                            logger.info(f"New thumbnail uploaded successfully: {thumbnail_url}")
                            uploaded_files.append(thumbnail_storage_path)
                        else:
                            logger.warning("Failed to upload new thumbnail, keeping existing one")
                            thumbnail_url = current_data.get('thumbnail_url')
                except Exception as e:
                    logger.error(f"Error uploading new thumbnail: {e}")
                    # Keep existing thumbnail
                    thumbnail_url = current_data.get('thumbnail_url')
            
            # Обновляем запись в user_data
            update_data = {
                'data_content': file_url,
                'updated_at': datetime.now().isoformat()
            }
            
            if title is not None:
                update_data['title'] = title
            if description is not None:
                update_data['description'] = description
            if thumbnail_url is not None:
                update_data['thumbnail_url'] = thumbnail_url
            
            # Use service role key for server-side operations to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                result = service_client.table('user_data').update(update_data).eq('id', data_id).eq('user_id', user_id).eq('data_type', 'html_game').execute()
            else:
                result = self.client.table('user_data').update(update_data).eq('id', data_id).eq('user_id', user_id).eq('data_type', 'html_game').execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"Файл {data_id} пользователя {user_id} успешно обновлен")
                
                # Clean up old files from storage after successful database update
                # This ensures we only delete old files if the new ones were successfully uploaded and DB updated
                old_file_url = current_data.get('data_content')
                old_thumbnail_url = current_data.get('thumbnail_url')
                
                # Delete old main game file
                if old_file_url and 'game-files/' in old_file_url:
                    try:
                        # Extract file path from old file URL
                        # URL format: https://xxx.supabase.co/storage/v1/object/public/game-files/games/user_id/file_id.html
                        if 'games/' in old_file_url:
                            old_file_path = old_file_url.split('games/')[1]
                            # Remove query parameters if present
                            old_file_path = old_file_path.split('?')[0]
                            if self.delete_file_from_storage('game-files', f"games/{old_file_path}"):
                                logger.info(f"Deleted old game file: games/{old_file_path}")
                            else:
                                logger.warning(f"Failed to delete old game file: games/{old_file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting old game file: {e}")
                
                # Delete old thumbnail file (only if we uploaded a new one)
                if thumbnail_storage_path and old_thumbnail_url and 'game-files/' in old_thumbnail_url:
                    try:
                        # Extract file path from old thumbnail URL
                        # URL format: https://xxx.supabase.co/storage/v1/object/public/game-files/thumbnails/user_id/thumbnail_id.png
                        if 'thumbnails/' in old_thumbnail_url:
                            old_thumbnail_path = old_thumbnail_url.split('thumbnails/')[1]
                            # Remove query parameters if present
                            old_thumbnail_path = old_thumbnail_path.split('?')[0]
                            if self.delete_file_from_storage('game-files', f"thumbnails/{old_thumbnail_path}"):
                                logger.info(f"Deleted old thumbnail file: thumbnails/{old_thumbnail_path}")
                            else:
                                logger.warning(f"Failed to delete old thumbnail file: thumbnails/{old_thumbnail_path}")
                    except Exception as e:
                        logger.error(f"Error deleting old thumbnail file: {e}")
                
                return result.data[0]
            else:
                logger.error(f"Не удалось обновить запись {data_id} - no data returned")
                logger.error(f"Update result: {result}")
                return None
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении файла пользователя: {e}")
            # Clean up uploaded files in case of failure
            if 'uploaded_files' in locals():
                for file_path in uploaded_files:
                    try:
                        self.delete_file_from_storage("game-files", file_path)
                        logger.info(f"Cleaned up failed upload: {file_path}")
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to clean up file {file_path}: {cleanup_error}")
            return None
        finally:
            # Clean up thumbnail file if it was created locally
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    os.unlink(thumbnail_path)
                    logger.info(f"Cleaned up temporary thumbnail file: {thumbnail_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up thumbnail file: {e}")
    
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
            logger.info(f"Creating service client for bucket: {bucket_name}")
            # Создаем клиент с service role key для обхода RLS
            from supabase import create_client
            service_client = create_client(self.url, self.service_role_key)
            
            logger.info(f"Attempting to upload file to {bucket_name}/{file_path}")
            logger.info(f"File content size: {len(file_content)} bytes")
            logger.info(f"Content type: {content_type}")
            
            # Загружаем файл в storage
            response = service_client.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": content_type} if content_type else None
            )
            
            logger.info(f"Upload response: {response}")
            
            if response:
                # Получаем публичный URL файла
                public_url = service_client.storage.from_(bucket_name).get_public_url(file_path)
                logger.info(f"Файл {file_path} успешно загружен в bucket {bucket_name}")
                logger.info(f"Public URL: {public_url}")
                return public_url
            else:
                logger.error("Upload response was empty or None")
                return None
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла в storage: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None

    # ============ LIKES SYSTEM METHODS ============
    
    def like_game(self, game_id: str, user_id: str) -> bool:
        """
        Likes a game for a user
        
        Args:
            game_id: ID of the game to like
            user_id: ID of the user liking the game
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Use service role key to bypass RLS for likes operations
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                
                # Insert like record
                response = service_client.table('game_likes').insert({
                    'game_id': game_id,
                    'user_id': user_id
                }).execute()
                
                if response.data:
                    logger.info(f"User {user_id} liked game {game_id}")
                    return True
                    
            return False
            
        except Exception as e:
            # Handle duplicate like (user already liked this game)
            if 'unique constraint' in str(e).lower() or 'duplicate key' in str(e).lower():
                logger.info(f"User {user_id} already liked game {game_id}")
                return True  # Consider it successful since the desired state is achieved
            
            logger.error(f"Error liking game {game_id} for user {user_id}: {e}")
            return False
    
    def unlike_game(self, game_id: str, user_id: str) -> bool:
        """
        Unlikes a game for a user
        
        Args:
            game_id: ID of the game to unlike
            user_id: ID of the user unliking the game
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Use service role key to bypass RLS for likes operations
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                
                # Delete like record
                response = service_client.table('game_likes').delete().eq('game_id', game_id).eq('user_id', user_id).execute()
                
                logger.info(f"User {user_id} unliked game {game_id}")
                return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error unliking game {game_id} for user {user_id}: {e}")
            return False
    
    def get_user_liked_games(self, user_id: str) -> List[str]:
        """
        Gets list of game IDs that a user has liked
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of game IDs that the user has liked
        """
        if not self.is_connected():
            return []
        
        try:
            # Use service role key to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                
                response = service_client.table('game_likes').select('game_id').eq('user_id', user_id).execute()
                
                if response.data:
                    return [like['game_id'] for like in response.data]
                    
            return []
            
        except Exception as e:
            logger.warning(f"Likes table not available, returning empty likes list: {e}")
            return []  # Return empty list if likes table doesn't exist
    
    def is_game_liked_by_user(self, game_id: str, user_id: str) -> bool:
        """
        Checks if a specific game is liked by a user
        
        Args:
            game_id: ID of the game
            user_id: ID of the user
            
        Returns:
            True if user has liked the game, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Use service role key to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                
                response = service_client.table('game_likes').select('id').eq('game_id', game_id).eq('user_id', user_id).execute()
                
                return len(response.data or []) > 0
                    
            return False
            
        except Exception as e:
            logger.error(f"Error checking if game {game_id} is liked by user {user_id}: {e}")
            return False
    
    def get_games_with_stats(self, limit: int = None, order_by: str = 'created_at') -> List[Dict[str, Any]]:
        """
        Gets all uploaded HTML games with their statistics (likes, plays)
        Falls back to basic game data if statistics tables don't exist
        
        Args:
            limit: Maximum number of games to return
            order_by: Field to order by ('created_at', 'likes_count', 'plays_count')
            
        Returns:
            List of dictionaries with game data and statistics
        """
        if not self.is_connected():
            return []
        
        try:
            # Use service role key to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                
                try:
                    # Try to query games with statistics join
                    query = service_client.table('user_data').select(
                        '*, game_statistics(likes_count, plays_count, updated_at)'
                    ).eq('data_type', 'html_game')
                    
                    # Apply ordering - Supabase doesn't support ordering by joined table fields directly
                    # We'll do client-side sorting after getting the data
                    query = query.order('created_at', desc=True)
                    
                    # Apply limit if specified
                    if limit:
                        query = query.limit(limit)
                    
                    response = query.execute()
                    
                    if response.data:
                        # Process the data to flatten statistics
                        games = []
                        for game in response.data:
                            stats = game.get('game_statistics')
                            if stats and isinstance(stats, dict):
                                # Single statistics record as dictionary
                                game['likes_count'] = stats.get('likes_count', 0)
                                game['plays_count'] = stats.get('plays_count', 0)
                            elif stats and isinstance(stats, list) and len(stats) > 0:
                                # Multiple statistics records as list (take first)
                                stat = stats[0]
                                game['likes_count'] = stat.get('likes_count', 0)
                                game['plays_count'] = stat.get('plays_count', 0)
                            else:
                                # No statistics record yet, initialize with defaults
                                game['likes_count'] = 0
                                game['plays_count'] = 0
                            
                            # Remove the nested statistics object
                            if 'game_statistics' in game:
                                del game['game_statistics']
                            
                            games.append(game)
                        
                        # Apply client-side sorting based on order_by parameter
                        if order_by == 'likes_count':
                            games.sort(key=lambda x: x.get('likes_count', 0), reverse=True)
                        elif order_by == 'plays_count':
                            games.sort(key=lambda x: x.get('plays_count', 0), reverse=True)
                        # created_at is already sorted by the query
                        
                        # Apply limit after sorting
                        if limit:
                            games = games[:limit]
                        
                        return games
                        
                except Exception as stats_error:
                    logger.warning(f"Statistics table not available, falling back to basic games: {stats_error}")
                    # Fall back to basic game query without statistics
                    return self._get_games_fallback(service_client, limit, order_by)
                    
            return []
            
        except Exception as e:
            logger.error(f"Error getting games with statistics: {e}")
            # Try fallback with regular client if service role fails
            try:
                return self._get_games_fallback(self.client, limit, order_by)
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                return []
    
    def _get_games_fallback(self, client, limit: int = None, order_by: str = 'created_at') -> List[Dict[str, Any]]:
        """
        Fallback method to get games without statistics when likes system tables don't exist
        """
        try:
            # Query basic games data
            query = client.table('user_data').select('*').eq('data_type', 'html_game')
            
            # Always order by created_at first, then we'll sort client-side
            query = query.order('created_at', desc=True)
            
            # Don't apply limit here - we need to sort first, then limit
            response = query.execute()
            
            if response.data:
                # Add default statistics to games
                games = []
                for game in response.data:
                    game['likes_count'] = 0  # Default values when no stats table
                    game['plays_count'] = 0
                    games.append(game)
                
                # Apply client-side sorting based on order_by parameter
                if order_by == 'likes_count':
                    games.sort(key=lambda x: x.get('likes_count', 0), reverse=True)
                elif order_by == 'plays_count':
                    games.sort(key=lambda x: x.get('plays_count', 0), reverse=True)
                # created_at is already sorted by the query
                
                # Apply limit after sorting
                if limit:
                    games = games[:limit]
                
                return games
                
            return []
            
        except Exception as e:
            logger.error(f"Fallback method failed: {e}")
            return []
    
    def increment_game_play_count(self, game_id: str) -> bool:
        """
        Increments the play count for a game
        
        Args:
            game_id: ID of the game
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Use service role key to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                
                # Try to update existing record
                existing = service_client.table('game_statistics').select('*').eq('game_id', game_id).execute()
                
                if existing.data and len(existing.data) > 0:
                    # Update existing record
                    new_count = existing.data[0]['plays_count'] + 1
                    service_client.table('game_statistics').update({
                        'plays_count': new_count,
                        'updated_at': 'now()'
                    }).eq('game_id', game_id).execute()
                else:
                    # Create new record
                    service_client.table('game_statistics').insert({
                        'game_id': game_id,
                        'likes_count': 0,
                        'plays_count': 1
                    }).execute()
                
                logger.info(f"Incremented play count for game {game_id}")
                return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error incrementing play count for game {game_id}: {e}")
            return False

    # ============ CREDITS SYSTEM METHODS ============
    
    def get_user_credits(self, user_id: str) -> int:
        """
        Gets the current credits for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            Number of credits the user has, 0 if not found
        """
        if not self.is_connected():
            return 0
        
        try:
            # Use service role key to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                
                response = service_client.table('user_credits').select('credits').eq('user_id', user_id).execute()
                
                if response.data and len(response.data) > 0:
                    return response.data[0]['credits']
                else:
                    # User doesn't have credits record yet, create one with 2 credits
                    logger.info(f"User {user_id} doesn't have credits record, creating one with 2 credits")
                    return self.create_user_credits_record(user_id, 2)
                    
            return 0
            
        except Exception as e:
            logger.error(f"Error getting credits for user {user_id}: {e}")
            return 0
    
    def create_user_credits_record(self, user_id: str, initial_credits: int = 2) -> int:
        """
        Creates a credits record for a user
        
        Args:
            user_id: ID of the user
            initial_credits: Initial number of credits (default 2)
            
        Returns:
            Number of credits created, 0 if failed
        """
        if not self.is_connected():
            return 0
        
        try:
            # Use service role key to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                
                response = service_client.table('user_credits').insert({
                    'user_id': user_id,
                    'credits': initial_credits
                }).execute()
                
                if response.data and len(response.data) > 0:
                    logger.info(f"Created credits record for user {user_id} with {initial_credits} credits")
                    return response.data[0]['credits']
                    
            return 0
            
        except Exception as e:
            logger.error(f"Error creating credits record for user {user_id}: {e}")
            return 0
    
    def update_user_credits(self, user_id: str, new_credits: int) -> bool:
        """
        Updates the credits for a user
        
        Args:
            user_id: ID of the user
            new_credits: New number of credits
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Use service role key to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                
                response = service_client.table('user_credits').update({
                    'credits': new_credits,
                    'updated_at': 'now()'
                }).eq('user_id', user_id).execute()
                
                if response.data and len(response.data) > 0:
                    logger.info(f"Updated credits for user {user_id} to {new_credits}")
                    return True
                else:
                    # User doesn't have credits record yet, create one
                    logger.info(f"User {user_id} doesn't have credits record, creating one with {new_credits} credits")
                    return self.create_user_credits_record(user_id, new_credits) > 0
                    
            return False
            
        except Exception as e:
            logger.error(f"Error updating credits for user {user_id}: {e}")
            return False
    
    def deduct_credits(self, user_id: str, amount: int) -> bool:
        """
        Deducts credits from a user's account
        
        Args:
            user_id: ID of the user
            amount: Number of credits to deduct
            
        Returns:
            True if successful, False if insufficient credits or error
        """
        if not self.is_connected():
            return False
        
        try:
            current_credits = self.get_user_credits(user_id)
            
            if current_credits < amount:
                logger.warning(f"User {user_id} has insufficient credits: {current_credits} < {amount}")
                return False
            
            new_credits = current_credits - amount
            return self.update_user_credits(user_id, new_credits)
            
        except Exception as e:
            logger.error(f"Error deducting credits for user {user_id}: {e}")
            return False
    
    def add_credits(self, user_id: str, amount: int) -> bool:
        """
        Adds credits to a user's account
        
        Args:
            user_id: ID of the user
            amount: Number of credits to add
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            current_credits = self.get_user_credits(user_id)
            new_credits = current_credits + amount
            return self.update_user_credits(user_id, new_credits)
            
        except Exception as e:
            logger.error(f"Error adding credits for user {user_id}: {e}")
            return False

    def search_games_with_stats(self, search_query: str, limit: int = None, order_by: str = 'created_at') -> List[Dict[str, Any]]:
        """
        Search games with statistics by title only
        
        Args:
            search_query: Search term to look for in game titles
            limit: Maximum number of games to return
            order_by: Field to order by ('created_at', 'likes_count', 'plays_count')
            
        Returns:
            List of dictionaries with game data and statistics
        """
        if not self.is_connected() or not search_query.strip():
            return []
        
        try:
            # Use service role key to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                
                try:
                    # Search in title field only using ilike for case-insensitive search
                    query = service_client.table('user_data').select(
                        '*, game_statistics(likes_count, plays_count, updated_at)'
                    ).eq('data_type', 'html_game').ilike('title', f'%{search_query}%')
                    
                    # Apply ordering
                    query = query.order('created_at', desc=True)
                    
                    # Apply limit if specified
                    if limit:
                        query = query.limit(limit)
                    
                    response = query.execute()
                    
                    if response.data:
                        # Process the data to flatten statistics
                        games = []
                        for game in response.data:
                            stats = game.get('game_statistics')
                            if stats and isinstance(stats, dict):
                                game['likes_count'] = stats.get('likes_count', 0)
                                game['plays_count'] = stats.get('plays_count', 0)
                            elif stats and isinstance(stats, list) and len(stats) > 0:
                                stat = stats[0]
                                game['likes_count'] = stat.get('likes_count', 0)
                                game['plays_count'] = stat.get('plays_count', 0)
                            else:
                                game['likes_count'] = 0
                                game['plays_count'] = 0
                            games.append(game)
                        
                        # Client-side sorting for statistics
                        if order_by == 'likes_count':
                            games.sort(key=lambda x: x.get('likes_count', 0), reverse=True)
                        elif order_by == 'plays_count':
                            games.sort(key=lambda x: x.get('plays_count', 0), reverse=True)
                        
                        return games
                    
                    return []
                    
                except Exception as e:
                    logger.error(f"Error searching games with stats: {e}")
                    # Fallback to basic search
                    return self._search_games_fallback(service_client, search_query, limit, order_by)
            else:
                return self._search_games_fallback(self.client, search_query, limit, order_by)
                
        except Exception as e:
            logger.error(f"Error in search_games_with_stats: {e}")
            return []
    
    def _search_games_fallback(self, client, search_query: str, limit: int = None, order_by: str = 'created_at') -> List[Dict[str, Any]]:
        """
        Fallback method to search games without statistics when likes system tables don't exist
        """
        try:
            # Search in title field only
            query = client.table('user_data').select('*').eq('data_type', 'html_game').ilike('title', f'%{search_query}%')
            
            # Simple ordering
            query = query.order('created_at', desc=True)
            
            # Apply limit if specified
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            
            if response.data:
                # Add default statistics to games
                games = []
                for game in response.data:
                    game['likes_count'] = 0
                    game['plays_count'] = 0
                    games.append(game)
                
                return games
                
            return []
            
        except Exception as e:
            logger.error(f"Fallback search method failed: {e}")
            return []
    
    def search_user_games(self, user_id: str, search_query: str) -> List[Dict[str, Any]]:
        """
        Search user's games by title only
        
        Args:
            user_id: ID of the user
            search_query: Search term to look for in game titles
            
        Returns:
            List of dictionaries with user's game data
        """
        if not self.is_connected() or not search_query.strip():
            return []
        
        try:
            # Use service role key for server-side operations to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                response = service_client.table('user_data').select('*').eq('user_id', user_id).eq('data_type', 'html_game').ilike('title', f'%{search_query}%').order('created_at', desc=True).execute()
            else:
                response = self.client.table('user_data').select('*').eq('user_id', user_id).eq('data_type', 'html_game').ilike('title', f'%{search_query}%').order('created_at', desc=True).execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error searching user games: {e}")
            return []

    # ============ NICKNAMES SYSTEM METHODS ============
    
    def get_user_nickname(self, user_id: str) -> Optional[str]:
        """
        Gets the nickname for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            User's nickname or None if not found
        """
        if not self.is_connected():
            return None
        
        try:
            # Use service role key to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                response = service_client.table('user_nicknames').select('nickname').eq('user_id', user_id).execute()
            else:
                response = self.client.table('user_nicknames').select('nickname').eq('user_id', user_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]['nickname']
            return None
            
        except Exception as e:
            logger.error(f"Error getting nickname for user {user_id}: {e}")
            return None
    
    def set_user_nickname(self, user_id: str, nickname: str) -> bool:
        """
        Sets or updates the nickname for a user
        
        Args:
            user_id: ID of the user
            nickname: The nickname to set
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected() or not nickname.strip():
            return False
        
        # Validate nickname length and characters
        nickname = nickname.strip()
        if len(nickname) < 2 or len(nickname) > 50:
            logger.error(f"Nickname must be between 2 and 50 characters: {nickname}")
            return False
        
        # Check for valid characters (alphanumeric, spaces, hyphens, underscores)
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', nickname):
            logger.error(f"Nickname contains invalid characters: {nickname}")
            return False
        
        try:
            # Use service role key to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                
                # Try to update existing nickname first
                update_response = service_client.table('user_nicknames').update({
                    'nickname': nickname,
                    'updated_at': 'now()'
                }).eq('user_id', user_id).execute()
                
                if update_response.data and len(update_response.data) > 0:
                    logger.info(f"Updated nickname for user {user_id} to '{nickname}'")
                    return True
                
                # If no existing record, insert new one
                insert_response = service_client.table('user_nicknames').insert({
                    'user_id': user_id,
                    'nickname': nickname
                }).execute()
                
                if insert_response.data and len(insert_response.data) > 0:
                    logger.info(f"Set nickname for user {user_id} to '{nickname}'")
                    return True
                    
            return False
            
        except Exception as e:
            # Handle duplicate nickname error
            if 'unique constraint' in str(e).lower() or 'duplicate key' in str(e).lower():
                logger.error(f"Nickname '{nickname}' is already taken")
                return False
            
            logger.error(f"Error setting nickname for user {user_id}: {e}")
            return False
    
    def delete_user_nickname(self, user_id: str) -> bool:
        """
        Deletes the nickname for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Use service role key to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                response = service_client.table('user_nicknames').delete().eq('user_id', user_id).execute()
                
                logger.info(f"Deleted nickname for user {user_id}")
                return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error deleting nickname for user {user_id}: {e}")
            return False
    
    def get_nickname_by_user_id(self, user_id: str) -> Optional[str]:
        """
        Gets nickname by user ID (alias for get_user_nickname for consistency)
        
        Args:
            user_id: ID of the user
            
        Returns:
            User's nickname or None if not found
        """
        return self.get_user_nickname(user_id)
    
    def get_all_nicknames(self) -> Dict[str, str]:
        """
        Gets all user nicknames as a mapping of user_id to nickname
        
        Returns:
            Dictionary mapping user_id to nickname
        """
        if not self.is_connected():
            return {}
        
        try:
            # Use service role key to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                response = service_client.table('user_nicknames').select('user_id, nickname').execute()
            else:
                response = self.client.table('user_nicknames').select('user_id, nickname').execute()
            
            if response.data:
                return {item['user_id']: item['nickname'] for item in response.data}
            return {}
            
        except Exception as e:
            logger.error(f"Error getting all nicknames: {e}")
            return {}
    
    def get_games_with_nicknames(self, limit: int = None, order_by: str = 'created_at') -> List[Dict[str, Any]]:
        """
        Gets all uploaded HTML games with user nicknames (if available)
        Falls back to regular games if nicknames table doesn't exist
        
        Args:
            limit: Maximum number of games to return
            order_by: Field to order by ('created_at', 'likes_count', 'plays_count')
            
        Returns:
            List of dictionaries with game data and user nicknames
        """
        if not self.is_connected():
            return []
        
        try:
            # For trending games (likes_count ordering), always try to get actual likes data first
            if order_by == 'likes_count':
                logger.info("Getting games with actual likes data for trending")
                games = self._get_games_with_actual_likes(limit)
            else:
                # For other orderings, use the stats method
                games = self.get_games_with_stats(limit, order_by)
            
            if not games:
                return []
            
            # Now try to get nicknames for all users and add them to the games
            try:
                # Get all nicknames
                if self.service_role_key:
                    from supabase import create_client
                    service_client = create_client(self.url, self.service_role_key)
                    nicknames_response = service_client.table('user_nicknames').select('user_id, nickname').execute()
                    
                    if nicknames_response.data:
                        # Create a mapping of user_id to nickname
                        nicknames_map = {item['user_id']: item['nickname'] for item in nicknames_response.data}
                        
                        # Add nicknames to games
                        for game in games:
                            user_id = game.get('user_id')
                            if user_id in nicknames_map:
                                game['user_nickname'] = nicknames_map[user_id]
                            else:
                                game['user_nickname'] = None
                    else:
                        # No nicknames found, set all to None
                        for game in games:
                            game['user_nickname'] = None
                            
            except Exception as e:
                logger.warning(f"Could not fetch nicknames, games will show user IDs: {e}")
                # Set all nicknames to None if we can't fetch them
                for game in games:
                    game['user_nickname'] = None
            
            return games
            
        except Exception as e:
            logger.error(f"Error getting games with nicknames: {e}")
            return []
    
    def _get_games_with_actual_likes(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Gets games with actual likes count from game_likes table
        This is a fallback when the statistics table doesn't work properly
        
        Args:
            limit: Maximum number of games to return
            
        Returns:
            List of dictionaries with game data and actual likes count
        """
        if not self.is_connected():
            return []
        
        try:
            # Use service role key to bypass RLS
            if self.service_role_key:
                from supabase import create_client
                service_client = create_client(self.url, self.service_role_key)
                
                # Get all games first
                games_response = service_client.table('user_data').select('*').eq('data_type', 'html_game').execute()
                
                if not games_response.data:
                    logger.info("No games found in database")
                    return []
                
                logger.info(f"Found {len(games_response.data)} games, counting likes...")
                
                # Get likes count for each game
                games = []
                for game in games_response.data:
                    game_id = game.get('id')
                    
                    try:
                        # Count likes for this game
                        likes_response = service_client.table('game_likes').select('id', count='exact').eq('game_id', game_id).execute()
                        likes_count = likes_response.count if likes_response.count is not None else 0
                        
                        plays_response = service_client.table('game_statistics').select('plays_count').eq('game_id', game_id).execute()
                        plays_count = plays_response.data[0]['plays_count'] if plays_response.data and len(plays_response.data) > 0 else 0
                        
                        game['likes_count'] = likes_count
                        game['plays_count'] = plays_count
                        games.append(game)
                        
                        if likes_count > 0:
                            logger.info(f"Game {game.get('title', 'Untitled')} has {likes_count} likes")
                            
                    except Exception as e:
                        logger.warning(f"Error counting likes for game {game_id}: {e}")
                        # Still add the game with 0 likes
                        game['likes_count'] = 0
                        game['plays_count'] = 0
                        games.append(game)
                
                # Sort by likes count (descending)
                games.sort(key=lambda x: x.get('likes_count', 0), reverse=True)
                
                # Apply limit after sorting
                if limit:
                    games = games[:limit]
                
                logger.info(f"Retrieved {len(games)} games with actual likes data")
                if games:
                    logger.info(f"Top game has {games[0].get('likes_count', 0)} likes")
                return games
                
            return []
            
        except Exception as e:
            logger.error(f"Error getting games with actual likes: {e}")
            return []
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Gets user by email address
        
        Args:
            email: User's email address
            
        Returns:
            Dictionary with user data or None
        """
        if not self.is_connected():
            logger.error("Supabase not connected")
            return None
        
        try:
            # Query auth.users table using service role key
            if not self.service_role_key:
                logger.error("Service role key not configured")
                return None
            
            # Create a client with service role key for admin operations
            admin_client = create_client(self.url, self.service_role_key)
            
            # Get user from auth.users
            result = admin_client.auth.admin.list_users()
            
            for user in result:
                if user.email == email:
                    return {
                        'id': user.id,
                        'email': user.email,
                        'created_at': user.created_at
                    }
            
            logger.warning(f"User with email {email} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None

# Глобальный экземпляр менеджера Supabase
supabase_manager = SupabaseManager()
