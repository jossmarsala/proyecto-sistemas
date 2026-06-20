




class Detalle:
    def __init__(self):
        self.id_detalle = None
        self.productos = []

    def agregar_producto(self,producto):
        self.productos.append(producto)

    @property
    def estado_global_entrega(self):
        """
        Es una property
        Revisa todos los productos. 
        Si al menos uno no está 'Completo', el pedido entero sigue abierto.
        """
        if not self.productos:
            return "Vacio"
            
        for prod in self.productos:
            if prod.estado_entrega != "Completo":
                return "Parcial / Pendiente"
        return "Completo"
    @property
    def pendientes(self):
        """
        Es una property
        Genera una lista con todos los productos con un  estado de entrega parcial, ademas marca la cantidad que compro,
        la que esta entregada  y la que resta entregar   
        """
        pendientes = []
        
        for producto in self.productos:
            if producto.estado_entrega != "Completo":
                prod_parcial = {
                    "Nombre" : producto.nombre,
                    "Total comprado" : producto.cantidad,
                    "Cantidad Entregada" : producto.cantidad_entregada,
                    "Resta Entregar" : producto.resta_entregar
                }
                pendientes.append(prod_parcial)
        return pendientes
    
