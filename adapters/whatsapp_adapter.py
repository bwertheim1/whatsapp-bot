import requests
from twilio.rest import Client
from utils.config import (
    USE_WHATSAPP_WEB, 
    WHATSAPP_SERVER_URL, 
    TWILIO_ACCOUNT_SID, 
    TWILIO_AUTH_TOKEN
)
from utils.logging_utils import log_info, log_error

class WhatsAppAdapter:
    """Adapter for WhatsApp messaging (Twilio and WhatsApp Web JS)"""
    
    def __init__(self):
        """Initialize the adapter based on configuration"""
        self.use_whatsapp_web = USE_WHATSAPP_WEB
        if not self.use_whatsapp_web:
            self.twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        log_info(f"WhatsApp adapter initialized. Using WhatsApp Web: {self.use_whatsapp_web}")
    
    def send_message(self, number, message):
        """Send a text message to a WhatsApp number
        
        Args:
            number (str): The phone number (with or without +)
            message (str): The message text to send
            
        Returns:
            bool: Success status
        """
        try:
            if self.use_whatsapp_web:
                # Clean number for WhatsApp Web JS (digits only)
                clean_number = number.replace("whatsapp:+", "").replace("+", "")
                
                # Use WhatsApp Web JS
                response = requests.post(
                    f"{WHATSAPP_SERVER_URL}/send-message",
                    json={"number": clean_number, "message": message}
                )
                if response.status_code == 200:
                    log_info(f"Message sent to {clean_number} using WhatsApp Web JS")
                    return True
                else:
                    log_error(f"Error sending message using WhatsApp Web JS: {response.text}")
                    return False
            else:
                # Use Twilio
                message = self.twilio_client.messages.create(
                    body=message,
                    from_=f"whatsapp:+14155238886",  # Twilio number
                    to=f"whatsapp:+{number.replace('+', '')}"
                )
                log_info(f"Message sent to {number} using Twilio")
                return True
        except Exception as e:
            log_error(f"Error sending message to {number}", e)
            return False
    
    def send_file(self, number, file_path, caption=None):
        """Send a file to a WhatsApp number
        
        Args:
            number (str): The phone number (with or without +)
            file_path (str): Path to the file to send
            caption (str, optional): Caption for the file
            
        Returns:
            bool: Success status
        """
        try:
            if self.use_whatsapp_web:
                # Clean number for WhatsApp Web JS (digits only)
                clean_number = number.replace("whatsapp:+", "").replace("+", "")
                
                # Use WhatsApp Web JS
                response = requests.post(
                    f"{WHATSAPP_SERVER_URL}/send-file",
                    json={"number": clean_number, "filePath": file_path, "caption": caption or ""}
                )
                if response.status_code == 200:
                    log_info(f"File sent to {clean_number} using WhatsApp Web JS")
                    return True
                else:
                    log_error(f"Error sending file using WhatsApp Web JS: {response.text}")
                    return False
            else:
                # For Twilio, we need a public URL
                log_info(f"Twilio requires a public URL to send files")
                return False
        except Exception as e:
            log_error(f"Error sending file to {number}", e)
            return False 