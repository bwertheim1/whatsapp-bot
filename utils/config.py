import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# App configuration
EXCEL_FILE = os.getenv("EXCEL_FILE", "invitados.xlsx")
ADMIN_NUMBER = os.getenv("ADMIN_NUMBER")  # Admin phone number without "+"

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# WhatsApp Web JS configuration
USE_WHATSAPP_WEB = os.getenv("USE_WHATSAPP_WEB", "false").lower() == "true"
WHATSAPP_SERVER_PORT = os.getenv("WHATSAPP_SERVER_PORT", "3000")
WHATSAPP_SERVER_URL = f"http://localhost:{WHATSAPP_SERVER_PORT}"

# Google Drive configuration
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID") 