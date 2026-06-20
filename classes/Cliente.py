class Cliente:
    def __init__(self,nombre,apellido,telefono):

        self.id_cliente = None
        self.nombre = nombre
        self.apellido = apellido
        self.num_telefono = telefono
        self.cuit = None
        self.razon_social = None
        self.dni = None

        
        self.direcciones=[]
        self.encargados=[]
        

    def agregar_direccion(self,direccion):
        """
            Funcion que añade una direccion a la lista direcciones del cliente

        :param self: Trabaja con self.direcciones que es una lista de Direccion
        :param direccion: Es un objeto Direccion
        """
        if direccion:
            self.direcciones.append(direccion)
        else:
            print("La direccion esta vacia, no se puede cargar")

    def agregar_encargado(self,encargado):
        """
            Funcion que añade un encargado a la lista encargados del cliente

        :param self: Trabaja con self.encargados que es una lista de Encargado
        :param encargado: Es un objeto Encargado
        """
        if encargado:
            self.encargados.append(encargado)
        else:
            print("Los datos del encagados estan vacios, no se puede cargar")

    def agregar_cuit(self,cuit):
        """
        Agrega un cuit
        
        :param self: propio clase
        :param cuit: cuit del cliente
        """
        self.cuit = cuit

    def agregar_rs(self,rs):
        """
        Agrega una razon social
        
        :param self: propio clase
        :param rs: Razon social del cliente
        """
        self.razon_social = rs

    def agregar_dni(self,dni):
        """
        Agrega un dni
        
        :param self: propio clase
        :param dni: dni cliente
        """
        self.dni = dni