class Producto:
    def __init__(self,nombre,precio,cantidad):
        
        self.nombre = nombre
        self.precio = precio
        self.cantidad = cantidad
        

        self.estado_entrega = "Completo"
        self.cantidad_entregada = cantidad
    @property
    def sub_total(self):
        """
        Es una property que calcula el subtotal de cada producto segun su cantidad y precio
        
        :param self:
        """
        return self.precio * self.cantidad
    
    def config_estado_entrega(self, cantidad_E_real):
        """
        Esta funcion determina el estado de la entrega segun la cantidad que retire el cliente del producto
        
        :param self: trabajamos con estado_entrega y cantidad
        :param cantidad_E_real: Es la cantidad que retira el cliente
        """
        if cantidad_E_real > self.cantidad:
            print("Error: No se puede entregar una cantidad mayor a los vendido")
            return
        
        self.cantidad_entregada = cantidad_E_real

        if self.cantidad_entregada ==  self.cantidad:
            self.estado_entrega = "Completo"
        elif self.cantidad_entregada == 0:
            self.estado_entrega = "Pendiente"
        else:
            self.estado_entrega = "Parcial"
    

    @property
    def resta_entregar(self):
        """
        Esta property determina lo que le falta entregar al cliente
        
        :param self: Trabajamos con canitdad y cantidad_entregada
        """
        return self.cantidad - self.cantidad_entregada