class Organizador:
    """Model class for Organizador (event organizer)"""
    
    def __init__(self, id=None, numero=None, nombre=None, fecha_registro=None):
        """Initialize an Organizador instance
        
        Args:
            id (int, optional): ID in database
            numero (str, optional): Phone number
            nombre (str, optional): Name
            fecha_registro (datetime, optional): Registration date
        """
        self.id = id
        self.numero = numero
        self.nombre = nombre
        self.fecha_registro = fecha_registro
    
    @classmethod
    def from_dict(cls, data):
        """Create an Organizador instance from a dictionary
        
        Args:
            data (dict): Dictionary with organizador data
            
        Returns:
            Organizador: New instance
        """
        return cls(
            id=data.get('id'),
            numero=data.get('numero'),
            nombre=data.get('nombre'),
            fecha_registro=data.get('fecha_registro')
        )
    
    def to_dict(self):
        """Convert instance to dictionary
        
        Returns:
            dict: Dictionary representation
        """
        return {
            'id': self.id,
            'numero': self.numero,
            'nombre': self.nombre,
            'fecha_registro': self.fecha_registro
        }
    
    def __str__(self):
        """String representation
        
        Returns:
            str: String representation
        """
        return f"Organizador(id={self.id}, nombre={self.nombre}, numero={self.numero})" 