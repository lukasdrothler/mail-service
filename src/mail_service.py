from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import logging
import os
import smtplib
import json

from src.basemodels import MailRequest, TemplateName

logger = logging.getLogger(__name__)


class MailService:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        # SMTP Configuration
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

        # Branding Configuration
        self.branding_config = {}
        
        if "APP_NAME" in os.environ:
            self.branding_config["app_name"] = os.environ["APP_NAME"]
        else:
            raise ValueError("APP_NAME environment variable is required")

        if "APP_OWNER" in os.environ:
            self.branding_config["app_owner"] = os.environ["APP_OWNER"]
        else:
            raise ValueError("APP_OWNER environment variable is required")

        if "CONTACT_EMAIL" in os.environ:
            self.branding_config["contact_email"] = os.environ["CONTACT_EMAIL"]
        else:
            raise ValueError("CONTACT_EMAIL environment variable is required")

        self.branding_config["logo_url"] = os.environ.get("LOGO_URL", "")
        self.branding_config["primary_color"] = os.environ.get("PRIMARY_COLOR", "#000000")
        self.branding_config["primary_shade_color"] = os.environ.get("PRIMARY_SHADE_COLOR", "#000000")
        self.branding_config["primary_foreground_color"] = os.environ.get("PRIMARY_FOREGROUND_COLOR", "#ffffff")
        
        logger.info(f"Branding configuration loaded for app: {self.branding_config['app_name']}")

    
    def process_variable_references(self, variables: Dict[str, Any], max_iterations: int = 3, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process variable references within variables (e.g., {app_name} in text)"""
        processed_variables = variables.copy()
        
        for iteration in range(max_iterations):
            changes_made = False
            
            # Create lookup dictionary combining context and current variables
            lookup_vars = context.copy() if context else {}
            lookup_vars.update(processed_variables)
            
            for key, value in processed_variables.items():
                if isinstance(value, str):
                    original_value = value
                    
                    # Replace all variable references in this string
                    for var_key, var_value in lookup_vars.items():
                        if var_key != key:  # Don't replace self-references
                            placeholder = f"{{{var_key}}}"
                            if placeholder in value:
                                value = value.replace(placeholder, str(var_value))
                    
                    if value != original_value:
                        processed_variables[key] = value
                        changes_made = True
                elif isinstance(value, dict):
                    # Recursively process nested dictionaries
                    processed_nested = self.process_variable_references(value, max_iterations=1, context=lookup_vars)
                    if processed_nested != value:
                        processed_variables[key] = processed_nested
                        changes_made = True
            
            # If no changes were made in this iteration, we're done
            if not changes_made:
                break
        
        return processed_variables


    def load_template(self, template_name: str) -> Optional[str]:
        """Load an HTML template file"""
        # Check custom directory first
        if "EMAIL_TEMPLATES_DIR" in os.environ:
            custom_dir = os.environ["EMAIL_TEMPLATES_DIR"]
            custom_path = os.path.join(custom_dir, f"{template_name}.html")
            if os.path.exists(custom_path):
                logger.info(f"Using custom email template: {custom_path}")
                try:
                    with open(custom_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    logger.error(f"Failed to load custom template {custom_path}: {e}")
        
        # Default directory
        default_dir = os.path.join(os.path.dirname(__file__), "templates")
        default_path = os.path.join(default_dir, f"{template_name}.html")
        
        if not os.path.exists(default_path):
            logger.warning(f"Template not found: {template_name}")
            return None

        try:
            with open(default_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            logger.info(f"Loaded default email template: {default_path}")
            return template_content
        except Exception as e:
            logger.error(f"Failed to load template {default_path}: {e}")
            return None


    def load_template_values(self, template_name: str) -> Dict[str, Any]:
        """Load default content from JSON file"""
        default_dir = os.path.join(os.path.dirname(__file__), "templates")
        default_json_path = os.path.join(default_dir, f"{template_name}.json")
        
        values = {}
        if os.path.exists(default_json_path):
            try:
                with open(default_json_path, 'r', encoding='utf-8') as f:
                    values = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load default template defaults {default_json_path}: {e}")
        
        # Check custom directory and merge
        if "EMAIL_TEMPLATES_DIR" in os.environ:
            custom_dir = os.environ["EMAIL_TEMPLATES_DIR"]
            custom_json_path = os.path.join(custom_dir, f"{template_name}.json")
            if os.path.exists(custom_json_path):
                try:
                    with open(custom_json_path, 'r', encoding='utf-8') as f:
                        custom_values = json.load(f)
                        values.update(custom_values)
                        logger.info(f"Merged custom template defaults from {custom_json_path}")
                except Exception as e:
                    logger.error(f"Failed to load custom template defaults {custom_json_path}: {e}")
        
        return values


    def render_template(
            self, template_content: str, variables: Dict[str, Any]
            ) -> str:
        """Render template with variables and configuration"""
        # Merge config with variables (variables override config)
        all_variables = {**self.branding_config, **variables}
        
        # Process variable references within the merged variables (multiple passes if needed)
        all_variables = self.process_variable_references(all_variables)
        
        # Replace all variables in the template
        for key, value in all_variables.items():
            placeholder = f"{{{{{key}}}}}"
            template_content = template_content.replace(placeholder, str(value))
        
        return template_content


    def send_email_html(self,
                        template_name: str,
                        variables: Dict[str, Any],
                        subject: str,
                        recipient: str
                        ) -> None:
        """Send email using template system"""
        
        # Load HTML template
        template_content = self.load_template(template_name)
        if not template_content:
            raise ValueError(f"Template '{template_name}' not found")

        html_content = self.render_template(
            template_content=template_content,
            variables=variables
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
            self, msg, recipient: str
            ) -> None:
        """Send prepared email message"""
        if self.dry_run:
            logger.info(f"Dry run enabled - not sending email to {recipient}")
            return
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


    def send_code_mail(self, request: MailRequest, template_name: TemplateName):
        """Send verification code mail"""
        if not request.verification_code:
            raise ValueError("Verification code is required for code mail")

        # Load default template values
        values = self.load_template_values(template_name)

        # Merge defaults with request content and dynamic variables
        variables = {
            **values,
            "username": request.username,
            "verification_code": request.verification_code
        }
        
        self.send_email_html(
            template_name=template_name,
            variables=variables,
            subject=f"Your code is {request.verification_code}",
            recipient=request.recipient
        )

    def send_custom_template_mail(self, request: MailRequest, template_name: str):
        """Send email using a custom template"""
        # Load default template values
        values = self.load_template_values(template_name)

        # Merge defaults with request content
        variables = {
            **values,
            "username": request.username
        }

        if request.subject:
            _subject = request.subject
        else:
            _subject = "No Subject"

        self.send_email_html(
            template_name=template_name,
            variables=variables,
            subject=_subject,
            recipient=request.recipient
        )