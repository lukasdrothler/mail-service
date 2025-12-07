from pydantic import BaseModel

class SendMailRequest(BaseModel):
    template_name: str
    username: str
    verification_code: str
    recipient: str


class TemplateName():
    EMAIL_VERIFICATION = "email_verification"
    EMAIL_CHANGE_VERIFICATION = "email_change_verification"
    FORGOT_PASSWORD_VERIFICATION = "forgot_password_verification"  # nosec