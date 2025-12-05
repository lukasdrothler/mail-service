from pydantic import BaseModel
from typing import Optional


class EmailVerificationContent(BaseModel):
    """Content for email verification template"""
    language: Optional[str] = "en"
    welcome_title: Optional[str] = "Welcome {username}! 🎉"
    welcome_message: Optional[str] = "Thanks for your interest in my app! I'm excited to have you on board. Please verify your email with the code below to unlock all the amazing features."
    verification_code_label: Optional[str] = "Your Verification Code"
    expiration_message: Optional[str] = "This code will expire in 24 hours."
    feature_preview_title: Optional[str] = "🎯 What awaits you:"
    feature_1: Optional[str] = "✨ Powerful tool designed for your success"
    feature_2: Optional[str] = "🔐 Bank-level security for your peace of mind"
    feature_3: Optional[str] = "📱 Seamless experience across all devices"
    feature_4: Optional[str] = "🚀 Regular updates with new features"
    warning_title: Optional[str] = "⚠️ Security Notice"
    warning_message: Optional[str] = "Never share this code with anyone. We will never ask for your verification code."
    wasnt_you_title: Optional[str] = "Didn't sign up?"
    wasnt_you_message: Optional[str] = "If you didn't create this account, no worries! Just ignore this email and nothing will happen."
    excitement_message: Optional[str] = "I can't wait for you to explore everything {app_name} has to offer. Let's get started!"
    support_message: Optional[str] = "Need help? Contact us at {contact_email}"
    personal_note: Optional[str] = "Thanks for being part of our community! 🎉"


class EmailChangeVerificationContent(BaseModel):
    """Content for email change verification template"""
    language: Optional[str] = "en"
    title: Optional[str] = "Email Change Verification"
    greeting: Optional[str] = "Hello {username}!"
    main_message: Optional[str] = "We received a request to change your email address. Please verify this change with the code below."
    verification_code_label: Optional[str] = "Your Verification Code"
    expiration_message: Optional[str] = "This code will expire in 24 hours."
    warning_title: Optional[str] = "⚠️ Security Notice"
    warning_message: Optional[str] = "Never share this code with anyone. We will never ask for your verification code."
    wasnt_you_title: Optional[str] = "Didn't request this?"
    wasnt_you_message: Optional[str] = "If you didn't request this email change, please secure your account immediately and contact our support team."
    support_message: Optional[str] = "Need help? Contact us at {contact_email}"
    personal_note: Optional[str] = "Thanks for being part of our community! 🎉"


class ForgotPasswordVerificationContent(BaseModel):
    """Content for forgot password verification template"""
    language: Optional[str] = "en"
    title: Optional[str] = "Password Reset Request"
    greeting: Optional[str] = "Hello {username}!"
    main_message: Optional[str] = "We received a request to reset your password. Use the code below to proceed with resetting your password."
    verification_code_label: Optional[str] = "Your Verification Code"
    expiration_message: Optional[str] = "This code will expire in 24 hours."
    warning_title: Optional[str] = "⚠️ Security Notice"
    warning_message: Optional[str] = "Never share this code with anyone. We will never ask for your verification code."
    wasnt_you_title: Optional[str] = "Didn't request this?"
    wasnt_you_message: Optional[str] = "If you didn't request a password reset, please secure your account immediately and contact our support team."
    support_message: Optional[str] = "Need help? Contact us at {contact_email}"
    personal_note: Optional[str] = "Thanks for being part of our community! 🎉"


class BrandingConfig(BaseModel):
    app_name: str
    app_owner: str
    contact_email: str
    logo_url: Optional[str]=""
    primary_color: Optional[str]="#000000"
    primary_shade_color: Optional[str]="#000000"
    primary_foreground_color: Optional[str]="#ffffff"


class SendMailRequest(BaseModel):
    template_name: str
    username: str
    verification_code: str
    recipient: str
    branding_config: BrandingConfig
    email_content: dict


class TemplateName():
    EMAIL_VERIFICATION = "email_verification"
    EMAIL_CHANGE_VERIFICATION = "email_change_verification"
    FORGOT_PASSWORD_VERIFICATION = "forgot_password_verification"