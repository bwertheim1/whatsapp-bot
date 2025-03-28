from services.supabase_service import SupabaseService
from utils.logging_utils import log_info, log_error

class ReportService:
    """Service for generating reports"""
    
    @staticmethod
    def generate_event_report(evento_id):
        """Generate a report for an evento
        
        Args:
            evento_id (int): ID of the evento
            
        Returns:
            str: Formatted report
        """
        try:
            # Get evento data
            success, evento = SupabaseService.get_event_by_id(evento_id)
            if not success:
                return "Error al obtener datos del evento"
            
            # Get invitados data
            success, invitados = SupabaseService.get_invitados_by_evento(evento_id)
            if not success:
                return f"Error al generar reporte: {invitados}"
            
            total = len(invitados)
            confirmados = len([i for i in invitados if i.get('confirmacion', '').lower() == 'sí'])
            rechazados = len([i for i in invitados if i.get('confirmacion', '').lower() == 'no'])
            pendientes = total - confirmados - rechazados
            
            return f"""📊 Reporte de "{evento['nombre']}":
- Total invitados: {total}
- Confirmados: {confirmados}
- Rechazados: {rechazados}
- Pendientes: {pendientes}"""
        except Exception as e:
            log_error("Error generating event report", e)
            return f"Error al generar reporte: {str(e)}"
    
    @staticmethod
    def check_all_responses(evento_id):
        """Check if all invitados have responded
        
        Args:
            evento_id (int): ID of the evento
            
        Returns:
            tuple: (all_responded, responded_count, total_count, pending_list)
        """
        try:
            # Get invitados data
            success, invitados = SupabaseService.get_invitados_by_evento(evento_id)
            if not success:
                log_error(f"Error getting invitados for event {evento_id}: {invitados}")
                return False, 0, 0, []
                
            total_invitados = len(invitados)
            if total_invitados == 0:
                return True, 0, 0, []  # No invitados, all responded
                
            # Count responses
            respondieron = [i for i in invitados if i.get('confirmacion') is not None 
                            and i.get('confirmacion').strip() != '']
            num_respuestas = len(respondieron)
            
            # List of pending invitados
            faltantes = [i['nombre'] for i in invitados if i.get('confirmacion') is None 
                        or i.get('confirmacion').strip() == '']
            
            todas_respondieron = (num_respuestas == total_invitados)
            
            return todas_respondieron, num_respuestas, total_invitados, faltantes
        except Exception as e:
            log_error(f"Error checking responses for event {evento_id}", e)
            return False, 0, 0, []
    
    @staticmethod
    def generate_pending_list(evento_id):
        """Generate a list of pending invitados
        
        Args:
            evento_id (int): ID of the evento
            
        Returns:
            str: Formatted list
        """
        try:
            todas_respondieron, num_respuestas, total_invitados, faltantes = ReportService.check_all_responses(evento_id)
            
            if todas_respondieron:
                return "✅ Todos los invitados han respondido"
            
            if not faltantes:
                return "No hay invitados pendientes"
            
            message = f"📝 Invitados pendientes ({len(faltantes)}/{total_invitados}):\n"
            for i, nombre in enumerate(faltantes, 1):
                message += f"{i}. {nombre}\n"
                
            return message
        except Exception as e:
            log_error("Error generating pending list", e)
            return f"Error al generar lista de pendientes: {str(e)}" 