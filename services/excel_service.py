import os
import pandas as pd
from datetime import datetime
from utils.config import EXCEL_FILE
from utils.logging_utils import log_info, log_error
from services.supabase_service import SupabaseService

class ExcelService:
    """Service for Excel file operations"""
    
    @staticmethod
    def import_excel_to_evento(file_path, evento_id):
        """Import data from Excel to an evento
        
        Args:
            file_path (str): Path to Excel file
            evento_id (int): ID of the evento
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Read Excel
            df = pd.read_excel(file_path)
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Verify required columns
            required_columns = ["Nombre", "Numero"]
            current_columns = [col.strip() for col in df.columns]
            required_columns_clean = [col.strip() for col in required_columns]
            
            if not all(col in current_columns for col in required_columns_clean):
                missing_cols = [col for col in required_columns_clean if col not in current_columns]
                return False, f"El Excel debe contener las columnas obligatorias: {', '.join(missing_cols)}"
                
            # Convert DataFrame to list of dictionaries
            invitados_formateados = []
            
            for _, row in df.iterrows():
                invitado_formateado = {
                    'evento_id': evento_id,
                    'nombre': str(row.get('Nombre', '')) if not pd.isna(row.get('Nombre', '')) else '',
                    'numero': str(row.get('Numero', '')) if not pd.isna(row.get('Numero', '')) else '',
                    'confirmacion': str(row.get('Confirmacion', '')) if not pd.isna(row.get('Confirmacion', '')) else '',
                    'acompanante': str(row.get('+1', '')) if not pd.isna(row.get('+1', '')) else '',
                    'restricciones_alimenticias': str(row.get('Restricciones alimenticias', '')) if not pd.isna(row.get('Restricciones alimenticias', '')) else ''
                }
                
                # Validate that number and name are not empty
                if invitado_formateado['nombre'] and invitado_formateado['numero']:
                    invitados_formateados.append(invitado_formateado)
            
            if not invitados_formateados:
                return False, "No se encontraron datos válidos para importar"
                
            # Import to Supabase
            success, message = SupabaseService.import_invitados_to_evento(evento_id, invitados_formateados)
            
            if success:
                log_info(f"Excel imported successfully: {len(invitados_formateados)} invitados for evento {evento_id}")
                return True, f"Excel importado con éxito. {len(invitados_formateados)} invitados registrados para su evento."
            else:
                return False, message
                
        except Exception as e:
            log_error("Error importing Excel to evento", e)
            return False, f"Error al importar Excel: {str(e)}"
    
    @staticmethod
    def export_evento_to_excel(evento_id, output_file=None):
        """Export invitados data to Excel file
        
        Args:
            evento_id (int): ID of the evento
            output_file (str, optional): Custom output file path
            
        Returns:
            tuple: (success, file_path or error_message)
        """
        try:
            # Generate unique filename for each evento if not provided
            if output_file is None:
                output_file = f"evento_{evento_id}.xlsx"
            
            # Get invitados from evento
            success, invitados = SupabaseService.get_invitados_by_evento(evento_id)
            if not success:
                return False, invitados
            
            # Convert to DataFrame
            df = pd.DataFrame(invitados)
            
            # Skip if no data
            if df.empty:
                return False, "No hay datos para exportar"
            
            # Rename columns for Excel format
            df = df.rename(columns={
                'nombre': 'Nombre',
                'numero': 'Numero',
                'confirmacion': 'Confirmacion',
                'acompanante': '+1',
                'restricciones_alimenticias': 'Restricciones alimenticias'
            })
            
            # Select relevant columns
            columns = ['Nombre', 'Numero', 'Confirmacion', '+1', 'Restricciones alimenticias']
            if all(col in df.columns for col in columns):
                df = df[columns]
            
            # Save Excel
            df.to_excel(output_file, index=False)
            
            log_info(f"Excel exported successfully to {output_file}")
            return True, output_file
        except Exception as e:
            log_error("Error exporting evento to Excel", e)
            return False, f"Error al exportar a Excel: {str(e)}"
    
    @staticmethod
    def backup_excel():
        """Create a backup of the Excel file
        
        Returns:
            bool: Success status
        """
        try:
            if os.path.exists(EXCEL_FILE):
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{EXCEL_FILE}"
                os.rename(EXCEL_FILE, backup_name)
                log_info(f"Excel backup created: {backup_name}")
                return True
            return False
        except Exception as e:
            log_error("Error creating Excel backup", e)
            return False
    
    @staticmethod
    def download_file(url, auth_tuple=None):
        """Download file from URL
        
        Args:
            url (str): URL to download from
            auth_tuple (tuple, optional): Basic auth credentials (username, password)
            
        Returns:
            tuple: (success, file_path or error_message)
        """
        try:
            import requests
            
            # Download file with auth if provided
            if auth_tuple:
                response = requests.get(url, auth=auth_tuple)
            else:
                response = requests.get(url)
                
            response.raise_for_status()
            
            # Save temporarily
            temp_file = "temp_download.xlsx"
            with open(temp_file, "wb") as f:
                f.write(response.content)
                
            log_info(f"File downloaded successfully to {temp_file}")
            return True, temp_file
        except Exception as e:
            log_error("Error downloading file", e)
            return False, str(e) 