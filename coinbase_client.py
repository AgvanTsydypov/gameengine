"""
Модуль для работы с Coinbase Commerce (криптовалютные платежи)
"""
import os
import logging
from typing import Optional, Dict, Any
from coinbase_commerce.client import Client
from coinbase_commerce.error import CoinbaseError

logger = logging.getLogger(__name__)

class CoinbaseCommerceManager:
    """Класс для управления интеграцией с Coinbase Commerce"""
    
    def __init__(self):
        self.api_key = os.getenv('COINBASE_COMMERCE_API_KEY')
        self.webhook_secret = os.getenv('COINBASE_COMMERCE_WEBHOOK_SECRET')
        
        if self.api_key:
            self.client = Client(api_key=self.api_key)
            logger.info("Coinbase Commerce API ключ настроен")
        else:
            self.client = None
            logger.warning("Coinbase Commerce API ключ не настроен")
    
    def is_configured(self) -> bool:
        """Проверяет, настроен ли Coinbase Commerce"""
        return bool(self.api_key and self.webhook_secret)
    
    def create_charge(self, name: str, description: str, amount: str, currency: str = 'USD', 
                     metadata: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Создает платеж (charge) в Coinbase Commerce
        
        Args:
            name: Название товара/услуги
            description: Описание
            amount: Сумма в долларах (например, "10.00")
            currency: Валюта (по умолчанию USD)
            metadata: Дополнительные данные
            
        Returns:
            Словарь с данными платежа или None при ошибке
        """
        if not self.is_configured():
            logger.error("Coinbase Commerce не настроен")
            return None
        
        try:
            charge_data = {
                'name': name,
                'description': description,
                'local_price': {
                    'amount': amount,
                    'currency': currency
                },
                'pricing_type': 'fixed_price'
            }
            
            if metadata:
                charge_data['metadata'] = metadata
            
            charge = self.client.charge.create(**charge_data)
            logger.info(f"Платеж Coinbase Commerce создан: {charge.id}")
            return charge
            
        except CoinbaseError as e:
            logger.error(f"Ошибка Coinbase Commerce при создании платежа: {e}")
            return None
        except Exception as e:
            logger.error(f"Общая ошибка при создании платежа Coinbase Commerce: {e}")
            return None
    
    def get_charge(self, charge_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает данные платежа по ID
        
        Args:
            charge_id: ID платежа
            
        Returns:
            Словарь с данными платежа или None при ошибке
        """
        if not self.is_configured():
            return None
        
        try:
            charge = self.client.charge.retrieve(charge_id)
            return charge
        except CoinbaseError as e:
            logger.error(f"Ошибка Coinbase Commerce при получении платежа: {e}")
            return None
        except Exception as e:
            logger.error(f"Общая ошибка при получении платежа Coinbase Commerce: {e}")
            return None
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Проверяет подпись webhook
        
        Args:
            payload: Тело запроса
            signature: Заголовок подписи
            
        Returns:
            True если подпись верна, False в противном случае
        """
        if not self.webhook_secret:
            logger.error("Webhook секрет не настроен - webhook verification disabled")
            logger.error("Set COINBASE_COMMERCE_WEBHOOK_SECRET environment variable to enable webhook verification")
            return False
        
        if not signature:
            logger.error("Missing CB-Signature header")
            return False
        
        try:
            import hmac
            import hashlib
            import base64
            
            # Coinbase Commerce использует HMAC SHA256
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).digest()
            
            expected_signature_b64 = base64.b64encode(expected_signature).decode('utf-8')
            
            if hmac.compare_digest(expected_signature_b64, signature):
                logger.info("Coinbase Commerce webhook signature verified successfully")
                return True
            else:
                logger.error("Coinbase Commerce webhook signature verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Error during Coinbase Commerce webhook signature verification: {e}")
            return False
    
    def get_supported_cryptocurrencies(self) -> list:
        """
        Возвращает список поддерживаемых криптовалют
        
        Returns:
            Список криптовалют
        """
        return [
            'BTC',  # Bitcoin
            'ETH',  # Ethereum
            'LTC',  # Litecoin
            'BCH',  # Bitcoin Cash
            'USDC', # USD Coin
            'USDT', # Tether
            'DAI',  # Dai
        ]
    
    def format_amount(self, amount: float) -> str:
        """
        Форматирует сумму для Coinbase Commerce
        
        Args:
            amount: Сумма в долларах
            
        Returns:
            Отформатированная строка суммы
        """
        return f"{amount:.2f}"

# Глобальный экземпляр менеджера Coinbase Commerce
coinbase_manager = CoinbaseCommerceManager()
