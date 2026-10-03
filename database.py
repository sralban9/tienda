import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = "tienda.db"


# ==========================================================
# CONEXIÓN
# ==========================================================

def conectar():
    conexion = sqlite3.connect(DATABASE)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


# ==========================================================
# CREAR TABLAS
# ==========================================================

def crear_tablas():

    conexion = conectar()
    cursor = conexion.cursor()

    # ------------------------------------------------------
    # USUARIOS
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'cliente',
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ------------------------------------------------------
    # CATEGORÍAS
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT
        )
    """)

    # ------------------------------------------------------
    # PRODUCTOS
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            imagen TEXT,
            categoria_id INTEGER,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (categoria_id)
                REFERENCES categorias(id)
                ON DELETE SET NULL
        )
    """)

    # ------------------------------------------------------
    # CARRITO
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carrito (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL DEFAULT 1,

            UNIQUE(usuario_id, producto_id),

            FOREIGN KEY (usuario_id)
                REFERENCES usuarios(id)
                ON DELETE CASCADE,

            FOREIGN KEY (producto_id)
                REFERENCES productos(id)
                ON DELETE CASCADE
        )
    """)

    # ------------------------------------------------------
    # PEDIDOS
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            total REAL NOT NULL,
            estado TEXT NOT NULL DEFAULT 'pendiente',
            fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (usuario_id)
                REFERENCES usuarios(id)
                ON DELETE CASCADE
        )
    """)

    # ------------------------------------------------------
    # DETALLE DE PEDIDOS
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio REAL NOT NULL,

            FOREIGN KEY (pedido_id)
                REFERENCES pedidos(id)
                ON DELETE CASCADE,

            FOREIGN KEY (producto_id)
                REFERENCES productos(id)
                ON DELETE CASCADE
        )
    """)

    conexion.commit()
    conexion.close()


# ==========================================================
# USUARIOS
# ==========================================================

def crear_usuario(nombre, email, password, rol="cliente"):

    conexion = conectar()
    cursor = conexion.cursor()

    password_hash = generate_password_hash(password)

    try:

        cursor.execute("""
            INSERT INTO usuarios
            (nombre, email, password, rol)
            VALUES (?, ?, ?, ?)
        """, (
            nombre,
            email,
            password_hash,
            rol
        ))

        conexion.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conexion.close()


def buscar_usuario(email):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT *
        FROM usuarios
        WHERE email = ?
    """, (email,))

    usuario = cursor.fetchone()

    conexion.close()

    return usuario


def obtener_usuario_por_id(usuario_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT *
        FROM usuarios
        WHERE id = ?
    """, (usuario_id,))

    usuario = cursor.fetchone()

    conexion.close()

    return usuario


def verificar_usuario(email, password):

    usuario = buscar_usuario(email)

    if usuario:

        if check_password_hash(
            usuario["password"],
            password
        ):
            return usuario

    return None


def obtener_usuarios():

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, nombre, email, rol, fecha_registro
        FROM usuarios
        ORDER BY id DESC
    """)

    usuarios = cursor.fetchall()

    conexion.close()

    return usuarios


# ==========================================================
# CATEGORÍAS
# ==========================================================

def agregar_categoria(nombre, descripcion=""):

    conexion = conectar()
    cursor = conexion.cursor()

    try:

        cursor.execute("""
            INSERT INTO categorias
            (nombre, descripcion)
            VALUES (?, ?)
        """, (
            nombre,
            descripcion
        ))

        conexion.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conexion.close()


def obtener_categorias():

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT *
        FROM categorias
        ORDER BY nombre
    """)

    categorias = cursor.fetchall()

    conexion.close()

    return categorias


# ==========================================================
# PRODUCTOS
# ==========================================================

def agregar_producto(
    nombre,
    descripcion,
    precio,
    stock,
    imagen="",
    categoria_id=None
):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO productos
        (
            nombre,
            descripcion,
            precio,
            stock,
            imagen,
            categoria_id
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        nombre,
        descripcion,
        precio,
        stock,
        imagen,
        categoria_id
    ))

    conexion.commit()

    producto_id = cursor.lastrowid

    conexion.close()

    return producto_id


def obtener_productos():

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            productos.*,
            categorias.nombre AS categoria
        FROM productos

        LEFT JOIN categorias
        ON productos.categoria_id = categorias.id

        ORDER BY productos.id DESC
    """)

    productos = cursor.fetchall()

    conexion.close()

    return productos


def obtener_producto(producto_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            productos.*,
            categorias.nombre AS categoria
        FROM productos

        LEFT JOIN categorias
        ON productos.categoria_id = categorias.id

        WHERE productos.id = ?
    """, (producto_id,))

    producto = cursor.fetchone()

    conexion.close()

    return producto


def actualizar_producto(
    producto_id,
    nombre,
    descripcion,
    precio,
    stock,
    imagen="",
    categoria_id=None
):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE productos

        SET
            nombre = ?,
            descripcion = ?,
            precio = ?,
            stock = ?,
            imagen = ?,
            categoria_id = ?

        WHERE id = ?
    """, (
        nombre,
        descripcion,
        precio,
        stock,
        imagen,
        categoria_id,
        producto_id
    ))

    conexion.commit()

    conexion.close()


def eliminar_producto(producto_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        DELETE FROM productos
        WHERE id = ?
    """, (producto_id,))

    conexion.commit()

    conexion.close()


# ==========================================================
# CARRITO
# ==========================================================

def agregar_al_carrito(
    usuario_id,
    producto_id,
    cantidad=1
):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT *
        FROM carrito
        WHERE usuario_id = ?
        AND producto_id = ?
    """, (
        usuario_id,
        producto_id
    ))

    item = cursor.fetchone()

    if item:

        cursor.execute("""
            UPDATE carrito

            SET cantidad = cantidad + ?

            WHERE usuario_id = ?
            AND producto_id = ?
        """, (
            cantidad,
            usuario_id,
            producto_id
        ))

    else:

        cursor.execute("""
            INSERT INTO carrito
            (
                usuario_id,
                producto_id,
                cantidad
            )
            VALUES (?, ?, ?)
        """, (
            usuario_id,
            producto_id,
            cantidad
        ))

    conexion.commit()

    conexion.close()


def obtener_carrito(usuario_id):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            carrito.id,
            carrito.producto_id,
            carrito.cantidad,
            productos.nombre,
            productos.precio,
            productos.imagen
        FROM carrito
        INNER JOIN productos
            ON carrito.producto_id = productos.id
        WHERE carrito.usuario_id = ?
    """, (usuario_id,))

    productos = cursor.fetchall()

    conn.close()

    return productos


def actualizar_carrito(
    usuario_id,
    producto_id,
    cantidad
):

    conexion = conectar()
    cursor = conexion.cursor()

    if cantidad <= 0:

        cursor.execute("""
            DELETE FROM carrito

            WHERE usuario_id = ?
            AND producto_id = ?
        """, (
            usuario_id,
            producto_id
        ))

    else:

        cursor.execute("""
            UPDATE carrito

            SET cantidad = ?

            WHERE usuario_id = ?
            AND producto_id = ?
        """, (
            cantidad,
            usuario_id,
            producto_id
        ))

    conexion.commit()

    conexion.close()


def eliminar_del_carrito(
    usuario_id,
    producto_id
):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        DELETE FROM carrito

        WHERE usuario_id = ?
        AND producto_id = ?
    """, (
        usuario_id,
        producto_id
    ))

    conexion.commit()

    conexion.close()


def vaciar_carrito(usuario_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        DELETE FROM carrito
        WHERE usuario_id = ?
    """, (usuario_id,))

    conexion.commit()

    conexion.close()


def calcular_total_carrito(usuario_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            SUM(
                productos.precio *
                carrito.cantidad
            )

        FROM carrito

        INNER JOIN productos
        ON carrito.producto_id = productos.id

        WHERE carrito.usuario_id = ?
    """, (usuario_id,))

    resultado = cursor.fetchone()[0]

    conexion.close()

    return resultado or 0


# ==========================================================
# PEDIDOS
# ==========================================================

def crear_pedido(usuario_id):

    conexion = conectar()
    cursor = conexion.cursor()

    try:

        # Obtener carrito

        cursor.execute("""
            SELECT
                carrito.producto_id,
                carrito.cantidad,
                productos.precio,
                productos.stock

            FROM carrito

            INNER JOIN productos
            ON carrito.producto_id = productos.id

            WHERE carrito.usuario_id = ?
        """, (usuario_id,))

        productos = cursor.fetchall()

        if not productos:

            return None

        total = 0

        # Comprobar stock

        for producto in productos:

            if producto["cantidad"] > producto["stock"]:

                conexion.rollback()

                return None

            total += (
                producto["precio"] *
                producto["cantidad"]
            )

        # Crear pedido

        cursor.execute("""
            INSERT INTO pedidos
            (
                usuario_id,
                total,
                estado
            )
            VALUES (?, ?, 'pendiente')
        """, (
            usuario_id,
            total
        ))

        pedido_id = cursor.lastrowid

        # Crear detalles

        for producto in productos:

            cursor.execute("""
                INSERT INTO detalle_pedidos
                (
                    pedido_id,
                    producto_id,
                    cantidad,
                    precio
                )
                VALUES (?, ?, ?, ?)
            """, (
                pedido_id,
                producto["producto_id"],
                producto["cantidad"],
                producto["precio"]
            ))

            # Descontar stock

            cursor.execute("""
                UPDATE productos

                SET stock = stock - ?

                WHERE id = ?
            """, (
                producto["cantidad"],
                producto["producto_id"]
            ))

        # Vaciar carrito

        cursor.execute("""
            DELETE FROM carrito
            WHERE usuario_id = ?
        """, (usuario_id,))

        conexion.commit()

        return pedido_id

    except Exception:

        conexion.rollback()

        raise

    finally:

        conexion.close()


def obtener_pedidos_usuario(usuario_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT *
        FROM pedidos

        WHERE usuario_id = ?

        ORDER BY fecha_pedido DESC
    """, (usuario_id,))

    pedidos = cursor.fetchall()

    conexion.close()

    return pedidos


def obtener_pedidos():

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            pedidos.*,
            usuarios.nombre,
            usuarios.email

        FROM pedidos

        INNER JOIN usuarios
        ON pedidos.usuario_id = usuarios.id

        ORDER BY pedidos.fecha_pedido DESC
    """)

    pedidos = cursor.fetchall()

    conexion.close()

    return pedidos


def obtener_detalles_pedido(pedido_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            detalle_pedidos.*,
            productos.nombre

        FROM detalle_pedidos

        INNER JOIN productos
        ON detalle_pedidos.producto_id = productos.id

        WHERE detalle_pedidos.pedido_id = ?
    """, (pedido_id,))

    detalles = cursor.fetchall()

    conexion.close()

    return detalles


def actualizar_estado_pedido(
    pedido_id,
    estado
):

    estados_validos = [
        "pendiente",
        "pagado",
        "enviado",
        "entregado",
        "cancelado"
    ]

    if estado not in estados_validos:
        return False

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE pedidos

        SET estado = ?

        WHERE id = ?
    """, (
        estado,
        pedido_id
    ))

    conexion.commit()

    conexion.close()

    return True


# ==========================================================
# DATOS INICIALES
# ==========================================================

def datos_iniciales():

    conexion = conectar()
    cursor = conexion.cursor()

    # ------------------------------------------
    # Categorías
    # ------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM categorias
    """)

    cantidad_categorias = cursor.fetchone()[0]

    if cantidad_categorias == 0:

        cursor.execute("""
            INSERT INTO categorias
            (nombre, descripcion)
            VALUES
            ('Tecnología', 'Productos tecnológicos'),
            ('Accesorios', 'Accesorios electrónicos'),
            ('Hogar', 'Productos para el hogar')
        """)

    conexion.commit()

    # ------------------------------------------
    # Productos
    # ------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM productos
    """)

    cantidad_productos = cursor.fetchone()[0]

    conexion.close()

    if cantidad_productos == 0:

        categorias = obtener_categorias()

        tecnologia_id = None
        accesorios_id = None

        for categoria in categorias:

            if categoria["nombre"] == "Tecnología":
                tecnologia_id = categoria["id"]

            elif categoria["nombre"] == "Accesorios":
                accesorios_id = categoria["id"]

        agregar_producto(
            "Laptop Lenovo",
            "Laptop para trabajo y estudio.",
            650.00,
            10,
            "https://images.unsplash.com/photo-1496181133206-80ce9b88a853",
            tecnologia_id
        )

        agregar_producto(
            "Smartphone",
            "Teléfono inteligente.",
            320.00,
            15,
            "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9",
            tecnologia_id
        )

        agregar_producto(
            "Auriculares",
            "Auriculares inalámbricos.",
            45.00,
            25,
            "https://images.unsplash.com/photo-1505740420928-5e560c06d30e",
            accesorios_id
        )

        agregar_producto(
            "Smartwatch",
            "Reloj inteligente.",
            80.00,
            12,
            "https://images.unsplash.com/photo-1523275335684-37898b6baf30",
            accesorios_id
        )


# ==========================================================
# CREAR ADMINISTRADOR
# ==========================================================

def crear_admin():

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id
        FROM usuarios
        WHERE email = ?
    """, ("admin@tienda.com",))

    admin = cursor.fetchone()

    conexion.close()

    if admin:
        return False

    return crear_usuario(
        "Administrador",
        "admin@tienda.com",
        "Admin123",
        "admin"
    )


# ==========================================================
# INICIALIZACIÓN
# ==========================================================

if __name__ == "__main__":

    crear_tablas()

    datos_iniciales()

    crear_admin()

    print("====================================")
    print(" BASE DE DATOS CREADA CORRECTAMENTE")
    print("====================================")
    print()
    print("Base de datos:", DATABASE)
    print()
    print("Administrador:")
    print("Correo: admin@tienda.com")
    print("Contraseña: Admin123")
    print()