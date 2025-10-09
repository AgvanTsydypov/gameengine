"""
NOWPayments API Integration Module
Handles cryptocurrency payment processing via NOWPayments
"""
import os
import logging
import requests
import hmac
import hashlib
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class NOWPaymentsManager:
    """Class for managing NOWPayments API integration"""
    
    # NOWPayments API Base URLs
    PRODUCTION_URL = "https://api.nowpayments.io/v1"
    SANDBOX_URL = "https://api-sandbox.nowpayments.io/v1"
    
    def __init__(self):
        self.api_key = os.getenv('NOWPAYMENTS_API_KEY')
        self.ipn_secret = os.getenv('NOWPAYMENTS_IPN_SECRET')
        self.use_sandbox = os.getenv('NOWPAYMENTS_SANDBOX', 'false').lower() == 'true'
        
        # Set base URL based on environment
        self.base_url = self.SANDBOX_URL if self.use_sandbox else self.PRODUCTION_URL
        
        if self.api_key:
            logger.info(f"NOWPayments API configured ({'sandbox' if self.use_sandbox else 'production'} mode)")
        else:
            logger.warning("NOWPayments API key not configured")
    
    def is_configured(self) -> bool:
        """Check if NOWPayments is properly configured"""
        return bool(self.api_key)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def get_available_currencies(self) -> Optional[List[str]]:
        """
        Get list of available cryptocurrencies
        
        Returns:
            List of currency codes or None on error
        """
        if not self.is_configured():
            logger.error("NOWPayments not configured")
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/currencies",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                currencies = data.get('currencies', [])
                logger.info(f"Retrieved {len(currencies)} available currencies")
                return currencies
            else:
                logger.error(f"Failed to get currencies: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting available currencies: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting currencies: {e}")
            return None
    
    def get_minimum_payment_amount(self, currency_from: str, currency_to: str) -> Optional[float]:
        """
        Get minimum payment amount for currency pair
        
        Args:
            currency_from: Source currency (e.g., 'usd')
            currency_to: Target cryptocurrency (e.g., 'btc')
            
        Returns:
            Minimum amount or None on error
        """
        if not self.is_configured():
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/min-amount",
                headers=self._get_headers(),
                params={
                    'currency_from': currency_from,
                    'currency_to': currency_to
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return float(data.get('min_amount', 0))
            else:
                logger.error(f"Failed to get minimum amount: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting minimum amount: {e}")
            return None
    
    def create_payment(self, 
                      price_amount: float,
                      price_currency: str,
                      pay_currency: str,
                      order_id: str,
                      order_description: str,
                      ipn_callback_url: str,
                      success_url: str = None,
                      cancel_url: str = None) -> Optional[Dict[str, Any]]:
        """
        Create a new payment
        
        Args:
            price_amount: Payment amount in price_currency
            price_currency: Currency of the price (e.g., 'usd')
            pay_currency: Cryptocurrency to receive (e.g., 'btc')
            order_id: Unique order identifier
            order_description: Description of the order
            ipn_callback_url: URL for payment status notifications
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect on payment cancellation
            
        Returns:
            Dictionary with payment data or None on error
        """
        if not self.is_configured():
            logger.error("NOWPayments not configured")
            return None
        
        try:
            payload = {
                'price_amount': price_amount,
                'price_currency': price_currency.lower(),
                'pay_currency': pay_currency.lower(),
                'order_id': order_id,
                'order_description': order_description,
                'ipn_callback_url': ipn_callback_url
            }
            
            # Add optional URLs if provided
            if success_url:
                payload['success_url'] = success_url
            if cancel_url:
                payload['cancel_url'] = cancel_url
            
            response = requests.post(
                f"{self.base_url}/payment",
                headers=self._get_headers(),
                json=payload,
                timeout=10
            )
            
            if response.status_code == 201 or response.status_code == 200:
                payment_data = response.json()
                logger.info(f"Payment created: {payment_data.get('payment_id')} for order {order_id}")
                return payment_data
            else:
                logger.error(f"Failed to create payment: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating payment: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating payment: {e}")
            return None
    
    def create_invoice(self,
                      price_amount: float,
                      price_currency: str,
                      order_id: str,
                      order_description: str,
                      ipn_callback_url: str,
                      success_url: str = None,
                      cancel_url: str = None) -> Optional[Dict[str, Any]]:
        """
        Create an invoice (allows customer to choose cryptocurrency)
        
        Args:
            price_amount: Payment amount in price_currency
            price_currency: Currency of the price (e.g., 'usd')
            order_id: Unique order identifier
            order_description: Description of the order
            ipn_callback_url: URL for payment status notifications
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect on payment cancellation
            
        Returns:
            Dictionary with invoice data or None on error
        """
        if not self.is_configured():
            logger.error("NOWPayments not configured")
            return None
        
        try:
            payload = {
                'price_amount': price_amount,
                'price_currency': price_currency.lower(),
                'order_id': order_id,
                'order_description': order_description,
                'ipn_callback_url': ipn_callback_url
            }
            
            # Add optional URLs if provided
            if success_url:
                payload['success_url'] = success_url
            if cancel_url:
                payload['cancel_url'] = cancel_url
            
            response = requests.post(
                f"{self.base_url}/invoice",
                headers=self._get_headers(),
                json=payload,
                timeout=10
            )
            
            if response.status_code == 201 or response.status_code == 200:
                invoice_data = response.json()
                logger.info(f"Invoice created: {invoice_data.get('id')} for order {order_id}")
                return invoice_data
            else:
                logger.error(f"Failed to create invoice: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating invoice: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating invoice: {e}")
            return None
    
    def get_payment_status(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """
        Get payment status
        
        Args:
            payment_id: ID of the payment
            
        Returns:
            Dictionary with payment status or None on error
        """
        if not self.is_configured():
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/payment/{payment_id}",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get payment status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting payment status: {e}")
            return None
    
    def verify_ipn_signature(self, request_data: bytes, signature: str) -> bool:
        """
        Verify IPN callback signature
        
        Args:
            request_data: Raw request body as bytes
            signature: Signature from x-nowpayments-sig header
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.ipn_secret:
            logger.error("IPN secret not configured - IPN verification disabled")
            logger.error("Set NOWPAYMENTS_IPN_SECRET environment variable to enable IPN verification")
            return False
        
        if not signature:
            logger.error("Missing x-nowpayments-sig header")
            return False
        
        try:
            # Calculate expected signature
            expected_signature = hmac.new(
                self.ipn_secret.encode('utf-8'),
                request_data,
                hashlib.sha512
            ).hexdigest()
            
            # Compare signatures
            if hmac.compare_digest(expected_signature, signature):
                logger.info("IPN signature verified successfully")
                return True
            else:
                logger.error("IPN signature verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying IPN signature: {e}")
            return False
    
    def get_estimate_price(self, amount: float, currency_from: str, currency_to: str) -> Optional[Dict[str, Any]]:
        """
        Get estimated price for conversion
        
        Args:
            amount: Amount to convert
            currency_from: Source currency
            currency_to: Target currency
            
        Returns:
            Dictionary with estimated price or None on error
        """
        if not self.is_configured():
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/estimate",
                headers=self._get_headers(),
                params={
                    'amount': amount,
                    'currency_from': currency_from.lower(),
                    'currency_to': currency_to.lower()
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get estimate: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting estimate: {e}")
            return None

# Global instance of NOWPayments manager
nowpayments_manager = NOWPaymentsManager()

