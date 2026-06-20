# Requerimientos del Sistema. NOMBRE DE MARCA: FARO.
**Proyecto:** Sistema de Control de Inventario y Proyección de Negocio

## 1. Visión General
Desarrollo de una herramienta integral web para una pyme ferretera. Se divide en dos módulos centrales:
1. **Núcleo transaccional:** Registro concurrente de ventas, actualización de stock en tiempo real y administración de cuentas corrientes.
2. **Módulo analítico y gerencial (DSS):** Dashboard de métricas, predicción de quiebres de stock y simulación de escenarios empresariales (What-If).

## 2. Límites y Alcances (EXCLUSIONES CRÍTICAS)
Para mantener el foco del desarrollo, el sistema **NO DEBE** incluir:
* **Facturación Fiscal Automática:** NO hay integración automática vía API con servidores de ARCA/AFIP para validar comprobantes electrónicos.
* **Gestión Automática de Proveedores:** NO realiza órdenes de compra automáticas ni pagos directos (solo emite alertas de stock mínimo).
* **Venta al Público (E-commerce):** Uso exclusivo interno en mostrador y administración. NO incluye tienda online B2C.

## 3. Arquitectura y Stack Tecnológico
* **Arquitectura:** Modelo de tres capas (Frontend, Lógica de Negocio, Persistencia). Multiplataforma (acceso vía navegador web).
* **Frontend:** HTML, CSS, JavaScript. Diseño de interfaz UI modular tipo "Bento Box" enfocado en una estética minimalista, clara y sin sobrecarga cognitiva.
* **Backend / Procesamiento:** Python (para lógica del servidor, cálculos matemáticos y motor de simulación).
* **Base de Datos:** Relacional (MySQL / PostgreSQL).
* **Infraestructura:** Alojamiento en Cloud Server (hosting en la nube). Periféricos locales: Ticketeras térmicas en sucursales.

## 4. Actores del Sistema
* **Vendedor:** Usuario operativo en el mostrador.
* **Supervisor:** Administrador de la sucursal.
* **Gerente General:** Dueño/Alta gerencia, encargado de la estrategia y simulaciones.

## 5. Casos de Uso Principales
* **CU01 - Registrar Venta:** Carga de productos al carrito, validación de stock, selección de pago (Efectivo/Tarjeta/Cuenta Corriente) y descuento concurrente de stock.
* **CU02 - Emitir Facturación:** Extensión del registro de venta (emisión de comprobante interno).
* **CU03 - Buscar Producto:** Buscador ágil (tiempo de respuesta < 3 segundos) con filtros combinados.
* **CU04 - Administrar Cuenta Corriente:** Gestión de deudas, registro de cargos/pagos y validación de límites de crédito (Supervisor).
* **CU05 - Actualizar Precios Globales:** Ajuste masivo de costos por inflación (Supervisor).
* **CU06 - Consultar Alertas:** Generación de alertas visuales rojas por stock mínimo perforado o límite de crédito excedido.
* **CU07 - Proyectar Quiebre de Stock:** Visualización de fecha estimada de agotamiento de producto (Gerencia).
* **CU08 - Simular Escenarios (What-If):** Alteración de variables (inflación/demanda) para proyectar rentabilidad (Gerencia).

## 6. Lógica de Negocio y Algoritmos Específicos
### 6.1 Motor de Predicción (Quiebre de Stock)
* **Fórmula Matemática:** `Dias_Restantes = Stock_Actual / Promedio_Ventas_Diarias`
* **Inputs:** Cruce de tabla `Detalle_Venta` (filtrando últimos 30 o 60 días para la tendencia actual) y `Stock_Sucursal`.
* **Output esperado:** Payload/JSON con ID del producto, días estimados restantes y un flag de alerta (si los días son menores al tiempo de reposición del proveedor).

### 6.2 Simulador de Escenarios (Módulo What-If)
* **Inputs de Usuario (Frontend):** Sliders para variables continuas (ej. Porcentaje de inflación estimada, Caída/Aumento de demanda de -50% a +50%) e inputs numéricos (costos fijos).
* **Lógica Backend (Python):** El motor debe clonar la base de precios actuales **en memoria** (sin mutar la base de datos de producción), aplicar las fórmulas de proyección y devolver la nueva rentabilidad.
* **Visualización:** Gráficos de líneas (ingresos actuales vs simulados) y tarjetas de KPI con colores semánticos (verde = positivo, rojo = riesgo).

## 7. Modelo de Datos (Entidades Clave)
Debe contemplarse integridad referencial para el DER:
* **Producto:** id_producto, sku, nombre, categoria, precio_costo, precio_venta, id_proveedor.
* **Stock_Sucursal:** id_producto, id_sucursal, cantidad_actual, stock_minimo_seguridad.
* **Venta:** id_venta, id_cliente, id_usuario, id_sucursal, fecha_hora, total, estado.
* **Detalle_Venta:** id_detalle, id_venta, id_producto, cantidad, precio_unitario_historico, subtotal.
* **Cliente:** id_cliente, cuit_dni, nombre, saldo_cuenta_corriente, limite_credito, notas.
* **Cuenta_Corriente:** Gestiona `limiteCredito`, `saldoActual`, y ejecuta `validarLimite()`.
* **Usuario:** id_usuario, nombre, rol, id_sucursal.
* **Sucursal:** id_sucursal, nombre, direccion.
* **Alerta:** tipo_alerta, mensaje, dispararNotificacion().
* **Simulador_Escenario:** inflacion_estimada, variacion_demanda.

## 8. Requisitos No Funcionales y Despliegue
* **Implementación:** Método Piloto (despliegue inicial aislado en Sucursal 2).
* **Migración de Datos:** Es mandatorio un script de importación para poblar la BD relacional con los registros manuales/planillas actuales.
* **Backups:** Ejecución de copias de seguridad automáticas de la BD de forma diaria al cierre operativo.

## 9. Restricciones de Calidad de Código (Constraints)
* **Simplicidad y Legibilidad Humana (Prioridad Alta):** El código fuente generado debe ser estrictamente simple, lineal e intuitivo. 
* **Cero Sobreingeniería:** Queda absolutamente prohibido utilizar patrones de diseño excesivamente abstractos, meta-programación, librerías de terceros innecesarias o estructuras complejas (código "clever"). 
* **Enfoque Académico:** El código debe reflejar el estilo de un desarrollador junior o estudiante universitario avanzado. Se debe priorizar que el código sea fácil de explicar a terceros por encima de la optimización extrema de rendimiento.
* **Documentación Explicativa:** Todas las funciones, componentes y cálculos lógicos (especialmente en el backend de Python) deben incluir comentarios claros en español que expliquen el *por qué* y el *cómo* funcionan paso a paso.
