import pytest
from src.basemodels import TemplateName, BrandingConfig, EmailVerificationContent, EmailChangeVerificationContent, ForgotPasswordVerificationContent

def test_process_variable_references(mail_service):
    # Test simple replacement
    variables = {
        "name": "World",
        "greeting": "Hello {name}"
    }
    processed = mail_service.process_variable_references(variables)
    assert processed["greeting"] == "Hello World"

    # Test nested replacement
    variables = {
        "a": "A",
        "b": "{a}B",
        "c": "{b}C"
    }
    processed = mail_service.process_variable_references(variables)
    assert processed["c"] == "ABC"

    # Test dictionary recursion
    variables = {
        "name": "User",
        "nested": {
            "message": "Hi {name}"
        }
    }
    processed = mail_service.process_variable_references(variables)
    assert processed["nested"]["message"] == "Hi User"

def test_load_template(mail_service):
    # Test loading an existing template from the actual templates directory
    content = mail_service.load_template("email_verification")
    assert content is not None
    assert "<!DOCTYPE html>" in content
    
    # Test loading a non-existent template
    content = mail_service.load_template("non_existent")
    assert content is None

def test_render_template(mail_service):
    template_content = "<h1>Welcome to {{app_name}}</h1><p>Hello {{username}}</p>"
    variables = {
        "username": "TestUser"
    }
    branding_config = BrandingConfig(
        app_name="TestApp",
        app_owner="Owner",
        contact_email="test@example.com"
    )
    
    rendered = mail_service.render_template(template_content, variables, branding_config)
    
    assert "Welcome to TestApp" in rendered
    assert "Hello TestUser" in rendered

def test_render_template_with_variable_references(mail_service):
    template_content = "<p>{{message}}</p>"
    variables = {
        "username": "TestUser",
        "message": "Hello {username}, welcome to {app_name}"
    }
    branding_config = BrandingConfig(
        app_name="TestApp",
        app_owner="Owner",
        contact_email="test@example.com"
    )
    
    rendered = mail_service.render_template(template_content, variables, branding_config)
    
    assert "Hello TestUser, welcome to TestApp" in rendered

def test_render_email_verification_template(mail_service):
    # Load template
    template_content = mail_service.load_template(TemplateName.EMAIL_VERIFICATION)
    assert template_content is not None

    # Setup data
    branding_config = BrandingConfig(
        app_name="TestApp",
        app_owner="TestOwner",
        contact_email="support@testapp.com"
    )
    
    content_model = EmailVerificationContent()
    variables = content_model.model_dump()
    variables.update({
        "username": "NewUser",
        "verification_code": "123456"
    })

    # Render
    rendered = mail_service.render_template(template_content, variables, branding_config)

    # Assertions
    assert "123456" in rendered
    assert "NewUser" in rendered
    assert "TestApp" in rendered
    assert "{{" not in rendered
    assert "}}" not in rendered

def test_render_email_change_verification_template(mail_service):
    # Load template
    template_content = mail_service.load_template(TemplateName.EMAIL_CHANGE_VERIFICATION)
    assert template_content is not None

    # Setup data
    branding_config = BrandingConfig(
        app_name="TestApp",
        app_owner="TestOwner",
        contact_email="support@testapp.com"
    )
    
    content_model = EmailChangeVerificationContent()
    variables = content_model.model_dump()
    variables.update({
        "username": "ExistingUser",
        "verification_code": "654321"
    })

    # Render
    rendered = mail_service.render_template(template_content, variables, branding_config)

    # Assertions
    assert "654321" in rendered
    assert "ExistingUser" in rendered
    assert "TestApp" in rendered
    assert "{{" not in rendered
    assert "}}" not in rendered

def test_render_forgot_password_verification_template(mail_service):
    # Load template
    template_content = mail_service.load_template(TemplateName.FORGOT_PASSWORD_VERIFICATION)
    assert template_content is not None

    # Setup data
    branding_config = BrandingConfig(
        app_name="TestApp",
        app_owner="TestOwner",
        contact_email="support@testapp.com"
    )
    
    content_model = ForgotPasswordVerificationContent()
    variables = content_model.model_dump()
    variables.update({
        "username": "ForgotUser",
        "verification_code": "987654"
    })

    # Render
    rendered = mail_service.render_template(template_content, variables, branding_config)

    # Assertions
    assert "987654" in rendered
    assert "ForgotUser" in rendered
    assert "TestApp" in rendered
    assert "{{" not in rendered
    assert "}}" not in rendered
