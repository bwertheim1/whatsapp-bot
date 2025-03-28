import json
from openai import OpenAI
from utils.config import OPENAI_API_KEY
from utils.logging_utils import log_info, log_error

class OpenAIService:
    """Service to handle OpenAI API interactions"""
    
    @staticmethod
    def init_client():
        """Initialize and return OpenAI client"""
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            return client
        except Exception as e:
            log_error("Error initializing OpenAI client", e)
            return None
    
    @staticmethod
    def analyze_response(mensaje):
        """Use GPT to analyze response message and extract relevant information
        
        Args:
            mensaje (str): Message to analyze
            
        Returns:
            dict or None: Extracted information or None on error
        """
        log_info(f"Analyzing message with GPT: '{mensaje}'")
        
        prompt = f"""Analiza este mensaje de respuesta a una invitación y extrae la información solicitada.
Contexto: Es una respuesta a un mensaje que pregunta sobre:
1. Confirmación de asistencia
2. Si llevará acompañante
3. Restricciones alimenticias

Mensaje a analizar: "{mensaje}"

Reglas de interpretación:
- Si menciona que va con alguien (esposa, pareja, amigo, etc.), implica que confirma asistencia Y que lleva acompañante
- Si dice que va solo/sola, implica que confirma asistencia pero NO lleva acompañante
- Cualquier mención a dieta especial o alergias debe registrarse como restricción
- Si no menciona restricciones, usar null

Responde SOLO con este JSON exacto:
{{
    "confirmacion": "sí/no",
    "acompanante": "sí/no",
    "restricciones": "texto de la restricción o null si no hay"
}}"""

        try:
            client = OpenAIService.init_client()
            if not client:
                return None
                
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente experto en interpretar respuestas a invitaciones."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            resultado = json.loads(response.choices[0].message.content)
            log_info(f"GPT analysis result: {resultado}")
            return resultado
        except Exception as e:
            log_error("Error analyzing message with GPT", e)
            return None
    
    @staticmethod
    def chat_with_gpt(mensaje, conversation_history):
        """Maintain a conversation with GPT
        
        Args:
            mensaje (str): User message
            conversation_history (list): History of conversation
            
        Returns:
            str: GPT response
        """
        log_info(f"Chatting with GPT. Message: '{mensaje}'")
        
        # Add user message to history
        conversation_history.append({"role": "user", "content": mensaje})
        
        try:
            # Limit history to avoid excessive tokens (last 10 messages)
            limited_history = conversation_history[-10:]
            
            client = OpenAIService.init_client()
            if not client:
                return "Lo siento, hubo un problema al conectar con el asistente."
                
            # Call GPT
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=limited_history,
                temperature=0.7,
                max_tokens=500
            )
            
            # Get response
            respuesta = response.choices[0].message.content
            log_info(f"GPT response: '{respuesta[:50]}...'")
            
            # Add response to history
            conversation_history.append({"role": "assistant", "content": respuesta})
            
            return respuesta
        except Exception as e:
            error_message = f"Error in chat with GPT: {str(e)}"
            log_error(error_message)
            return f"Lo siento, tuve un problema para procesar tu mensaje: {str(e)}" 