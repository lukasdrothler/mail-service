import pytest
from src.basemodels import TemplateName

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
    
    # Mock branding config in mail_service
    mail_service.branding_config = {
        "app_name": "TestApp",
        "app_owner": "Owner",
        "contact_email": "test@example.com"
    }
    
    rendered = mail_service.render_template(template_content, variables)
    
    assert "Welcome to TestApp" in rendered
    assert "Hello TestUser" in rendered

def test_render_template_with_variable_references(mail_service):
    template_content = "<p>{{message}}</p>"
    variables = {
        "username": "TestUser",
        "message": "Hello {username}, welcome to {app_name}"
    }
    
    # Mock branding config in mail_service
    mail_service.branding_config = {
        "app_name": "TestApp",
        "app_owner": "Owner",
        "contact_email": "test@example.com"
    }
    
    rendered = mail_service.render_template(template_content, variables)
    
    assert "Hello TestUser, welcome to TestApp" in rendered

def test_render_email_verification_template(mail_service):
    # Load template
    template_content = mail_service.load_template(TemplateName.EMAIL_VERIFICATION)
    assert template_content is not None

    # Mock branding config in mail_service
    mail_service.branding_config = {
        "app_name": "TestApp",
        "app_owner": "TestOwner",
        "contact_email": "support@testapp.com",
        "logo_url": "",
        "primary_color": "#000000",
        "primary_shade_color": "#000000",
        "primary_foreground_color": "#ffffff"
    }
    
    variables = mail_service.load_template_values(TemplateName.EMAIL_VERIFICATION)
    variables.update({
        "username": "NewUser",
        "verification_code": "123456"
    })

    # Render
    rendered = mail_service.render_template(template_content, variables)

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

    # Mock branding config in mail_service
    mail_service.branding_config = {
        "app_name": "TestApp",
        "app_owner": "TestOwner",
        "contact_email": "support@testapp.com",
        "logo_url": "",
        "primary_color": "#000000",
        "primary_shade_color": "#000000",
        "primary_foreground_color": "#ffffff"
    }
    
    variables = mail_service.load_template_values(TemplateName.EMAIL_CHANGE_VERIFICATION)
    variables.update({
        "username": "ExistingUser",
        "verification_code": "654321"
    })

    # Render
    rendered = mail_service.render_template(template_content, variables)

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

    # Mock branding config in mail_service
    mail_service.branding_config = {
        "app_name": "TestApp",
        "app_owner": "TestOwner",
        "contact_email": "support@testapp.com",
        "logo_url": "",
        "primary_color": "#000000",
        "primary_shade_color": "#000000",
        "primary_foreground_color": "#ffffff"
    }
    
    variables = mail_service.load_template_values(TemplateName.FORGOT_PASSWORD_VERIFICATION)
    variables.update({
        "username": "ForgotUser",
        "verification_code": "987654"
    })

    # Render
    rendered = mail_service.render_template(template_content, variables)

    # Assertions
    assert "987654" in rendered
    assert "ForgotUser" in rendered
    assert "TestApp" in rendered
    assert "{{" not in rendered
    assert "}}" not in rendered

def test_render_template_missing_variables(mail_service):
    # Test that missing variables result in unrendered placeholders
    template_content = "<p>Hello {{username}}, your code is {{code}}</p>"
    variables = {
        "username": "TestUser"
        # code is missing
    }
    
    # Mock branding config in mail_service
    mail_service.branding_config = {
        "app_name": "TestApp",
        "app_owner": "Owner",
        "contact_email": "test@example.com"
    }
    
    rendered = mail_service.render_template(template_content, variables)
    
    assert "Hello TestUser" in rendered
    assert "{{code}}" in rendered  # Should remain unrendered

def test_process_variable_references_circular(mail_service):
    # Test circular dependency handling
    variables = {
        "a": "{b}",
        "b": "{a}"
    }
    
    # Should not hang infinitely, but stop after max_iterations
    processed = mail_service.process_variable_references(variables, max_iterations=3)
    
    # Depending on implementation, it might be partially resolved or remain as is
    # In the current implementation, it will swap back and forth or stay same
    # We just want to ensure it returns and doesn't crash
    assert isinstance(processed, dict)

def test_send_email_html_missing_template(mail_service):
    # Test sending email with non-existent template
    
    # Mock branding config in mail_service
    mail_service.branding_config = {
        "app_name": "TestApp",
        "app_owner": "Owner",
        "contact_email": "test@example.com"
    }
    
    with pytest.raises(ValueError, match="Template 'non_existent_template' not found"):
        mail_service.send_email_html(
            template_name="non_existent_template",
            variables={},
            subject="Test",
            recipient="test@example.com"
        )
