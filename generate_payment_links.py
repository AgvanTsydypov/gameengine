#!/usr/bin/env python3
"""
Script to generate Stripe Payment Links for credit packages
Run this script to create Payment Links and get the URLs to update in app.py
"""

import os
import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def create_products_and_prices():
    """Create products and prices in Stripe"""
    
    # Define credit packages
    packages = [
        {
            'name': 'Mini Pack - 6 Credits',
            'description': 'Great for testing a few games',
            'price': 100,  # $1.00 in cents
            'credits': 6
        },
        {
            'name': 'Starter Pack - 50 Credits',
            'description': 'Perfect for trying out our AI game generation',
            'price': 500,  # $5.00 in cents
            'credits': 50
        },
        {
            'name': 'Creator Pack - 120 Credits', 
            'description': 'Great for regular game creators',
            'price': 1000,  # $10.00 in cents
            'credits': 120
        },
        {
            'name': 'Pro Pack - 300 Credits',
            'description': 'Best value for serious game developers', 
            'price': 2000,  # $20.00 in cents
            'credits': 300
        }
    ]
    
    payment_links = []
    
    for package in packages:
        print(f"\nCreating product: {package['name']}")
        
        # Create product
        product = stripe.Product.create(
            name=package['name'],
            description=package['description']
        )
        print(f"✅ Product created: {product.id}")
        
        # Create price
        price = stripe.Price.create(
            product=product.id,
            unit_amount=package['price'],
            currency='usd',
        )
        print(f"✅ Price created: {price.id}")
        
        # Create payment link with redirect URLs
        base_url = os.getenv('BASE_URL', 'http://localhost:8888')
        payment_link = stripe.PaymentLink.create(
            line_items=[{
                'price': price.id,
                'quantity': 1,
            }],
            after_completion={
                'type': 'redirect',
                'redirect': {
                    'url': f'{base_url}/payment_success'
                }
            },
            # Note: Stripe Payment Links don't support cancel URLs directly
            # Users can manually return via browser back button or close tab
        )
        print(f"✅ Payment Link created: {payment_link.url}")
        
        payment_links.append({
            'name': package['name'],
            'credits': package['credits'],
            'price': package['price'] / 100,
            'payment_link_url': payment_link.url
        })
    
    return payment_links

def cleanup_old_products():
    """Helper function to list and optionally delete old products"""
    print("\n" + "="*60)
    print("🧹 CLEANUP OLD PRODUCTS (Optional)")
    print("="*60)
    print("If you want to clean up old products, run this in Python shell:")
    print("""
import stripe
import os
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# List all products
products = stripe.Product.list(limit=20)
for product in products.data:
    if 'Pack' in product.name:  # Only credit pack products
        print(f"Product: {product.name} (ID: {product.id})")
        
        # To delete a specific product (uncomment and modify):
        # stripe.Product.modify(product.id, active=False)
        # print(f"Deactivated: {product.name}")
""")

def show_app_update_instructions(payment_links):
    """Show instructions for updating app.py with new payment links"""
    print("\n" + "="*60)
    print("🔄 NEXT STEPS:")
    print("="*60)
    print("1. Copy the credit_packages array above")
    print("2. Replace the existing credit_packages in app.py")
    print("3. Restart your Flask application")
    print("")
    print("⚠️  IMPORTANT: The new Payment Links include redirect URLs:")
    
    for package in payment_links:
        print(f"   - {package['name']}: Redirects to your BASE_URL/payment_success")
    
    print("")
    print("🌍 Environment-specific URLs:")
    print("   - Development: http://localhost:8888/payment_success")
    print("   - Production: https://glitchpeach.com/payment_success")
    print("="*60)

def print_app_config(payment_links):
    """Print the configuration to update in app.py"""
    
    print("\n" + "="*60)
    print("UPDATE YOUR APP.PY WITH THESE PAYMENT LINK URLs:")
    print("="*60)
    
    print("\nReplace the credit_packages in app.py with:")
    print("credit_packages = [")
    
    for i, link in enumerate(payment_links):
        package_name = link['name'].split(' - ')[0]  # Remove credits part
        credits = link['credits']
        price = link['price']
        price_per_credit = price / credits
        
        print(f"    {{")
        print(f"        'credits': {credits},")
        print(f"        'price': {price:.2f},")
        print(f"        'price_cents': {int(price * 100)},")
        print(f"        'name': '{package_name}',")
        print(f"        'description': '...',")
        print(f"        'price_per_credit': {price_per_credit:.3f},")
        print(f"        'payment_link_url': '{link['payment_link_url']}'")
        if i < len(payment_links) - 1:
            print(f"    }},")
        else:
            print(f"    }}")
    
    print("]")
    
    print("\n" + "="*60)
    print("IMPORTANT SETUP STEPS:")
    print("="*60)
    print("1. Set BASE_URL in your .env file:")
    print("   BASE_URL=https://your-domain.com (for production)")
    print("   BASE_URL=http://localhost:8888 (for development)")
    print("")
    print("2. Set up webhooks for checkout.session.completed:")
    print("   - Webhook URL: https://your-domain.com/stripe_webhook")
    print("   - Add STRIPE_WEBHOOK_SECRET to .env file")
    print("")
    print("3. Test the integration with test cards:")
    print("   - 4242 4242 4242 4242 (Visa)")
    print("   - Any future expiry date and 3-digit CVC")
    print("")
    print("4. Payment flow:")
    print("   - User clicks 'Buy' → Stripe Payment Link")
    print("   - After payment → Redirects to /payment_success")
    print("   - Success page → Shows updated credits & redirects to /payment")
    print("="*60)

if __name__ == "__main__":
    if not stripe.api_key:
        print("❌ Error: STRIPE_SECRET_KEY not found in environment variables")
        print("Please add your Stripe secret key to .env file")
        exit(1)
    
    try:
        print("🚀 Creating Stripe products, prices, and payment links...")
        payment_links = create_products_and_prices()
        print_app_config(payment_links)
        show_app_update_instructions(payment_links)
        cleanup_old_products()
        
    except stripe.error.StripeError as e:
        print(f"❌ Stripe error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
