# WhatsApp Invitation Management System

A WhatsApp-based system for managing event invitations and tracking responses.

## Features

- Create and manage events
- Import guest lists from Excel
- Send mass invitations via WhatsApp
- Automatically process response messages using AI
- Generate reports on response status
- Export response data to Excel

## Project Structure

The application has been modularized for better maintainability:

```
.
├── app.py                  # Main application entry point
├── models/                 # Data models
│   ├── __init__.py
│   ├── evento.py           # Event model
│   ├── invitado.py         # Guest model
│   └── organizador.py      # Organizer model
├── services/               # Business logic services
│   ├── __init__.py
│   ├── excel_service.py    # Excel file operations
│   ├── openai_service.py   # OpenAI API integration
│   ├── report_service.py   # Report generation
│   ├── session_service.py  # Session management
│   ├── supabase_service.py # Database operations
│   └── verification_service.py # Verification code management
├── adapters/               # External service adapters
│   ├── __init__.py
│   └── whatsapp_adapter.py # WhatsApp messaging adapter
├── routes/                 # API routes
│   ├── __init__.py
│   ├── landing_routes.py   # Landing page routes
│   └── webhook_routes.py   # Webhook handler routes
├── utils/                  # Helper utilities
│   ├── __init__.py
│   ├── config.py           # Configuration and environment variables
│   └── logging_utils.py    # Logging utilities
├── .env                    # Environment variables (not in git)
├── .env.example            # Example environment variables
├── requirements.txt        # Python dependencies
├── index.html              # Landing page
└── whatsapp-server.js      # WhatsApp Web JS server
```

## Installation

1. Clone the repository
2. Install Python dependencies:
```bash
pip install -r requirements.txt
```
3. Install Node.js dependencies (if using WhatsApp Web JS):
```bash
npm install
```
4. Copy `.env.example` to `.env` and set your environment variables
5. Set up Supabase tables (see `create_tables.sql`)

## Configuration

The system can be configured to use either Twilio WhatsApp API or WhatsApp Web JS:

- Twilio: Set `USE_WHATSAPP_WEB=false` in `.env` and configure Twilio credentials
- WhatsApp Web JS: Set `USE_WHATSAPP_WEB=true` in `.env` and run the WhatsApp server

## Usage

1. Start the Flask application:
```bash
python app.py
```

2. If using WhatsApp Web JS, start the WhatsApp server:
```bash
node whatsapp-server.js
```

3. Visit the landing page to register as an organizer
4. Follow the instructions to create events and manage invitations

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a new Pull Request 