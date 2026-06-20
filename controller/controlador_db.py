import sqlite3
import sys
import os
from classes import Venta,Detalle





def obtener_ruta_base():
    """
    Devuelve la ruta correcta tanto si estamos en desarrollo (Python)
    como si estamos en producción (.exe congelado).
    """
    if getattr(sys, 'frozen', False):
        # SI ESTAMOS EN MODO .EXE
        # sys.executable es la ruta del archivo .exe
        return os.path.dirname(sys.executable)
    else:
        # SI ESTAMOS EN MODO SCRIPT .PY
        # Usamos __file__ como veníamos haciendo
        # Nota: Ajusta esto según dónde esté este archivo (controller o raiz)
        return os.path.dirname(os.path.abspath(__file__))

# --- APLICANDO LA LÓGICA ---

RUTA_BASE = obtener_ruta_base()


if not getattr(sys, 'frozen', False):
     # Solo subimos de nivel si estamos en modo desarrollo (.py)
     RUTA_BASE = os.path.dirname(RUTA_BASE)

# Ahora definimos la carpeta database
CARPETA_DB = os.path.join(RUTA_BASE, "database")
DB_NAME = os.path.join(CARPETA_DB, "ventas.db")

# Creación segura de carpeta
if not os.path.exists(CARPETA_DB):
    os.makedirs(CARPETA_DB)

print(f"DEBUG: La base de datos estará en: {DB_NAME}")

def crear_tabla():
    #! Variables para trabajar con la base de datos
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
         #? Tabla VENTAS
         #!Agregar atributos
        c.execute("""CREATE TABLE IF NOT EXISTS ventas (
                id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT NOT NULL,
                telefono INTEGER,
                referencia TEXT,
                fecha DATE DEFAULT (datetime('now','localtime')),
                total REAL
                )
                """)
        
        #? Tabla Detalle relacionada con la tabla ventas
        #!Agregar atributos
        c.execute("""CREATE TABLE IF NOT EXISTS detalles(
                id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
                id_venta INTEGER,
                producto TEXT,
                precio REAL,
                cantidad REAL,
                FOREIGN KEY (id_venta) REFERENCES ventas(id_venta)
                )
                """)
        
        #?Crear tabla clientes,direcciones_cliente,encargado_obra

        conn.commit()
        print("✅ Base de datos verificada/creada correctamente.")
    except sqlite3.Error as e:

        print(f"Hubo un error en la base de datos: {e}")
    finally:
        conn.close()

def guardar_venta(obj_venta):
    #! Variables para trabajar con la base de datos
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        #!Ver que pasa si es una venta estandar 
        #*Cargamos los datos a sus tablas, no cargamos id o fecha porque es automatico
        c.execute("INSERT INTO ventas (cliente, telefono, referencia, total) VALUES (:name_cliente,:num_cliente,:ref_venta,:monto_total)",{
            "name_cliente":obj_venta.name_cliente,
            "num_cliente":obj_venta.num_cliente,
            "ref_venta":obj_venta.ref_venta,
            "monto_total":obj_venta.monto_total,})
        
        id_ventas_generado = c.lastrowid
        print(f"ID DE VENTA GENERADO: {id_ventas_generado}")
        #!Hay que modificar porque hay que llamar al obj detalle relacionado al objeto venta para desarmar la lista de producto esto obliga a acmodar todas las variabesl
        for detalle in obj_venta.lista_detalle_venta:
            #*Cargamos los datos "detalle" de la venta a la tabla detalles
            c.execute("INSERT INTO detalles (id_venta, producto, precio, cantidad) VALUES (:id_venta,:producto,:precio,:cantidad)",{
                    "id_venta":id_ventas_generado,
                    "producto":detalle.producto,
                    "precio":detalle.precio,
                    "cantidad":detalle.cantidad})
        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Hubo un error guardando la venta {e}")
        return False
    finally:
        conn.close()