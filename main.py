from controller import controlador_db, controlador_venta,controlador_detalle
from exporter.exportar_excel import exportar_datos_a_excel
import sys

def menu_principal():

    controlador_db.crear_tabla()

    venta_actual = None
    while True:

        print("\n" + "="*30)
        print("   SISTEMA DE GESTIÓN DE VENTAS")
        print("="*30)

        
        if venta_actual:
            print(f"Venta activa: {venta_actual.name_cliente} | Items: {len(venta_actual.lista_detalle_venta)}")
        else:
            print("No hay venta activa")
    
        print("\n1. 🆕 Iniciar Nueva Venta")
        print("2. ➕ Agregar Producto")
        print("3. 💾 Finalizar y Guardar")
        print("4. ❌ Cancelar Venta Actual")
        print("5. 📊 Exportar a excel")
        print("0. 🚪 Salir")
        
        opcion = input("\nElige una opción: ").strip()

        match opcion:

            case "1":
                if venta_actual:
                    print("Ya tenes una venta activa, finalizala para crear otra")
                else:
                    venta_actual = controlador_venta.iniciar_venta()
            case "2":
                if venta_actual:
                    nuevo_detalle = controlador_detalle.crear_detalle(venta_actual)
                    controlador_venta.agregar_detalle(venta_actual,nuevo_detalle)
                else:
                    print("Primero debes iniciar una venta para agregar productos")
            case "3":
                if venta_actual and len(venta_actual.lista_detalle_venta) > 0:
                    print(f"Total a pagar: {venta_actual.monto_total}")
                    confirmar = input("Confirmar guardado s/n: ").lower()
                    if confirmar == "s":
                        exito = controlador_db.guardar_venta(venta_actual)
                        if exito:
                            venta_actual = None
                            print("Venta cargada")
                else:
                    print("No hay venta activa o esta vacia")
            case "4":
                if venta_actual:
                    confirmar = input("Esta seguro de cancelar la venta? s/n: ").lower()
                    if confirmar == "s":
                        venta_actual = None
                        print("Venta descartada")
                else:
                    print("No hay nada que descartar")
            case "5":
                exportar_datos_a_excel(controlador_db.DB_NAME)
            case "0":
                print("Saliendo del sistema....")
                sys.exit()
            case _:
                print("❌ Opción no válida. Por favor elige entre 1 y 5.")

if __name__ == "__main__":

    menu_principal()
