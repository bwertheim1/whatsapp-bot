from supabase import create_client
from utils.config import SUPABASE_URL, SUPABASE_KEY
from utils.logging_utils import log_info, log_error

class SupabaseService:
    """Service for handling Supabase database operations"""
    
    @staticmethod
    def init_client():
        """Initialize and return Supabase client"""
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            return supabase
        except Exception as e:
            log_error("Error initializing Supabase client", e)
            return None
    
    @staticmethod
    def initialize_database():
        """Verify and create necessary tables in Supabase"""
        log_info("Initializing database...")
        try:
            supabase = SupabaseService.init_client()
            if not supabase:
                log_error("Failed to connect to Supabase. Check credentials.")
                return False

            # Function to verify if a table exists
            def verify_table(table_name):
                try:
                    response = supabase.table(table_name).select('*').limit(1).execute()
                    log_info(f"Table '{table_name}' exists in Supabase")
                    return True
                except Exception as e:
                    error_message = str(e)
                    log_error(f"Table '{table_name}' does not exist or there's an error", e)
                    return False

            # Verify all necessary tables
            tables_exist = {
                'invitados': verify_table('invitados'),
                'organizadores': verify_table('organizadores'),
                'eventos': verify_table('eventos')
            }
            
            # Log missing tables
            if not all(tables_exist.values()):
                log_warning("Some tables are missing. Please create them manually in the Supabase panel.")
                for table, exists in tables_exist.items():
                    if not exists:
                        log_warning(f"Table '{table}' needs to be created")
            
            return True
        except Exception as e:
            log_error("Error initializing database", e)
            return False

    # Organizadores operations
    @staticmethod
    def get_organizador_by_numero(numero):
        """Get organizador by phone number"""
        try:
            supabase = SupabaseService.init_client()
            if not supabase:
                return False, "Could not connect to Supabase"
            
            response = supabase.table('organizadores').select('*').eq('numero', numero).execute()
            if len(response.data) == 0:
                return False, "Organizador not found"
            
            return True, response.data[0]
        except Exception as e:
            log_error(f"Error getting organizador by number", e)
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def register_organizador(numero, nombre="Organizador"):
        """Register a new organizador"""
        try:
            supabase = SupabaseService.init_client()
            if not supabase:
                return False, "Could not connect to Supabase"
            
            # Check if organizador already exists
            response = supabase.table('organizadores').select('*').eq('numero', numero).execute()
            if len(response.data) > 0:
                return True, response.data[0]
            
            # Register new organizador
            organizador_data = {
                'numero': numero,
                'nombre': nombre
            }
            
            response = supabase.table('organizadores').insert(organizador_data).execute()
            if len(response.data) == 0:
                return False, "Error registering organizador"
            
            return True, response.data[0]
        except Exception as e:
            log_error(f"Error registering organizador", e)
            return False, f"Error: {str(e)}"

    # Eventos operations
    @staticmethod
    def create_evento(organizador_id, nombre, descripcion="", fecha=None):
        """Create a new evento"""
        try:
            supabase = SupabaseService.init_client()
            if not supabase:
                return False, "Could not connect to Supabase"
            
            evento_data = {
                'organizador_id': organizador_id,
                'nombre': nombre,
                'descripcion': descripcion
            }
            
            if fecha:
                evento_data['fecha'] = fecha
            
            response = supabase.table('eventos').insert(evento_data).execute()
            if len(response.data) == 0:
                return False, "Error creating evento"
            
            return True, response.data[0]
        except Exception as e:
            log_error(f"Error creating evento", e)
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_eventos_by_organizador(organizador_id):
        """Get all eventos for an organizador"""
        try:
            supabase = SupabaseService.init_client()
            if not supabase:
                return False, "Could not connect to Supabase"
            
            response = supabase.table('eventos').select('*').eq('organizador_id', organizador_id).execute()
            return True, response.data
        except Exception as e:
            log_error(f"Error getting eventos for organizador", e)
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_active_evento(organizador_id):
        """Get the most recent evento for an organizador"""
        try:
            supabase = SupabaseService.init_client()
            if not supabase:
                return False, "Could not connect to Supabase"
            
            response = supabase.table('eventos').select('*').eq('organizador_id', organizador_id).order('fecha_creacion', desc=True).limit(1).execute()
            if len(response.data) == 0:
                return False, "No active eventos"
            
            return True, response.data[0]
        except Exception as e:
            log_error(f"Error getting active evento", e)
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def delete_evento(evento_id):
        """Delete an evento and its invitados"""
        try:
            supabase = SupabaseService.init_client()
            if not supabase:
                return False, "Could not connect to Supabase"
            
            # Delete invitados first
            supabase.table('invitados').delete().eq('evento_id', evento_id).execute()
            
            # Delete evento
            supabase.table('eventos').delete().eq('id', evento_id).execute()
            
            return True, "Evento deleted successfully"
        except Exception as e:
            log_error(f"Error deleting evento", e)
            return False, f"Error: {str(e)}"

    # Invitados operations
    @staticmethod
    def get_invitados_by_evento(evento_id):
        """Get all invitados for an evento"""
        try:
            supabase = SupabaseService.init_client()
            if not supabase:
                return False, "Could not connect to Supabase"
            
            response = supabase.table('invitados').select('*').eq('evento_id', evento_id).execute()
            return True, response.data
        except Exception as e:
            log_error(f"Error getting invitados for evento", e)
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_invitado_by_numero(evento_id, numero):
        """Get invitado by phone number for an evento"""
        try:
            supabase = SupabaseService.init_client()
            if not supabase:
                return False, "Could not connect to Supabase"
            
            response = supabase.table('invitados').select('*').eq('evento_id', evento_id).eq('numero', numero).execute()
            if len(response.data) == 0:
                return False, "Invitado not found in this evento"
            
            return True, response.data[0]
        except Exception as e:
            log_error(f"Error getting invitado by number", e)
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def update_invitado_response(invitado_id, confirmacion=None, acompanante=None, restricciones=None):
        """Update an invitado's response"""
        try:
            supabase = SupabaseService.init_client()
            if not supabase:
                return False, "Could not connect to Supabase"
            
            update_data = {}
            
            if confirmacion is not None:
                update_data['confirmacion'] = confirmacion
            if acompanante is not None:
                update_data['acompanante'] = acompanante
            if restricciones is not None:
                update_data['restricciones_alimenticias'] = restricciones
            
            if not update_data:
                return True, "No changes to update"
            
            response = supabase.table('invitados').update(update_data).eq('id', invitado_id).execute()
            return True, "Response updated successfully"
        except Exception as e:
            log_error(f"Error updating invitado response", e)
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def import_invitados_to_evento(evento_id, invitados):
        """Import invitados to an evento"""
        try:
            supabase = SupabaseService.init_client()
            if not supabase:
                return False, "Could not connect to Supabase"
            
            # Delete existing invitados
            supabase.table('invitados').delete().eq('evento_id', evento_id).execute()
            
            # Insert new invitados
            response = supabase.table('invitados').insert(invitados).execute()
            
            return True, f"Successfully imported {len(invitados)} invitados"
        except Exception as e:
            log_error(f"Error importing invitados to evento", e)
            return False, f"Error: {str(e)}"

    @staticmethod
    def get_event_by_id(evento_id):
        """Get evento by ID
        
        Args:
            evento_id (int): ID of the evento
            
        Returns:
            tuple: (success, evento or error_message)
        """
        try:
            supabase = SupabaseService.init_client()
            if not supabase:
                return False, "Could not connect to Supabase"
            
            response = supabase.table('eventos').select('*').eq('id', evento_id).execute()
            if len(response.data) == 0:
                return False, "Evento not found"
            
            return True, response.data[0]
        except Exception as e:
            log_error(f"Error getting evento by ID", e)
            return False, f"Error: {str(e)}"

# Import this at the end to avoid circular imports
from utils.logging_utils import log_warning 