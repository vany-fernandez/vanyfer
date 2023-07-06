import sqlite3

# Configurar la conexión a la base de datos SQLite
DATABASE = 'inventario.db'

def get_db_connection():
    print("Obteniendo conexión...") # Para probar que se ejecuta la función
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Crear la tabla 'productos' si no existe
def create_table():
    print("Creando tabla productos...") # Para probar que se ejecuta la función
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            codigo INTEGER PRIMARY KEY,
            descripcion TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio REAL NOT NULL
        ) ''')
    conn.commit()
    cursor.close()
    conn.close()

# Verificar si la base de datos existe, si no, crearla y crear la tabla
def create_database():
    print("Creando la BD...") # Para probar que se ejecuta la función
    conn = sqlite3.connect(DATABASE)
    conn.close()
    create_table()

# Programa principal
# Crear la base de datos y la tabla Productos si no existen
create_database()


# -------------------------------------------------------------------
# Definimos la clase "Producto"
# -------------------------------------------------------------------
class Producto:
    # Definimos el constructor e inicializamos los atributos de instancia
    def __init__(self, codigo, descripcion, cantidad, precio):
        self.codigo = codigo           # Código 
        self.descripcion = descripcion # Descripción
        self.cantidad = cantidad       # Cantidad disponible (stock)
        self.precio = precio           # Precio 

    # Este método permite modificar un producto.
    def modificar(self, nueva_descripcion, nueva_cantidad, nuevo_precio):
        self.descripcion = nueva_descripcion  # Modifica la descripción
        self.cantidad = nueva_cantidad        # Modifica la cantidad
        self.precio = nuevo_precio            # Modifica el precio


# -------------------------------------------------------------------
# Definimos la clase "Inventario"
# -------------------------------------------------------------------
class Inventario:
    def __init__(self):
        self.conexion = get_db_connection()
        self.cursor = self.conexion.cursor()

    def agregar_producto(self, codigo, descripcion, cantidad, precio):
        producto_existente = self.consultar_producto(codigo)
        if producto_existente:
            print("Ya existe un producto con ese código.")
            return False
        nuevo_producto = Producto(codigo, descripcion, cantidad, precio)
        sql = f'INSERT INTO productos VALUES ({codigo}, "{descripcion}", {cantidad}, {precio});'
        self.cursor.execute(sql)
        self.conexion.commit()
        return True

    def consultar_producto(self, codigo):
        sql = f'SELECT * FROM productos WHERE codigo = {codigo};'
        self.cursor.execute(sql)
        row = self.cursor.fetchone()
        if row:
            codigo, descripcion, cantidad, precio = row
            return Producto(codigo, descripcion, cantidad, precio)
        return False

    def modificar_producto(self, codigo, nueva_descripcion, nueva_cantidad, nuevo_precio):
        producto = self.consultar_producto(codigo)
        if producto:
            producto.modificar(nueva_descripcion, nueva_cantidad, nuevo_precio)
            sql = f'UPDATE productos SET descripcion = "{nueva_descripcion}", cantidad = {nueva_cantidad}, precio = {nuevo_precio} WHERE codigo = {codigo};' 
            print("-"*50)
            print(f'Producto modificado:\nCódigo: {producto.codigo}\nDescripción: {producto.descripcion}\nCantidad: {producto.cantidad}\nPrecio: {producto.precio}')
            self.cursor.execute(sql)
            self.conexion.commit()

    def eliminar_producto(self, codigo):
        sql = f'DELETE FROM productos WHERE codigo = {codigo};' 
        self.cursor.execute(sql)
        if self.cursor.rowcount > 0:
            print(f'Producto {codigo} eliminado.')
            self.conexion.commit()
        else:
            print(f'Producto {codigo} no encontrado.')

    def listar_productos(self):
        print("-"*50)
        print("INVENTARIO - Lista de productos:")
        print("Código\tDescripción\tCant\tPrecio")
        self.cursor.execute("SELECT * FROM productos")
        rows = self.cursor.fetchall()
        for row in rows:
            codigo, descripcion, cantidad, precio = row
            print(f'{codigo}\t{descripcion}\t{cantidad}\t{precio}')
        print("-"*50)



# -------------------------------------------------------------------
# Definimos la clase "Carrito"
# -------------------------------------------------------------------
class Carrito:
    def __init__(self):
        self.conexion = sqlite3.connect('inventario.db')  # Conexión a la BD
        self.cursor = self.conexion.cursor()
        self.items = []

    def agregar(self, codigo, cantidad, inventario):
        producto = inventario.consultar_producto(codigo)
        if producto is False:
            print("El producto no existe.")
            return False
        if producto.cantidad < cantidad:
            print("Cantidad en stock insuficiente.")
            return False

        for item in self.items:
            if item.codigo == codigo:
                item.cantidad += cantidad
                sql = f'UPDATE productos SET cantidad = cantidad - {cantidad}  WHERE codigo = {codigo};'
                self.cursor.execute(sql)
                self.conexion.commit()
                return True

        nuevo_item = Producto(codigo, producto.descripcion, cantidad, producto.precio)
        self.items.append(nuevo_item)
        sql = f'UPDATE productos SET cantidad = cantidad - {cantidad}  WHERE codigo = {codigo};'
        self.cursor.execute(sql)
        self.conexion.commit()
        return True

    def quitar(self, codigo, cantidad, inventario):
        for item in self.items:
            if item.codigo == codigo:
                if cantidad > item.cantidad:
                    print("Cantidad a quitar mayor a la cantidad en el carrito.")
                    return False
                item.cantidad -= cantidad
                print(f'Se ha/n eliminado {cantidad} ítem/s del producto {codigo} en el carrito.')
                if item.cantidad == 0:
                    self.items.remove(item)
                    print(f'Producto {codigo} eliminado del carrito.')
                sql = f'UPDATE productos SET cantidad = cantidad + {cantidad} WHERE codigo = {codigo};'
                self.cursor.execute(sql)
                self.conexion.commit()
                return True
    
    def mostrar(self):
        print("-"*50)
        print("CARRITO - Lista de productos:")
        print("Código\tDescripción\tCant\tPrecio")
        for item in self.items:
            print(f'{item.codigo}\t{item.descripcion}\t{item.cantidad}\t{item.precio}')
        print("-"*50)


# -------------------------------------------------------------------
# Ejemplo de uso de las clases y objetos definidos antes:
# -------------------------------------------------------------------
# Programa principal
# Crear la base de datos y la tabla si no existen
create_database()

# Crear una instancia de la clase Inventario
mi_inventario = Inventario()

# Crear una instancia de la clase Carrito
mi_carrito = Carrito()

# Crear 3 productos y agregarlos al inventario
mi_inventario.agregar_producto(1, 'Teclado USB 101 teclas', 10, 4500)
mi_inventario.agregar_producto(2, 'Mouse USB 3 botones', 5, 2500)
mi_inventario.agregar_producto(3, 'Monitor LCD 22 pulgadas', 15, 52500)

# Listar todos los productos del inventario
mi_inventario.listar_productos()

# Agregar 2 productos al carrito
mi_carrito.agregar(1, 2, mi_inventario) # Agregar 2 unidades del producto con código 1 al carrito
mi_carrito.agregar(3, 4, mi_inventario) # Agregar 1 unidad del producto con código 3 al carrito

# Listar todos los productos del carrito
mi_carrito.mostrar()

# Quitar 1 producto al carrito
mi_carrito.quitar (1, 1, mi_inventario) # Quitar 1 unidad del producto con código 1 al carrito

# Listar todos los productos del carrito
mi_carrito.mostrar()

# Mostramos el inventario
mi_inventario.listar_productos()















'''
# Clase inventario: Programa principal
# Crear una instancia de la clase Inventario
mi_inventario = Inventario() 

# Agregar productos 
mi_inventario.agregar_producto(1, 'Teclado USB 101 teclas', 10, 4500)
mi_inventario.agregar_producto(2, 'Mouse USB 3 botones', 5, 2500)
mi_inventario.agregar_producto(3, 'Monitor LCD 22 pulgadas', 15, 52500)
mi_inventario.agregar_producto(4, 'Monitor LCD 27 pulgadas', 25, 78500)
mi_inventario.agregar_producto(5, 'Mouse Pad color azul', 5, 500)

# Consultar un producto 
producto = mi_inventario.consultar_producto(30)
if producto != False:
    print(f'Producto encontrado:\nCódigo: {producto.codigo}\nDescripción: {producto.descripcion}\nCantidad: {producto.cantidad}\nPrecio: {producto.precio}')  
else:
    print("Producto no encontrado.")

# Modificar un producto 
mi_inventario.modificar_producto(3, 'Monitor LCD 24 pulgadas', 5, 62000)

# Listar todos los productos
mi_inventario.listar_productos()

# Eliminar un producto 
mi_inventario.eliminar_producto(2)

# Confirmamos que haya sido eliminado
mi_inventario.listar_productos()
'''


'''
# Programa principal
producto = Producto(1, 'Teclado USB 101 teclas', 10, 4500)
# Accedemos a los atributos del objeto
print(f'{producto.codigo} | {producto.descripcion} | {producto.cantidad} | {producto.precio}')
# Modificar los datos del producto
producto.modificar('Teclado Mecánico USB', 20, 4800) 
print(f'{producto.codigo} | {producto.descripcion} | {producto.cantidad} | {producto.precio}')
'''
