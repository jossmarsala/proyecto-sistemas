from classes.Cliente import Cliente



def crear_cliente(tipo,name,apellido,str_num,str_dni = None,str_cuit = None,razon_s = None):
        """
        Crea un cliente con los datos basicos, segun si es simple o complejo    
        
        :param tipo:  Indica si es simple o complejo
        :param name: nombre del cliente
        :param apellido: apellido del cliente
        :param str_num: numero de telefono del cliente
        :param str_dni: dni del cliente(opcional)
        :param str_cuit: cuit del cliente (obligatorio segun tipo)
        :param razon_s: razon social del cliente(obligatorio segun tipo)
        """
  
        if not name or len(name) > 50:
            raise ValueError("Tiene que ingresar un nombre para el cliente")

        if not apellido or len(apellido) > 50:
            raise ValueError(f"Tiene que ingresar un apellido para el cliente {name}")

        if not str_num or len(str_num) < 8 or len(str_num) > 13:
            raise ValueError("El numero no puede estar vacio o tiene que tener la correcta longitud")
        
        if not str_num.isdigit():
            raise ValueError("El teléfono solo debe contener números.")
        
        
        new_cliente = Cliente(name,apellido,str_num)


        if tipo == "simple":
            if str_dni:
                if not str_dni.isdigit() or len(str_dni) < 7:
                    raise ValueError("DNI inválido.")
                new_cliente.agregar_dni(str_dni)


        elif tipo == "Completo": 
            if not str_cuit or len(str_cuit) != 11 :
                raise ValueError("Tiene que ingresar un numero con la correcta longitud")
            if not str_cuit.isdigit():
                raise ValueError("Tiene que ingresar un numero valido, sin caracteres especiales")
            new_cliente.agregar_cuit(str_cuit)

            if not razon_s or len(razon_s) > 50:
                raise ValueError(f"Tiene que ingresar una razon social para el cliente")
            new_cliente.agregar_rs(razon_s)
        
        return new_cliente