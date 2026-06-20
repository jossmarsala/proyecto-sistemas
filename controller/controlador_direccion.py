from classes.Direccion import Direccion




def crear_direccion(
        tipo_dir, ubi_maps=False,
        calle_principal=None,calle_b=None,calle_c=None,numeracion=None,
        barrio=None,manzana=None,casa=None,
        depto=None,piso=None,
):
    """
    Crea una direccion segun los datos que el pasan
    
    :param tipo_dir: Dtermina si es una direccion combianada o simple (str)
    :param calle_principal: Calle principal sobre la que esta la casa/obra (str) (por defecto None)
    :param calle_b: Entre que calle esta la principal (str) (por defecto None)
    :param calle_c: Entre que calle esta la principal (str) (por defecto None)
    :param numeracion: Numeracion de la obra/casa segun la calle principal (str) (por defecto None)
    :param barrio: Barrio de la obra/casa (str) (por defecto None)
    :param manzana: Manzana del barrio de la obra/casa (str) (por defecto None)
    :param casa: Nro casa/obra segun el barrio y la manzana (str) (por defecto None)
    :param depto: nro depto (str) (por defecto None)
    :param piso: piso del depto (str) (por defecto None)
    :param ubi_maps: Ubicacion por maps de la obra/casa (boolean) (False x defecto)
    """


    new_dir = Direccion()

    if tipo_dir == "Barrio":
        if not manzana or not barrio or not casa:
            raise ValueError("Los datos de la direccion segun barrio tienen que estar completos")
        new_dir.agregar_direccion_barrio(barrio, manzana, casa)


    if tipo_dir == "Calle":
        if not calle_principal or not numeracion:
            raise ValueError("Los datos de la direccion segun Calle tienen que estar completos")
        new_dir.agregar_direccion_calle(calle_principal,calle_b,calle_c, numeracion)


    if tipo_dir == "Calle y Barrio":
        if not calle_principal or not numeracion:
            raise ValueError("Los datos de la direccion segun Calle tienen que estar completos")
        if not manzana or not barrio or not casa:
            raise ValueError("Los datos de la direccion segun barrio tienen que estar completos")
        new_dir.agregar_direccion_barrio(barrio, manzana, casa)
        new_dir.agregar_direccion_calle(calle_principal,calle_b,calle_c,numeracion)


    if tipo_dir == "Calle y depto":
        if not calle_principal or not numeracion:
            raise ValueError("Los datos de la direccion segun Calle tienen que estar completos")
        new_dir.agregar_direccion_calle(calle_principal, calle_b,calle_c,numeracion)
        if not depto or not piso:
            raise ValueError("Los datos de la direccion segun depto tienen que estar completos")
        new_dir.agregar_dep_piso(depto,piso)


    if ubi_maps:
        new_dir.agregar_ubicacion_maps(ubi_maps)

    
    try:
        new_dir.validar_integridad()
    except ValueError as e:
        raise ValueError(f"Error de validación interna de la clase: {e}")
    
    return new_dir