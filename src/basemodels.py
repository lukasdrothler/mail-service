from pydantic import BaseModel
from typing import Optional


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


class TemplateName():
    EMAIL_VERIFICATION = "email_verification"
    EMAIL_CHANGE_VERIFICATION = "email_change_verification"
    FORGOT_PASSWORD_VERIFICATION = "forgot_password_verification"  # nosec