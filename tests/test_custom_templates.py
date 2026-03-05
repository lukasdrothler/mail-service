import pytest
import os
import json
import tempfile
import shutil
from src.mail_service import MailService

@pytest.fixture
def custom_templates_dir():
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Set required env vars for MailService
    os.environ["SMTP_USER"] = "testuser"
    os.environ["SMTP_PASSWORD"] = "testpass"
    os.environ["APP_NAME"] = "TestApp"
    os.environ["APP_OWNER"] = "TestOwner"
    os.environ["CONTACT_EMAIL"] = "test@example.com"
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)
    del os.environ["SMTP_USER"]
    del os.environ["SMTP_PASSWORD"]
    del os.environ["APP_NAME"]
    del os.environ["APP_OWNER"]
    del os.environ["CONTACT_EMAIL"]

def test_load_custom_html_template(custom_templates_dir):
    # Create a custom HTML template
    template_name = "custom_test"
    template_content = "<h1>Custom Template</h1>"
    with open(os.path.join(custom_templates_dir, f"{template_name}.html"), "w") as f:
        f.write(template_content)
    
    # Set environment variable
    os.environ["EMAIL_TEMPLATES_DIR"] = custom_templates_dir
    
    try:
        service = MailService()
        loaded_content = service.load_template(template_name)
        assert loaded_content == template_content
    finally:
        del os.environ["EMAIL_TEMPLATES_DIR"]

def test_load_custom_json_values_merge(custom_templates_dir):
    # Create a custom JSON default file
    template_name = "email_verification"
    custom_defaults = {
        "en": {
            "welcome_title": "Custom Welcome Title",
            "new_field": "New Value"
        }
    }
    with open(os.path.join(custom_templates_dir, f"{template_name}.json"), "w") as f:
        json.dump(custom_defaults, f)
    
    # Set environment variable
    os.environ["EMAIL_TEMPLATES_DIR"] = custom_templates_dir
    
    try:
        service = MailService()
        defaults = service.load_template_values(template_name)
        
        # Check if custom values are present
        assert defaults["welcome_title"] == "Custom Welcome Title"
        assert defaults["new_field"] == "New Value"
        
        # Check if original values are preserved (assuming email_verification.json exists in default dir)
        assert "verification_code_label" in defaults
        assert defaults["verification_code_label"] == "Your Verification Code"
        
    finally:
        del os.environ["EMAIL_TEMPLATES_DIR"]

def test_load_custom_html_override_default(custom_templates_dir):
    # Create a custom HTML template with same name as default
    template_name = "email_verification"
    template_content = "<h1>Custom Verification</h1>"
    with open(os.path.join(custom_templates_dir, f"{template_name}.html"), "w") as f:
        f.write(template_content)
    
    # Set environment variable
    os.environ["EMAIL_TEMPLATES_DIR"] = custom_templates_dir
    
    try:
        service = MailService()
        loaded_content = service.load_template(template_name)
        assert loaded_content == template_content
        assert "Custom Verification" in loaded_content
    finally:
        del os.environ["EMAIL_TEMPLATES_DIR"]

def test_load_custom_json_values_language_fallback(custom_templates_dir):
    # Create a custom JSON default file only with 'en'
    template_name = "email_fallback_test"
    custom_defaults = {
        "en": {
            "title": "English Title"
        }
    }
    with open(os.path.join(custom_templates_dir, f"{template_name}.json"), "w") as f:
        json.dump(custom_defaults, f)
    
    os.environ["EMAIL_TEMPLATES_DIR"] = custom_templates_dir
    
    try:
        service = MailService()
        # Requesting 'fr' which doesn't exist, should fallback to 'en'
        defaults = service.load_template_values(template_name, language="fr")
        
        assert defaults["title"] == "English Title"
        assert defaults["language"] == "fr" # The requested language is still set in return
        
    finally:
        del os.environ["EMAIL_TEMPLATES_DIR"]

def test_load_custom_json_values_specific_language(custom_templates_dir):
    # Create a custom JSON default file with 'en' and 'de'
    template_name = "email_lang_test"
    custom_defaults = {
        "en": {
            "title": "English Title"
        },
        "de": {
            "title": "German Title"
        }
    }
    with open(os.path.join(custom_templates_dir, f"{template_name}.json"), "w") as f:
        json.dump(custom_defaults, f)
    
    os.environ["EMAIL_TEMPLATES_DIR"] = custom_templates_dir
    
    try:
        service = MailService()
        
        # Requesting 'de'
        defaults_de = service.load_template_values(template_name, language="de")
        assert defaults_de["title"] == "German Title"
        
        # Requesting 'en'
        defaults_en = service.load_template_values(template_name, language="en")
        assert defaults_en["title"] == "English Title"
        
    finally:
        del os.environ["EMAIL_TEMPLATES_DIR"]

def test_load_custom_json_invalid_json(custom_templates_dir):
    template_name = "invalid_json_test"
    with open(os.path.join(custom_templates_dir, f"{template_name}.json"), "w") as f:
        f.write("{invalid_json}")
    
    os.environ["EMAIL_TEMPLATES_DIR"] = custom_templates_dir
    
    try:
        service = MailService()
        defaults = service.load_template_values(template_name)
        # Should return empty dict (plus language key) and log error, not crash
        assert "language" in defaults
    finally:
        del os.environ["EMAIL_TEMPLATES_DIR"]
