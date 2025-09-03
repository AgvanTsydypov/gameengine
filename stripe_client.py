"""
Модуль для работы со Stripe (заглушки для будущей интеграции)
"""
import os
import logging
from typing import Optional, Dict, Any
import stripe

logger = logging.getLogger(__name__)

class StripeManager:
    """Класс для управления интеграцией со Stripe"""
    
    def __init__(self):
        self.publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY')
        self.secret_key = os.getenv('STRIPE_SECRET_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        if self.secret_key:
            stripe.api_key = self.secret_key
            logger.info("Stripe API ключ настроен")
        else:
            logger.warning("Stripe секретный ключ не настроен")
    
    def is_configured(self) -> bool:
        """Проверяет, настроен ли Stripe"""
        return bool(self.secret_key and self.publishable_key)
    
    def create_customer(self, email: str, name: str = None) -> Optional[Dict[str, Any]]:
        """
        Создает клиента в Stripe
        
        Args:
            email: Email клиента
            name: Имя клиента (опционально)
            
        Returns:
            Словарь с данными клиента или None при ошибке
        """
        if not self.is_configured():
            logger.error("Stripe не настроен")
            return None
        
        try:
            customer_data = {
                'email': email,
            }
            
            if name:
                customer_data['name'] = name
            
            customer = stripe.Customer.create(**customer_data)
            logger.info(f"Клиент Stripe создан: {customer.id}")
            return customer
            
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка Stripe при создании клиента: {e}")
            return None
        except Exception as e:
            logger.error(f"Общая ошибка при создании клиента Stripe: {e}")
            return None
    
    def create_payment_intent(self, amount: int, currency: str = 'usd', customer_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Создает намерение платежа
        
        Args:
            amount: Сумма в центах
            currency: Валюта (по умолчанию USD)
            customer_id: ID клиента (опционально)
            
        Returns:
            Словарь с данными намерения платежа или None при ошибке
        """
        if not self.is_configured():
            logger.error("Stripe не настроен")
            return None
        
        try:
            intent_data = {
                'amount': amount,
                'currency': currency,
                'automatic_payment_methods': {
                    'enabled': True,
                },
            }
            
            if customer_id:
                intent_data['customer'] = customer_id
            
            intent = stripe.PaymentIntent.create(**intent_data)
            logger.info(f"Намерение платежа создано: {intent.id}")
            return intent
            
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка Stripe при создании намерения платежа: {e}")
            return None
        except Exception as e:
            logger.error(f"Общая ошибка при создании намерения платежа: {e}")
            return None
    
    def create_subscription(self, customer_id: str, price_id: str) -> Optional[Dict[str, Any]]:
        """
        Создает подписку
        
        Args:
            customer_id: ID клиента
            price_id: ID цены/плана
            
        Returns:
            Словарь с данными подписки или None при ошибке
        """
        if not self.is_configured():
            logger.error("Stripe не настроен")
            return None
        
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{
                    'price': price_id,
                }],
                payment_behavior='default_incomplete',
                payment_settings={'save_default_payment_method': 'on_subscription'},
                expand=['latest_invoice.payment_intent'],
            )
            
            logger.info(f"Подписка создана: {subscription.id}")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка Stripe при создании подписки: {e}")
            return None
        except Exception as e:
            logger.error(f"Общая ошибка при создании подписки: {e}")
            return None
    
    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает данные клиента
        
        Args:
            customer_id: ID клиента
            
        Returns:
            Словарь с данными клиента или None при ошибке
        """
        if not self.is_configured():
            return None
        
        try:
            customer = stripe.Customer.retrieve(customer_id)
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка Stripe при получении клиента: {e}")
            return None
        except Exception as e:
            logger.error(f"Общая ошибка при получении клиента: {e}")
            return None
    
    def get_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Получает клиента по email
        
        Args:
            email: Email клиента
            
        Returns:
            Словарь с данными клиента или None при ошибке
        """
        if not self.is_configured():
            return None
        
        try:
            customers = stripe.Customer.list(email=email, limit=1)
            return customers.data[0] if customers.data else None
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка Stripe при поиске клиента по email: {e}")
            return None
        except Exception as e:
            logger.error(f"Общая ошибка при поиске клиента по email: {e}")
            return None
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """
        Отменяет подписку
        
        Args:
            subscription_id: ID подписки
            
        Returns:
            True если отмена прошла успешно, False в противном случае
        """
        if not self.is_configured():
            return False
        
        try:
            stripe.Subscription.delete(subscription_id)
            logger.info(f"Подписка {subscription_id} отменена")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка Stripe при отмене подписки: {e}")
            return False
        except Exception as e:
            logger.error(f"Общая ошибка при отмене подписки: {e}")
            return False
    
    def create_webhook_endpoint(self, url: str, events: list) -> Optional[Dict[str, Any]]:
        """
        Создает webhook endpoint
        
        Args:
            url: URL для webhook
            events: Список событий для отслеживания
            
        Returns:
            Словарь с данными webhook или None при ошибке
        """
        if not self.is_configured():
            return None
        
        try:
            endpoint = stripe.WebhookEndpoint.create(
                url=url,
                enabled_events=events,
            )
            logger.info(f"Webhook endpoint создан: {endpoint.id}")
            return endpoint
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка Stripe при создании webhook: {e}")
            return None
        except Exception as e:
            logger.error(f"Общая ошибка при создании webhook: {e}")
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
            logger.error("Webhook секрет не настроен")
            return False
        
        try:
            stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return True
        except ValueError as e:
            logger.error(f"Неверный payload: {e}")
            return False
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Неверная подпись: {e}")
            return False

# Глобальный экземпляр менеджера Stripe
stripe_manager = StripeManager()
