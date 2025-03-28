class Invitado:
    """Model class for Invitado (event guest)"""
    
    def __init__(self, id=None, evento_id=None, nombre=None, numero=None,
                 confirmacion=None, acompanante=None, restricciones_alimenticias=None):
        """Initialize an Invitado instance
        
        Args:
            id (int, optional): ID in database
            evento_id (int, optional): ID of evento
            nombre (str, optional): Guest name
            numero (str, optional): Phone number
            confirmacion (str, optional): Confirmation status (Sí/No)
            acompanante (str, optional): Companion status (Sí/No)
            restricciones_alimenticias (str, optional): Dietary restrictions
        """
        self.id = id
        self.evento_id = evento_id
        self.nombre = nombre
        self.numero = numero
        self.confirmacion = confirmacion
        self.acompanante = acompanante
        self.restricciones_alimenticias = restricciones_alimenticias
    
    @classmethod
    def from_dict(cls, data):
        """Create an Invitado instance from a dictionary
        
        Args:
            data (dict): Dictionary with invitado data
            
        Returns:
            Invitado: New instance
        """
        return cls(
            id=data.get('id'),
            evento_id=data.get('evento_id'),
            nombre=data.get('nombre'),
            numero=data.get('numero'),
            confirmacion=data.get('confirmacion'),
            acompanante=data.get('acompanante'),
            restricciones_alimenticias=data.get('restricciones_alimenticias')
        )
    
    def to_dict(self):
        """Convert instance to dictionary
        
        Returns:
            dict: Dictionary representation
        """
        return {
            'id': self.id,
            'evento_id': self.evento_id,
            'nombre': self.nombre,
            'numero': self.numero,
            'confirmacion': self.confirmacion,
            'acompanante': self.acompanante,
            'restricciones_alimenticias': self.restricciones_alimenticias
        }
    
    def __str__(self):
        """String representation
        
        Returns:
            str: String representation
        """
        return f"Invitado(id={self.id}, nombre={self.nombre}, numero={self.numero}, confirmacion={self.confirmacion})"
    
    @property
    def has_responded(self):
        """Check if invitado has responded
        
        Returns:
            bool: True if responded, False otherwise
        """
        return self.confirmacion is not None and self.confirmacion.strip() != '' 