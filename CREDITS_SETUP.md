# Credits System Setup Guide

This guide explains how to set up the credits system for your AI Game Studio application.

## Overview

The credits system allows users to:
- Start with 2 credits upon registration
- View their current credits on the my-games page
- Have credits managed through the database

## Database Setup

### Step 1: Run the SQL Schema

1. Go to your Supabase dashboard
2. Navigate to the SQL Editor
3. Copy and paste the contents of `credits_schema.sql`
4. Execute the SQL to create the credits table and related functions

### Step 2: Verify the Setup

The SQL will create:
- `user_credits` table with proper RLS policies
- Automatic trigger to create credits record when users register
- Functions for managing credits

## Features Implemented

### 1. Database Schema
- `user_credits` table with user_id, credits, and timestamps
- Row Level Security (RLS) policies for data protection
- Automatic credits creation trigger for new users

### 2. Backend API
- `get_user_credits(user_id)` - Get current credits
- `create_user_credits_record(user_id, initial_credits)` - Create credits record
- `update_user_credits(user_id, new_credits)` - Update credits
- `deduct_credits(user_id, amount)` - Deduct credits with validation
- `add_credits(user_id, amount)` - Add credits

### 3. Frontend Display
- Credits display on my-games page
- Styled with cyber theme matching the app
- Animated coin icon with pulse effect

### 4. Registration Integration
- New users automatically get 2 credits
- Fallback mechanism if trigger doesn't work

## API Endpoints

### GET /api/user-credits
Returns the current user's credits count.

**Response:**
```json
{
  "success": true,
  "credits": 2
}
```

## Testing

Run the test script to verify everything works:

```bash
python test_credits.py
```

This will test:
- Credits record creation
- Getting user credits
- Adding credits
- Deducting credits
- Insufficient credits validation

## Usage Examples

### In Python Code
```python
from supabase_client import supabase_manager

# Get user credits
credits = supabase_manager.get_user_credits("user-id")

# Add credits
supabase_manager.add_credits("user-id", 5)

# Deduct credits (with validation)
success = supabase_manager.deduct_credits("user-id", 1)
```

### In JavaScript (Frontend)
```javascript
// Get user credits via API
fetch('/api/user-credits')
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log('User has', data.credits, 'credits');
    }
  });
```

## Troubleshooting

### Credits Not Showing
1. Check if the `user_credits` table exists in Supabase
2. Verify RLS policies are set up correctly
3. Check Supabase service role key configuration

### New Users Not Getting Credits
1. Verify the trigger function is created
2. Check if the trigger is enabled on `auth.users` table
3. Check application logs for errors

### Database Connection Issues
1. Verify `SUPABASE_SERVICE_ROLE_KEY` is set in your `.env` file
2. Check Supabase URL and key configuration
3. Run the test script to diagnose issues

## Security Notes

- Credits are protected by Row Level Security (RLS)
- Users can only see their own credits
- Service role is required for server-side operations
- All credit operations are logged for audit purposes

## Future Enhancements

Potential features to add:
- Credits purchase system with Stripe integration
- Credits usage for premium features
- Credits history/transaction log
- Admin panel for credits management
- Credits expiration system
