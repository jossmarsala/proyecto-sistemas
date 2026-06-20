from classes.Venta import Venta



def iniciar_venta():
        
        while(True):
            name_cliente =  input("Ingrese el nombre del cliente: ").strip()

            if name_cliente:
                break
            print("❌ Error: El nombre no puede estar vacío.")
        while(True):
            try:
                entrada_num = input(f"Ingrese el numero de telefono del cliente {name_cliente}: ")
                num_cliente = int(entrada_num)
                break
            except ValueError:
                print(f"El numero de telefono tiene que ser enteramente numerico, sin ningun signo añadido")

        while(True):
            ref_venta = input("Ingrese una referencia de la venta: ").strip()
            if ref_venta:
                break
            print("❌ Error: La referencia es obligatoria.")
        print("✅ Datos de cabecera cargados correctamente.")
        return Venta(name_cliente, num_cliente, ref_venta)


def agregar_detalle(obj_venta,obj_detalle):
    obj_venta.agregar_detalle(obj_detalle)
    print(f"✅ Agregado: {obj_detalle.producto} | Subtotal: ${obj_detalle.sub_total}")