import random
from datetime import datetime, timedelta
from utils.logging_utils import log_info, log_error

class VerificationService:
    """Service for verification code management"""
    
    # Dictionary to store verification codes
    # {phone_number: {'code': '123456', 'verified': False, 'created_at': datetime}}
    verification_codes = {}
    
    @staticmethod
    def generate_code(numero):
        """Generate a verification code for a phone number
        
        Args:
            numero (str): Phone number
            
        Returns:
            str: Generated code
        """
        log_info(f"Generating verification code for: {numero}")
        
        # Generate a random 6-digit code
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Store the code
        VerificationService.verification_codes[numero] = {
            'codigo': code,
            'verificado': False,
            'fecha_generacion': datetime.now()
        }
        
        log_info(f"Verification code generated for {numero}: {code}")
        return code
    
    @staticmethod
    def verify_code(numero, code):
        """Verify a code for a phone number
        
        Args:
            numero (str): Phone number
            code (str): Code to verify
            
        Returns:
            bool: True if verified, False otherwise
        """
        log_info(f"Verifying code for {numero}: {code}")
        
        if numero not in VerificationService.verification_codes:
            log_info(f"No verification code found for {numero}")
            return False
        
        stored_code = VerificationService.verification_codes[numero]
        
        # Check if code has expired (24 hours)
        if datetime.now() - stored_code['fecha_generacion'] > timedelta(hours=24):
            log_info(f"Verification code for {numero} has expired")
            return False
        
        # Check if code matches
        if stored_code['codigo'] == code:
            log_info(f"Verification successful for {numero}")
            VerificationService.verification_codes[numero]['verificado'] = True
            return True
        
        log_info(f"Verification failed for {numero}")
        return False
    
    @staticmethod
    def is_verified(numero):
        """Check if a phone number is verified
        
        Args:
            numero (str): Phone number
            
        Returns:
            bool: True if verified, False otherwise
        """
        return (numero in VerificationService.verification_codes and 
                VerificationService.verification_codes[numero].get('verificado', False))
    
    @staticmethod
    def clear_verification(numero):
        """Clear verification data for a phone number
        
        Args:
            numero (str): Phone number
        """
        if numero in VerificationService.verification_codes:
            del VerificationService.verification_codes[numero]
            log_info(f"Verification data cleared for {numero}")
    
    @staticmethod
    def get_all_verification_codes():
        """Get all verification codes (for debugging)
        
        Returns:
            dict: All verification codes
        """
        return VerificationService.verification_codes 