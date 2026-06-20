from classes.Detalle import Detalle






def crear_detalle(obj_venta):
        #! el controlador detalle tiene que retornar una lisrta con todos los productos y el controlador fventa añade directamnete esa lista de prodcutos
    print(f"Añadiendo productos a la venta {obj_venta.ref_venta}")
    while(True):
        producto = input("Ingrese el nombre del producto: ").strip()

        if producto:
            break
        print("Tiene que colocar el nombre del producto")

    while(True):
        try:
            precio = int(input(f"Ingrese el precio del producto {producto}: "))
            if precio >= 0: 
                break
            print("❌ El precio no puede ser negativo.")
        except ValueError:
            print("❌ Error: Precio debe ser números.") 
            
            
    while(True):
        try:
            cantidad = float(input(f"Ingrese la cantidad del producto {producto}: "))
            if cantidad > 0: 
                break
            print("❌ La cantidad no puede ser negativo o 0.")
        except ValueError:
            print("❌ Error: Cantidad debe ser números.") 
    
    return Detalle(producto,precio,cantidad)