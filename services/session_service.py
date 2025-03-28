from utils.logging_utils import log_info, log_error

class SessionService:
    """Service to manage organizer sessions"""
    
    # Dictionary to store organizer sessions
    # {phone_number: {evento_activo_id: id, context: {...}, esperando_seleccion: bool, ...}}
    sessions = {}
    
    @staticmethod
    def get_session(numero):
        """Get session for a phone number
        
        Args:
            numero (str): Phone number
            
        Returns:
            dict: Session data or empty dict
        """
        return SessionService.sessions.get(numero, {})
    
    @staticmethod
    def create_session(numero):
        """Create a new session for a phone number
        
        Args:
            numero (str): Phone number
            
        Returns:
            dict: Session data
        """
        if numero not in SessionService.sessions:
            SessionService.sessions[numero] = {
                'evento_activo_id': None,
                'context': {}
            }
        return SessionService.sessions[numero]
    
    @staticmethod
    def set_active_event(numero, evento_id):
        """Set active event for a session
        
        Args:
            numero (str): Phone number
            evento_id (int): Event ID
        """
        if numero not in SessionService.sessions:
            SessionService.create_session(numero)
        
        SessionService.sessions[numero]['evento_activo_id'] = evento_id
        log_info(f"Active event set for {numero}: {evento_id}")
    
    @staticmethod
    def get_active_event(numero):
        """Get active event for a session
        
        Args:
            numero (str): Phone number
            
        Returns:
            int or None: Event ID
        """
        return SessionService.get_session(numero).get('evento_activo_id')
    
    @staticmethod
    def set_session_data(numero, key, value):
        """Set arbitrary data in a session
        
        Args:
            numero (str): Phone number
            key (str): Data key
            value: Data value
        """
        if numero not in SessionService.sessions:
            SessionService.create_session(numero)
        
        SessionService.sessions[numero][key] = value
    
    @staticmethod
    def get_session_data(numero, key, default=None):
        """Get arbitrary data from a session
        
        Args:
            numero (str): Phone number
            key (str): Data key
            default: Default value if key not found
            
        Returns:
            Value of key or default
        """
        return SessionService.get_session(numero).get(key, default)
    
    @staticmethod
    def clear_session(numero):
        """Clear a session
        
        Args:
            numero (str): Phone number
        """
        if numero in SessionService.sessions:
            del SessionService.sessions[numero]
            log_info(f"Session cleared for {numero}")
    
    @staticmethod
    def is_waiting_for_selection(numero):
        """Check if session is waiting for event selection
        
        Args:
            numero (str): Phone number
            
        Returns:
            bool: True if waiting for selection
        """
        return SessionService.get_session_data(numero, 'esperando_seleccion', False)
    
    @staticmethod
    def set_waiting_for_selection(numero, waiting=True):
        """Set waiting for selection status
        
        Args:
            numero (str): Phone number
            waiting (bool): Waiting status
        """
        SessionService.set_session_data(numero, 'esperando_seleccion', waiting)
    
    @staticmethod
    def is_confirming_deletion(numero):
        """Check if session is confirming event deletion
        
        Args:
            numero (str): Phone number
            
        Returns:
            bool: True if confirming deletion
        """
        return SessionService.get_session_data(numero, 'confirmando_borrado', False)
    
    @staticmethod
    def set_confirming_deletion(numero, evento_id=None, nombre=None, confirming=True):
        """Set confirming deletion status
        
        Args:
            numero (str): Phone number
            evento_id (int, optional): Event ID to delete
            nombre (str, optional): Event name
            confirming (bool): Confirming status
        """
        SessionService.set_session_data(numero, 'confirmando_borrado', confirming)
        
        if confirming and evento_id is not None:
            SessionService.set_session_data(numero, 'evento_a_borrar_id', evento_id)
            
        if confirming and nombre is not None:
            SessionService.set_session_data(numero, 'evento_a_borrar_nombre', nombre)
    
    @staticmethod
    def get_event_to_delete(numero):
        """Get event ID to delete
        
        Args:
            numero (str): Phone number
            
        Returns:
            tuple: (event_id, event_name)
        """
        evento_id = SessionService.get_session_data(numero, 'evento_a_borrar_id')
        nombre = SessionService.get_session_data(numero, 'evento_a_borrar_nombre')
        return evento_id, nombre 