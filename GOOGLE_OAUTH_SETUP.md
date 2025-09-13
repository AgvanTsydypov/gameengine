# Google OAuth Setup Guide

This guide explains how to configure Google OAuth authentication with Supabase for your Flask app.

## Prerequisites

1. You need to have Google OAuth credentials already set up in your Supabase project (as mentioned, this is already done)
2. Your Supabase project should have Google as an OAuth provider enabled

## What Was Added

### 1. Flask Routes

Two new routes were added to `app.py`:

- **`/auth/google`** - Initiates the Google OAuth flow
- **`/auth/google/callback`** - Handles the OAuth callback from Google

### 2. UI Updates

Google sign-in/sign-up buttons were added to:

- **Login page** (`/login`) - "Войти через Google" button
- **Register page** (`/register`) - "Зарегистрироваться через Google" button  
- **Login modal** (in header) - Google sign-in button
- **Register modal** (in header) - Google sign-up button

### 3. Font Awesome Integration

Font Awesome 6.4.0 was added to the base template to support Google icons.

## How It Works

1. **User clicks Google button** → Redirects to `/auth/google`
2. **Flask initiates OAuth** → Creates Supabase OAuth URL and redirects user to Google
3. **User authenticates with Google** → Google redirects back to `/auth/google/callback`
4. **Flask processes callback** → Extracts user info from JWT token and creates/updates user session
5. **User is logged in** → Redirected to homepage with success message

## User Experience

- **New users**: Google authentication automatically creates a new user account with 2 free credits
- **Existing users**: Google authentication logs them in using their existing account
- **Seamless integration**: Works alongside existing email/password authentication

## Configuration Notes

The following redirect URLs should be configured in your Supabase project:

- **Development**: `http://localhost:8888/auth/google/callback`
- **Production**: `https://yourdomain.com/auth/google/callback`

## Testing

To test the Google OAuth integration:

1. Start your Flask app
2. Go to `/login` or `/register`
3. Click the "Войти через Google" or "Зарегистрироваться через Google" button
4. Complete the Google authentication flow
5. Verify you're logged in and redirected to the homepage

## Error Handling

The implementation includes comprehensive error handling:

- Invalid tokens are rejected with user-friendly error messages
- Network errors are logged and users are redirected to login
- JWT parsing errors are handled gracefully
- Missing user data is handled appropriately

## Security Considerations

- JWT tokens are validated before processing
- User sessions are properly managed
- Redirect URLs are validated against configured domains
- Error messages don't expose sensitive information

## Files Modified

- `app.py` - Added OAuth routes
- `templates/login.html` - Added Google sign-in button
- `templates/register.html` - Added Google sign-up button  
- `templates/base.html` - Added Font Awesome and updated modals

The Google OAuth integration is now ready to use!
