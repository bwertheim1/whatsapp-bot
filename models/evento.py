from datetime import datetime

class Evento:
    """Model class for Evento (event)"""
    
    def __init__(self, id=None, organizador_id=None, nombre=None, 
                 descripcion=None, fecha=None, fecha_creacion=None):
        """Initialize an Evento instance
        
        Args:
            id (int, optional): ID in database
            organizador_id (int, optional): ID of organizador
            nombre (str, optional): Event name
            descripcion (str, optional): Event description
            fecha (datetime, optional): Event date
            fecha_creacion (datetime, optional): Creation date
        """
        self.id = id
        self.organizador_id = organizador_id
        self.nombre = nombre
        self.descripcion = descripcion
        self.fecha = fecha
        self.fecha_creacion = fecha_creacion or datetime.now()
    
    @classmethod
    def from_dict(cls, data):
        """Create an Evento instance from a dictionary
        
        Args:
            data (dict): Dictionary with evento data
            
        Returns:
            Evento: New instance
        """
        return cls(
            id=data.get('id'),
            organizador_id=data.get('organizador_id'),
            nombre=data.get('nombre'),
            descripcion=data.get('descripcion'),
            fecha=data.get('fecha'),
            fecha_creacion=data.get('fecha_creacion')
        )
    
    def to_dict(self):
        """Convert instance to dictionary
        
        Returns:
            dict: Dictionary representation
        """
        return {
            'id': self.id,
            'organizador_id': self.organizador_id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'fecha': self.fecha,
            'fecha_creacion': self.fecha_creacion
        }
    
    def __str__(self):
        """String representation
        
        Returns:
            str: String representation
        """
        return f"Evento(id={self.id}, nombre={self.nombre}, organizador_id={self.organizador_id})" 