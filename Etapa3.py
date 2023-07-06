import sqlite3
from flask import Flask,  jsonify, request
from flask_cors import CORS


# Configurar la conexión a la base de datos SQLite
DATABASE = 'nomina.db'

def get_db_connection():
    print("Obteniendo conexión...") # Para probar que se ejecuta la función
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Crear la tabla 'clientes' si no existe
def create_table():
    print("Creando tabla clientes...") # Para probar que se ejecuta la función
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            cuit INTEGER PRIMARY KEY,
            razonSocial TEXT NOT NULL,
            direccion TEXT NOT NULL,
            contacto INTEGER NOT NULL
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

# Verificar si la base de datos existe, si no, crearla y crear la tabla
def create_database():
    print("Creando la BD...") # Para probar que se ejecuta la función
    conn = sqlite3.connect(DATABASE)
    conn.close()
    create_table()

# Crear la base de datos y la tabla si no existen
create_database()

# -------------------------------------------------------------------
# Definimos la clase "Cliente"
# -------------------------------------------------------------------
class Cliente:
    def __init__(self, cuit, razonSocial, direccion, contacto):
        self.cuit = cuit
        self.razonSocial = razonSocial
        self.direccion = direccion
        self.contacto = contacto

    def modificar(self, nueva_razonSocial, nueva_direccion, nuevo_contacto):
        self.razonSocial = nueva_razonSocial
        self.direccion = nueva_direccion
        self.contacto = nuevo_contacto


# -------------------------------------------------------------------
# Definimos la clase "Nomina"
# -------------------------------------------------------------------
class Nomina:
    def __init__(self):
        self.conexion = get_db_connection()
        self.cursor = self.conexion.cursor()

    def agregar_cliente(self, cuit, razonSocial, direccion, contacto):
        cliente_existente = self.consultar_cliente(cuit)
        if cliente_existente:
            return jsonify({'message': 'Ya existe un cliente con ese código.'}), 400

        #nuevo_cliente = Cliente(cuit, razonSocial, direccion, contacto)
        self.cursor.execute("INSERT INTO clientes VALUES (?, ?, ?, ?)", (cuit, razonSocial, direccion, contacto))
        self.conexion.commit()
        return jsonify({'message': 'Cliente agregado correctamente.'}), 200

    def consultar_cliente(self, cuit):
        self.cursor.execute("SELECT * FROM clientes WHERE cuit = ?", (cuit,))
        row = self.cursor.fetchone()
        if row:
            cuit, razonSocial, direccion, contacto = row
            return Cliente(cuit, razonSocial, direccion, contacto)
        return None

    def modificar_cliente(self, cuit, nueva_razonSocial, nueva_direccion, nuevo_contacto):
        cliente = self.consultar_cliente(cuit)
        if cliente:
            cliente.modificar(nueva_razonSocial, nueva_direccion, nuevo_contacto)
            self.cursor.execute("UPDATE clientes SET razonSocial = ?, direccion = ?, contacto = ? WHERE cuit = ?",
                                (nueva_razonSocial, nueva_direccion, nuevo_contacto, cuit))
            self.conexion.commit()
            return jsonify({'message': 'Cliente modificado correctamente.'}), 200
        return jsonify({'message': 'Cliente no encontrado.'}), 404

    def listar_clientes(self):
        self.cursor.execute("SELECT * FROM clientes")
        rows = self.cursor.fetchall()
        clientes = []
        for row in rows:
            cuit, razonSocial, direccion, contacto = row
            cliente = {'cuit': cuit, 'razonSocial': razonSocial, 'direccion': direccion, 'contacto': contacto}
            clientes.append(cliente)
        return jsonify(clientes), 200

    def eliminar_cliente(self, cuit):
        self.cursor.execute("DELETE FROM clientes WHERE cuit = ?", (cuit,))
        if self.cursor.rowcount > 0:
            self.conexion.commit()
            return jsonify({'message': 'Cliente eliminado correctamente.'}), 200
        return jsonify({'message': 'Cliente no encontrado.'}), 404


# -------------------------------------------------------------------
# Definimos la clase "Carrito"
# -------------------------------------------------------------------
class Carrito:
    def __init__(self):
        self.conexion = get_db_connection()
        self.cursor = self.conexion.cursor()
        self.items = []

    def agregar(self, cuit, direccion, nomina):
        cliente = nomina.consultar_cliente(cuit)
        if cliente is None:
            return jsonify({'message': 'El cliente no existe.'}), 404
        if cliente.direccion < direccion:
            return jsonify({'message': 'direccion en stock insuficiente.'}), 400

        for item in self.items:
            if item.cuit == cuit:
                item.direccion += direccion
                self.cursor.execute("UPDATE clientes SET direccion = direccion - ? WHERE cuit = ?",
                                    (direccion, cuit))
                self.conexion.commit()
                return jsonify({'message': 'Cliente agregado al carrito correctamente.'}), 200

        nuevo_item = Cliente(cuit, cliente.razonSocial, direccion, cliente.contacto)
        self.items.append(nuevo_item)
        self.cursor.execute("UPDATE clientes SET direccion = direccion - ? WHERE cuit = ?",
                            (direccion, cuit))
        self.conexion.commit()
        return jsonify({'message': 'Cliente agregado al carrito correctamente.'}), 200

    def quitar(self, cuit, direccion, nomina):
        for item in self.items:
            if item.cuit == cuit:
                if direccion > item.direccion:
                    return jsonify({'message': 'direccion a quitar mayor a la direccion en el carrito.'}), 400
                item.direccion -= direccion
                if item.direccion == 0:
                    self.items.remove(item)
                self.cursor.execute("UPDATE clientes SET direccion = direccion + ? WHERE cuit = ?",
                                    (direccion, cuit))
                self.conexion.commit()
                return jsonify({'message': 'Cliente quitado del carrito correctamente.'}), 200

        return jsonify({'message': 'El cliente no se encuentra en el carrito.'}), 404

    def mostrar(self):
        clientes_carrito = []
        for item in self.items:
            cliente = {'cuit': item.cuit, 'razonSocial': item.razonSocial, 'direccion': item.direccion,
                        'contacto': item.contacto}
            clientes_carrito.append(cliente)
        return jsonify(clientes_carrito), 200


# -------------------------------------------------------------------
# Configuración y rutas de la API Flask
# -------------------------------------------------------------------
#1)	Importación de los módulos y creación de la aplicación Flask

app = Flask(__name__)
CORS(app)

carrito = Carrito()         # Instanciamos un carrito
nomina = Nomina()   # Instanciamos un nomina

# 2 - Ruta para obtener los datos de un cliente según su código
# GET: envía la información haciéndola visible en la URL de la página web.
@app.route('/clientes/<int:cuit>', methods=['GET'])
def obtener_cliente(cuit):
    cliente = nomina.consultar_cliente(cuit)
    if cliente:
        return jsonify({
            'cuit': cliente.cuit,
            'razonSocial': cliente.razonSocial,
            'direccion': cliente.direccion,
            'contacto': cliente.contacto
        }), 200
    return jsonify({'message': 'Cliente no encontrado.'}), 404

# 3 - Ruta para obtener la lista de clientes del nomina
@app.route('/clientes', methods=['GET'])
def obtener_clientes():
    return nomina.listar_clientes()

# 4 - Ruta para agregar un cliente al nomina
# POST: envía la información ocultándola del usuario.
@app.route('/clientes', methods=['POST'])
def agregar_cliente():
    cuit = request.json.get('cuit')
    razonSocial = request.json.get('razonSocial')
    direccion = request.json.get('direccion')
    contacto = request.json.get('contacto')
    return nomina.agregar_cliente(cuit, razonSocial, direccion, contacto)

# 5 - Ruta para modificar un cliente del nomina
# PUT: permite actualizar información.
@app.route('/clientes/<int:cuit>', methods=['PUT'])
def modificar_cliente(cuit):
    nueva_razonSocial = request.json.get('razonSocial')
    nueva_direccion = request.json.get('direccion')
    nuevo_contacto = request.json.get('contacto')
    return nomina.modificar_cliente(cuit, nueva_razonSocial, nueva_direccion, nuevo_contacto)

# 6 - Ruta para eliminar un cliente del nomina
# DELETE: permite eliminar información.
@app.route('/clientes/<int:cuit>', methods=['DELETE'])
def eliminar_cliente(cuit):
    return nomina.eliminar_cliente(cuit)

# 7 - Ruta para agregar un cliente al carrito
@app.route('/carrito', methods=['POST'])
def agregar_carrito():
    cuit = request.json.get('cuit')
    direccion = request.json.get('direccion')
    nomina = Nomina()
    return carrito.agregar(cuit, direccion, nomina)

# 8 - Ruta para quitar un cliente del carrito
@app.route('/carrito', methods=['DELETE'])
def quitar_carrito():
    cuit = request.json.get('cuit')
    direccion = request.json.get('direccion')
    nomina = Nomina()
    return carrito.quitar(cuit, direccion, nomina)

# 9 - Ruta para obtener el contenido del carrito
@app.route('/carrito', methods=['GET'])
def obtener_carrito():
    return carrito.mostrar()

# 10 - Ruta para obtener el index
@app.route('/')
def index():
    return 'API de Nomina'

# Finalmente, si estamos ejecutando este archivo, lanzamos app.
if __name__ == '__main__':
    app.run()