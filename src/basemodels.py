from pydantic import BaseModel
from typing import Optional

class MailRequest(BaseModel):
    template_name: str
    username: str
    recipient: str
    verification_code: Optional[str] = None
    subject: Optional[str] = None

# TODO: Implement notification mail to old email if email was changed
class TemplateName():
    EMAIL_VERIFICATION = "email_verification"
    EMAIL_CHANGE_VERIFICATION = "email_change_verification"
    FORGOT_PASSWORD_VERIFICATION = "forgot_password_verification"  # nosec