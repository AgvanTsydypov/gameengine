-- Create table to track processed payments and prevent duplicate credit additions
CREATE TABLE IF NOT EXISTS processed_payments (
    id SERIAL PRIMARY KEY,
    order_id TEXT UNIQUE NOT NULL,
    payment_id TEXT,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    credits_added INTEGER,
    amount_paid DECIMAL(10,2),
    currency TEXT,
    payment_type TEXT DEFAULT 'nowpayments', -- 'stripe' or 'nowpayments'
    stripe_session_id TEXT, -- For Stripe payments
    customer_email TEXT, -- For Stripe payments
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_processed_payments_order_id ON processed_payments(order_id);
CREATE INDEX IF NOT EXISTS idx_processed_payments_payment_id ON processed_payments(payment_id);
CREATE INDEX IF NOT EXISTS idx_processed_payments_user_id ON processed_payments(user_id);
CREATE INDEX IF NOT EXISTS idx_processed_payments_processed_at ON processed_payments(processed_at);
CREATE INDEX IF NOT EXISTS idx_processed_payments_payment_type ON processed_payments(payment_type);
CREATE INDEX IF NOT EXISTS idx_processed_payments_stripe_session_id ON processed_payments(stripe_session_id);

-- Add RLS (Row Level Security) policy
ALTER TABLE processed_payments ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own processed payments
CREATE POLICY "Users can view their own processed payments" ON processed_payments
    FOR SELECT USING (auth.uid() = user_id);

-- Policy: Service role can do everything (for webhooks and admin)
CREATE POLICY "Service role can manage all processed payments" ON processed_payments
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
