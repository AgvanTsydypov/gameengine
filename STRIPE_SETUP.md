# Stripe Payment Links Integration Setup

This guide will help you set up Stripe Payment Links for the GlitchPeachAI credit top-up system.

## Prerequisites

1. A Stripe account (create one at https://stripe.com)
2. Your Flask application running

## Step 1: Get Stripe API Keys

1. Log in to your Stripe Dashboard
2. Go to **Developers** > **API Keys**
3. Copy your **Publishable key** and **Secret key**

## Step 2: Configure Environment Variables

Add these variables to your `.env` file:

```env
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

**Important:** 
- Use `pk_test_` and `sk_test_` for testing
- Use `pk_live_` and `sk_live_` for production
- Never commit your secret keys to version control

## Step 3: Create Products and Prices in Stripe

1. Go to **Products** in your Stripe Dashboard
2. Create 3 products for each credit package:

### Starter Pack (50 Credits - $5.00)
- Product name: "Starter Pack - 50 Credits"
- Price: $5.00 USD (one-time)
- Copy the **Price ID** (starts with `price_`)

### Creator Pack (120 Credits - $10.00)
- Product name: "Creator Pack - 120 Credits"
- Price: $10.00 USD (one-time)
- Copy the **Price ID** (starts with `price_`)

### Pro Pack (300 Credits - $20.00)
- Product name: "Pro Pack - 300 Credits"
- Price: $20.00 USD (one-time)
- Copy the **Price ID** (starts with `price_`)

## Step 4: Create Payment Links

1. Go to **Payment Links** in your Stripe Dashboard
2. Click **Create payment link**
3. For each product:
   - Select the product and price
   - Set success URL: `https://yourdomain.com/payment?success=true`
   - Set cancel URL: `https://yourdomain.com/payment`
   - Copy the **Payment Link URL** (starts with `https://buy.stripe.com/`)

## Step 5: Update Payment Link URLs

Update the `payment_link_url` values in `app.py` with your actual Payment Link URLs:

```python
credit_packages = [
    {
        'credits': 50, 
        'price': 5.00, 
        'name': 'Starter Pack', 
        'payment_link_url': 'https://buy.stripe.com/your_starter_pack_link'
    },
    # ... etc
]
```

## Step 6: Set Up Webhooks (Required for Credit Addition)

Webhooks automatically add credits to user accounts when payments succeed.

1. In Stripe Dashboard, go to **Developers** > **Webhooks**
2. Click **Add endpoint**
3. Set the endpoint URL to: `https://yourdomain.com/stripe_webhook`
4. Select events: `checkout.session.completed`
5. Copy the webhook signing secret to your `.env` file

## Step 7: Test the Integration

1. Start your Flask application
2. Log in to your account
3. Go to the **TOP UP** page
4. Click "Buy Now" on any package
5. Complete the payment using Stripe's test card numbers:
   - **Success:** 4242 4242 4242 4242
   - **Decline:** 4000 0000 0000 0002
   - **Requires authentication:** 4000 0025 0000 3155

## Credit Packages

The system includes these pre-configured packages:

| Package | Credits | Price | Price/Credit | Description |
|---------|---------|-------|--------------|-------------|
| Starter Pack | 50 | $5.00 | $0.10 | Perfect for trying out AI game generation |
| Creator Pack | 120 | $10.00 | $0.083 | Great for regular game creators (Most Popular) |
| Pro Pack | 300 | $20.00 | $0.067 | Best value for serious game developers |

## Security Notes

1. **Never expose secret keys** in client-side code
2. **Always verify webhook signatures** before processing
3. **Use HTTPS** in production
4. **Validate payment amounts** server-side
5. **Log all payment events** for debugging

## Troubleshooting

### Payment Intent Creation Fails
- Check that `STRIPE_SECRET_KEY` is set correctly
- Verify the key starts with `sk_test_` or `sk_live_`
- Check Flask logs for detailed error messages

### Webhook Not Working
- Verify `STRIPE_WEBHOOK_SECRET` is set correctly
- Check that the webhook URL is accessible
- Ensure the webhook endpoint is receiving POST requests
- Check Stripe Dashboard for webhook delivery logs

### Credits Not Added After Payment
- Check webhook configuration
- Verify the webhook is receiving `payment_intent.succeeded` events
- Check that the payment intent metadata contains correct user_id and credits
- Review Flask logs for webhook processing errors

## Production Deployment

1. **Switch to live keys** in your production environment
2. **Update webhook URL** to your production domain
3. **Test thoroughly** with small amounts first
4. **Monitor webhook delivery** in Stripe Dashboard
5. **Set up proper logging** for payment events

## Support

For Stripe-specific issues, consult:
- [Stripe Documentation](https://stripe.com/docs)
- [Stripe Support](https://support.stripe.com)

For application-specific issues, check the Flask logs and ensure all environment variables are properly configured.
