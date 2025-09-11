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
        
        # Create payment link
        payment_link = stripe.PaymentLink.create(
            line_items=[{
                'price': price.id,
                'quantity': 1,
            }],
        )
        print(f"✅ Payment Link created: {payment_link.url}")
        
        payment_links.append({
            'name': package['name'],
            'credits': package['credits'],
            'price': package['price'] / 100,
            'payment_link_url': payment_link.url
        })
    
    return payment_links

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
    print("DON'T FORGET TO:")
    print("1. Set up webhooks for checkout.session.completed")
    print("2. Test the integration with test cards")
    print("3. Update success/cancel URLs in Stripe Dashboard if needed")
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
        
    except stripe.error.StripeError as e:
        print(f"❌ Stripe error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
