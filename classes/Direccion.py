class Direccion:
    def __init__(self):
        self.id_direccion = None
        self.calle_principal = None
        self.calle_b = None
        self.calle_c = None
        self.numeracion = None
        self.barrio = None
        self.manzana = None
        self.casa = None
        self.departamento = None
        self.piso = None
        self.ubicacion_maps = None

    def agregar_direccion_calle(self,calle_principal,calle_b,calle_c,numeracion):
        self.calle_principal = calle_principal
        self.calle_b = calle_b
        self.calle_c = calle_c
        self.numeracion = numeracion
        

    def agregar_direccion_barrio(self,barrio,manzana,casa):

        self.barrio = barrio
        self.manzana = manzana
        self.casa = casa
        
    def agregar_dep_piso(self,departamento,piso):
            
        self.departamento = departamento
        self.piso = piso
        

    def agregar_ubicacion_maps(self,ubi):
        self.ubicacion_maps = ubi


    def validar_integridad(self):
        """
        Verifica que la dirección tenga la consistencia mínima necesaria.
        Validamos que exista una ubicación base y que los detalles (depto) estén completos.
        """
        tiene_urbana = self.calle_principal and self.numeracion
        tiene_barrio = self.barrio and self.manzana and self.casa

        if not tiene_urbana and not tiene_barrio:
            raise ValueError("⛔ Error: Dirección vacía. Requiere (Calle y Altura) O (Barrio, Mz y Casa).")


        tiene_piso = self.piso is not None
        tiene_depto = self.departamento is not None

        if tiene_piso != tiene_depto: 
            raise ValueError("⛔ Error: Datos de edificio incompletos. Si indica Piso, debe indicar Depto (y viceversa).")

        return True
        

        