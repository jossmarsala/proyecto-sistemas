from classes.Encargado_obra import Encargado_obra




def crear_encargado(name,str_num,apellido=None):
    """
    Crea un encargado con la opcion de agregar un apellido
    
    :param name: Nombre del encargado (str)
    :param str_num: Numero de cel del encargado (str)
    :param apelldio: Apellido del encargado (str) (None x defecto)
    """

    if not name or len(name) > 50:
        raise ValueError("Tiene que ingresar un nombre para el cliente")

    if not str_num or len(str_num) < 8 or len(str_num) > 13:
        raise ValueError("El numero no puede estar vacio o tiene que tener la correcta longitud")
    
    if not str_num.isdigit():
        raise ValueError("El teléfono solo debe contener números.")
    
    if apellido and len(apellido) > 50:
        raise ValueError("Error: El apellido tiene que ser menor a 50 caracteres.")
    

    new_encargado = Encargado_obra(name, str_num, apellido)

    return new_encargado