

class Venta:
    def __init__(self,num_semanal_venta,ref_venta,tipo_pago,detalle,fecha_venta,dia_venta,hora_venta):
        #* Atributos "constructores"
        self.id_venta = None #? Atributo sql

        self.fecha_venta = fecha_venta
        self.num_semanal_venta = num_semanal_venta
        self.ref_venta = ref_venta
        self.tipo_pago = tipo_pago
        self.dia_venta = dia_venta
        self.hora_venta = hora_venta

        self.detalle = detalle

        #* Atributos properties
        self.tipo_venta = "local"
        self.estandar = True
        self.cobro_inmediato = True
        self.entrega_inmediata = True
        self.estado_pago = "Pagado"
        #* Estos atributos funcionan segun los properties anteriores y se definen en el controlador

        #?Atributos que dependen de pedido
        self.fecha_entrega = None
        self.hora_entrega = None
        self.dia_entrega = None

        #?Atributos que dependen de estado de pago
        self.monto_cobrado = 0.0

    
    #!Hay que acomodar el monto_total

    @property
    def saldo_pendiente(self):
        """
        Calcula cuánto falta cobrar
        """
        return self.monto_total - self.monto_cobrado
    @property
    def monto_total(self):
        #!Cheackear
        """
        Este metodo realiza la suma de subtotales segun la lista de productos en el detalle
        y asigna el resultado de esta al monto total de la venta
        
        :param self: self.detalle
        """
        if not self.detalle or not hasattr(self.detalle, 'productos'):
            return 0.0
        return sum(producto.sub_total for producto in self.detalle.productos)
    
     
    def config_cobro_inmediato(self, verif):
        """
        Este metodo se encarga de verificar si la venta cobra el total o no
        En caso de no serlo el booleano tiene que ser False asi cambia el atributo a False
        Por defecto es verdadero (el cobro es total)

        :param self: Self.cobro_inmediato
        :param verif: Boolean
        """
        if verif == False:
            self.cobro_inmediato= False

    def config_tipo_entrega(self, verif):
        """
        Este metodo se encarga de verificar si se hace una entrega parcial o total de los prodcutos
        En caso de no serlo el booleano tiene que ser False asi cambia el atributo a False
        Por defecto es verdadero (la entrega es total)

        :param self: Self.entrega_inmediata
        :param verif: Boolean
        """
        if verif == False:
            self.entrega_inmediata = False
    def config_tipo_venta(self,verif):
        """
        Asigna el valor de tipo de venta segun la variable verif, si esta es falsa entonces es un pedido si es verdadera entonces es local
        
        :param self: Self.tipo_venta
        :param verif: Boolean
        """
        if verif == True:
            self.tipo_venta = "local"
        else:
            self.tipo_venta = "pedido"
    def config_estado_pago(self,verif):
        """
        Define el estado de pago segun la variable verif, si esta es falsa entonces falta cobrar y si es True esta pagado
        
        :param self: Self.estado_pago
        :param verif: Boolean
        """
        if verif == False:
            self.estado_pago = "A cobrar / parcial"