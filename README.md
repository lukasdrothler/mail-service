# Mail Service

A lightweight, RabbitMQ-driven microservice for sending transactional emails. This service consumes messages from a RabbitMQ queue, renders HTML templates with dynamic content, and sends emails via SMTP.

## Features

- 🐇 **RabbitMQ Integration**: Consumes email sending requests asynchronously.
- 📝 **HTML Templates**: Supports customizable HTML templates for various email types (Verification, Password Reset, etc.).
- 🎨 **Branding Support**: Dynamic branding configuration (colors, logos, app name) per request.
- 🛡️ **Type Safety**: Uses Pydantic models for request validation.
- 🐳 **Docker Ready**: Includes Dockerfile for easy containerization.

## Project Structure

```
mail-service/
├── main.py                 # Entry point
├── src/
│   ├── basemodels.py       # Pydantic data models
│   ├── mail_service.py     # Core logic (Template rendering, SMTP)
│   ├── rmq_consumer.py     # RabbitMQ consumer implementation
│   └── templates/          # HTML Email templates
├── tests/                  # Pytest test suite
├── Dockerfile              # Docker build instructions
└── requirements.txt        # Python dependencies
```

## Prerequisites

- Python 3.9+
- RabbitMQ Server
- SMTP Server (e.g., Gmail, AWS SES, Mailgun)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mail-service
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The service is configured via environment variables. You can use a `.env` file in the root directory.

| Variable | Description | Default |
|----------|-------------|---------|
| `CURRENT_ENV` | Set to `development` for verbose logging | `production` |
| `SMTP_SERVER` | SMTP Server Host | `localhost` |
| `SMTP_PORT` | SMTP Server Port | `587` |
| `SMTP_USER` | SMTP Username | **Required** |
| `SMTP_PASSWORD` | SMTP Password | **Required** |
| `RABBITMQ_HOST` | RabbitMQ Host | `localhost` |
| `RABBITMQ_PORT` | RabbitMQ Port | `5672` |
| `RABBITMQ_MAIL_QUEUE_NAME` | Queue name to consume from | **Required** |
| `RABBITMQ_USERNAME` | RabbitMQ Username | **Required** |
| `RABBITMQ_PASSWORD` | RabbitMQ Password | **Required** |
| `EMAIL_TEMPLATES_DIR` | Custom path for templates | `src/templates` |

## Usage

### Running Locally

Ensure your RabbitMQ and SMTP credentials are set in your environment or `.env` file.

```bash
python main.py
```

### Running with Docker

```bash
docker build -t mail-service .
docker run --env-file .env mail-service
```

## Message Format

The service expects JSON messages in the RabbitMQ queue matching the `SendMailRequest` schema.

**Example Payload:**

```json
{
  "template_name": "email_verification",
  "username": "John Doe",
  "verification_code": "123456",
  "recipient": "user@example.com",
  "branding_config": {
    "app_name": "MyApp",
    "app_owner": "My Company",
    "contact_email": "support@myapp.com",
    "primary_color": "#4F46E5",
    "logo_url": "https://myapp.com/logo.png"
  },
  "email_content": {
    "language": "en",
    "welcome_title": "Welcome aboard!"
  }
}
```

### Supported Templates

- `email_verification`
- `email_change_verification`
- `forgot_password_verification`

## Development

### Running Tests

The project uses `pytest` for testing.

```bash
pytest
```
