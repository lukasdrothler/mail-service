from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import logging
import os
import smtplib

from src.basemodels import SendMailRequest, TemplateName, BrandingConfig, EmailChangeVerificationContent, ForgotPasswordVerificationContent, EmailVerificationContent

logger = logging.getLogger(__name__)


class MailService:
    def __init__(self):
        if "SMTP_SERVER" in os.environ:
            self.host = os.environ["SMTP_SERVER"]
            logger.info(f"Using SMTP server '{self.host}' from environment variable 'SMTP_SERVER'")
        else:
            self.host = "localhost"
            logger.warning(f"Using SMTP server '{self.host}' since 'SMTP_SERVER' not set")
        
        if "SMTP_PORT" in os.environ:
            self.port = int(os.environ["SMTP_PORT"])
            logger.info(f"Using SMTP port '{self.port}' from environment variable 'SMTP_PORT'")
        else:
            self.port = 587
            logger.warning(f"Using SMTP port '{self.port}' since 'SMTP_PORT' not set")

        if "SMTP_USER" in os.environ:
            self.user = os.environ["SMTP_USER"]
            logger.info(f"Using SMTP user '{self.user}' from environment variable 'SMTP_USER'")
        else:
            logger.error("SMTP_USER environment variable not set, cannot send emails")
            raise ValueError("SMTP_USER environment variable is required for email sending")

        if "SMTP_PASSWORD" in os.environ:
            self.password = os.environ["SMTP_PASSWORD"]
            logger.info("Using SMTP password from environment variable 'SMTP_PASSWORD'")
        else:
            logger.error("SMTP_PASSWORD environment variable not set, cannot send emails")
            raise ValueError("SMTP_PASSWORD environment variable is required for email sending")

    
    def _process_variable_references(self, variables: Dict[str, Any], max_iterations: int = 3) -> Dict[str, Any]:
        """Process variable references within variables (e.g., {app_name} in text)"""
        processed_variables = variables.copy()
        
        for iteration in range(max_iterations):
            changes_made = False
            
            for key, value in processed_variables.items():
                if isinstance(value, str):
                    original_value = value
                    
                    # Replace all variable references in this string
                    for var_key, var_value in processed_variables.items():
                        if var_key != key:  # Don't replace self-references
                            placeholder = f"{{{var_key}}}"
                            if placeholder in value:
                                value = value.replace(placeholder, str(var_value))
                    
                    if value != original_value:
                        processed_variables[key] = value
                        changes_made = True
                elif isinstance(value, dict):
                    # Recursively process nested dictionaries
                    processed_nested = self._process_variable_references(value, max_iterations=1)
                    if processed_nested != value:
                        processed_variables[key] = processed_nested
                        changes_made = True
            
            # If no changes were made in this iteration, we're done
            if not changes_made:
                break
        
        return processed_variables


    def _load_template(self, template_name: str) -> Optional[str]:
        """Load an HTML template file"""
        if "EMAIL_TEMPLATES_DIR" in os.environ:
            _templates_dir = os.environ["EMAIL_TEMPLATES_DIR"]
            logger.info(f"Using email templates directory '{_templates_dir}' from environment variable 'EMAIL_TEMPLATES_DIR'")
        else:
            _templates_dir = os.path.join(os.path.dirname(__file__), "templates")
            logger.info(f"Using default email templates directory since 'EMAIL_TEMPLATES_DIR' not set")
        
        template_path = os.path.join(_templates_dir, f"{template_name}.html")
        if not os.path.exists(template_path):
            logger.warning(f"Template not found: {template_name}")
            return None

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            logger.info(f"Loaded email template: {template_path}")
            return template_content
        except Exception as e:
            logger.error(f"Failed to load template {template_path}: {e}")
            return None


    def _render_template(
            self, template_content: str, variables: Dict[str, Any], branding_config: BrandingConfig
            ) -> str:
        """Render template with variables and configuration"""
        # Merge config with variables (variables override config)
        all_variables = {**branding_config.model_dump(), **variables}
        
        # Process variable references within the merged variables (multiple passes if needed)
        all_variables = self._process_variable_references(all_variables)
        
        # Replace all variables in the template
        for key, value in all_variables.items():
            placeholder = f"{{{{{key}}}}}"
            template_content = template_content.replace(placeholder, str(value))
        
        return template_content


    def send_email_html(self,
                        template_name: str,
                        variables: Dict[str, Any],
                        subject: str,
                        recipient: str,
                        branding_config: BrandingConfig
                        ) -> None:
        """Send email using template system"""
        
        # Load HTML template
        template_content = self._load_template(template_name)
        if not template_content:
            raise ValueError(f"Template '{template_name}' not found")

        html_content = self._render_template(
            template_content=template_content,
            variables=variables,
            branding_config=branding_config
        )
        
        # Create multipart message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.user
        msg['To'] = recipient
        
        # Add HTML version
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        self._send_message(
            msg=msg,
            recipient=recipient
            )
        return None

    def _send_message(
            self, msg, recipient: str,
            ) -> None:
        """Send prepared email message"""
        try:
            # Create SMTP connection
            logger.info(f"Connecting to SMTP server at {self.host}:{self.port}...")
            server = smtplib.SMTP(host=self.host, port=self.port)
            server.starttls()
            server.login(self.user, self.password)
            server.sendmail(self.user, [recipient], msg.as_string())
            server.quit()
            logger.info(f"Successfully sent email to {recipient}")
            
        except OSError as e:
            if e.errno == 101: # Network is unreachable
                logger.critical(f"NETWORK ERROR: Cannot reach SMTP server {self.host}:{self.port}. "
                                f"Check Kubernetes egress policies or DNS settings. Error: {e}")
            elif e.errno == 111: # Connection refused
                logger.critical(f"CONNECTION REFUSED: SMTP server {self.host}:{self.port} refused connection. "
                                f"Check if the server is running and port is correct. Error: {e}")
            else:
                logger.error(f"OS Error during email sending: {e}")
            raise RuntimeError(f"Network/OS error sending email to {recipient}: {e}") from e
            
        except Exception as e:
            error_message = f"Failed to send email to {recipient}: {e}"
            logger.error(error_message)
            logger.error(f"Parameters: host={self.host}, port={self.port}, user={self.user}")
            raise RuntimeError(error_message) from e


    def send_email_plain_text(self, content, subject, recipient: str):
        """Send plain text email (backward compatibility)"""
        try:
            msg = MIMEText(content, 'plain', 'utf-8')
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = recipient
            
            self._send_message(
                msg=msg,
                recipient=recipient,
            )
            
        except Exception as e:
            logger.error(f"Failed to create or send plain text email: {e}")
            raise


    def send_email_verification_mail(self, request: SendMailRequest):
        """Send email verification mail"""
        template_variables = EmailVerificationContent(**request.email_content)

        # Convert BaseModel to dict and merge with dynamic variables
        variables = {
            **template_variables.model_dump(),
            "username": request.username,
            "verification_code": request.verification_code
        }
        
        self.send_email_html(
            template_name=TemplateName.EMAIL_VERIFICATION,
            variables=variables,
            subject=f"Dein Code lautet {request.verification_code}",
            recipient=request.recipient,
            branding_config=request.branding_config
        )


    def send_email_change_verification_mail(
            self,
            username: str,
            recipient: str,
            verification_code: str,
            email_content: EmailChangeVerificationContent,
            subject: str,
            branding_config: BrandingConfig
            ):
        """Send email change verification mail"""
        # Convert BaseModel to dict and merge with dynamic variables
        variables = {
            **email_content.model_dump(),
            "username": username,
            "verification_code": verification_code
        }
        
        self.send_email_html(
            template_name="email_change_verification",
            variables=variables,
            subject=subject,
            recipient=recipient,
            branding_config=branding_config
        )

    def send_forgot_password_verification_mail(
            self,
            username: str,
            recipient: str,
            verification_code: str,
            email_content: ForgotPasswordVerificationContent,
            subject: str,
            branding_config: BrandingConfig
            ):
        """Send forgot password verification mail"""
        # Convert BaseModel to dict and merge with dynamic variables
        variables = {
            **email_content.model_dump(),
            "username": username,
            "verification_code": verification_code
        }
        
        self.send_email_html(
            template_name="forgot_password_verification",
            variables=variables,
            subject=subject,
            recipient=recipient,
            branding_config=branding_config
        )