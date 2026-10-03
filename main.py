from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps

from database import (
    crear_tablas,

    # USUARIOS
    crear_usuario,
    buscar_usuario,
    verificar_usuario,
    obtener_usuario_por_id,
    obtener_usuarios,

    # CATEGORÍAS
    obtener_categorias,

    # PRODUCTOS
    agregar_producto,
    obtener_productos,
    obtener_producto,
    actualizar_producto,
    eliminar_producto,

    # CARRITO
    agregar_al_carrito,
    obtener_carrito,
    actualizar_carrito,
    eliminar_del_carrito,
    vaciar_carrito,
    calcular_total_carrito,

    # PEDIDOS
    crear_pedido,
    obtener_pedidos_usuario,
    obtener_pedidos,
    obtener_detalles_pedido,
    actualizar_estado_pedido,

    # DATOS INICIALES
    datos_iniciales,
    crear_admin
)


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

app = Flask(__name__)

app.secret_key = "mi-tienda-secreta-2026"


# ==========================================================
# USUARIO ACTUAL
# ==========================================================

def usuario_actual():

    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return None

    return obtener_usuario_por_id(usuario_id)


# ==========================================================
# PROTECCIÓN LOGIN
# ==========================================================

def login_requerido(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "usuario_id" not in session:

            flash(
                "Debes iniciar sesión para continuar.",
                "warning"
            )

            return redirect(url_for("login"))

        return func(*args, **kwargs)

    return wrapper


# ==========================================================
# PROTECCIÓN ADMIN
# ==========================================================

def es_admin():

    usuario = usuario_actual()

    if not usuario:
        return False

    return usuario["rol"] == "admin"


def admin_requerido(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "usuario_id" not in session:

            flash(
                "Debes iniciar sesión.",
                "warning"
            )

            return redirect(url_for("login"))

        if not es_admin():

            flash(
                "No tienes permisos para acceder.",
                "danger"
            )

            return redirect(url_for("inicio"))

        return func(*args, **kwargs)

    return wrapper


# ==========================================================
# INICIO
# ==========================================================

@app.route("/")
def inicio():

    productos = obtener_productos()
    categorias = obtener_categorias()

    return render_template(
        "index.html",
        productos=productos,
        categorias=categorias,
        usuario=usuario_actual()
    )


# ==========================================================
# PRODUCTOS
# ==========================================================

@app.route("/productos")
def productos():

    productos = obtener_productos()
    categorias = obtener_categorias()

    return render_template(
        "productos.html",
        productos=productos,
        categorias=categorias,
        usuario=usuario_actual()
    )


# ==========================================================
# DETALLE PRODUCTO
# ==========================================================

@app.route("/producto/<int:producto_id>")
def detalle_producto(producto_id):

    producto = obtener_producto(producto_id)

    if not producto:

        flash(
            "El producto no existe.",
            "danger"
        )

        return redirect(url_for("productos"))

    return render_template(
        "producto.html",
        producto=producto,
        usuario=usuario_actual()
    )


# ==========================================================
# REGISTRO
# ==========================================================

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirmar_password = request.form.get(
            "confirmar_password",
            ""
        )

        # Validaciones

        if not nombre or not email or not password:

            flash(
                "Todos los campos son obligatorios.",
                "danger"
            )

            return redirect(url_for("registro"))

        if password != confirmar_password:

            flash(
                "Las contraseñas no coinciden.",
                "danger"
            )

            return redirect(url_for("registro"))

        if len(password) < 6:

            flash(
                "La contraseña debe tener al menos 6 caracteres.",
                "warning"
            )

            return redirect(url_for("registro"))

        # Comprobar usuario

        usuario_existente = buscar_usuario(email)

        if usuario_existente:

            flash(
                "El correo electrónico ya está registrado.",
                "warning"
            )

            return redirect(url_for("registro"))

        # Crear usuario

        resultado = crear_usuario(
            nombre,
            email,
            password
        )

        if resultado:

            flash(
                "Cuenta creada correctamente.",
                "success"
            )

            return redirect(url_for("login"))

        flash(
            "No se pudo crear la cuenta.",
            "danger"
        )

    return render_template(
        "registro.html"
    )


# ==========================================================
# LOGIN
# ==========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        usuario = verificar_usuario(
            email,
            password
        )

        if usuario:

            session["usuario_id"] = usuario["id"]
            session["usuario_nombre"] = usuario["nombre"]
            session["usuario_rol"] = usuario["rol"]

            flash(
                f"Bienvenido, {usuario['nombre']}.",
                "success"
            )

            return redirect(
                url_for("inicio")
            )

        flash(
            "Correo o contraseña incorrectos.",
            "danger"
        )

    return render_template(
        "login.html"
    )


# ==========================================================
# CERRAR SESIÓN
# ==========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Sesión cerrada correctamente.",
        "success"
    )

    return redirect(
        url_for("inicio")
    )


# ==========================================================
# CARRITO
# ==========================================================

@app.route("/carrito")
def carrito():

    usuario_id = session.get("usuario_id")

    if not usuario_id:

        return render_template(
            "carrito.html",
            carrito=[],
            total=0,
            usuario=None
        )

    carrito_items = obtener_carrito(
        usuario_id
    )

    total = calcular_total_carrito(
        usuario_id
    )

    return render_template(
        "carrito.html",
        carrito=carrito_items,
        total=total,
        usuario=usuario_actual()
    )


# ==========================================================
# AGREGAR AL CARRITO
# ==========================================================

@app.route(
    "/agregar-carrito/<int:producto_id>",
    methods=["POST"]
)
@login_requerido
def agregar_carrito(producto_id):

    producto = obtener_producto(
        producto_id
    )

    if not producto:

        flash(
            "Producto no encontrado.",
            "danger"
        )

        return redirect(
            url_for("inicio")
        )

    if producto["stock"] <= 0:

        flash(
            "El producto está agotado.",
            "warning"
        )

        return redirect(
            url_for(
                "detalle_producto",
                producto_id=producto_id
            )
        )

    cantidad = request.form.get(
        "cantidad",
        default=1,
        type=int
    )

    if cantidad < 1:
        cantidad = 1

    if cantidad > producto["stock"]:

        flash(
            "No hay suficiente stock.",
            "warning"
        )

        return redirect(
            url_for(
                "detalle_producto",
                producto_id=producto_id
            )
        )

    agregar_al_carrito(
        session["usuario_id"],
        producto_id,
        cantidad
    )

    flash(
        f"{producto['nombre']} fue agregado al carrito.",
        "success"
    )

    return redirect(
        url_for("carrito")
    )


# ==========================================================
# ACTUALIZAR CARRITO
# ==========================================================

@app.route(
    "/actualizar-carrito/<int:producto_id>",
    methods=["POST"]
)
@login_requerido
def actualizar_carrito_route(producto_id):

    cantidad = request.form.get(
        "cantidad",
        type=int
    )

    if cantidad is None:

        flash(
            "Cantidad inválida.",
            "danger"
        )

        return redirect(
            url_for("carrito")
        )

    actualizar_carrito(
        session["usuario_id"],
        producto_id,
        cantidad
    )

    flash(
        "Carrito actualizado.",
        "success"
    )

    return redirect(
        url_for("carrito")
    )


# ==========================================================
# ELIMINAR PRODUCTO DEL CARRITO
# ==========================================================

@app.route(
    "/eliminar-carrito/<int:producto_id>",
    methods=["POST"]
)
@login_requerido
def eliminar_carrito(producto_id):

    eliminar_del_carrito(
        session["usuario_id"],
        producto_id
    )

    flash(
        "Producto eliminado del carrito.",
        "success"
    )

    return redirect(
        url_for("carrito")
    )


# ==========================================================
# VACIAR CARRITO
# ==========================================================

@app.route(
    "/vaciar-carrito",
    methods=["POST"]
)
@login_requerido
def vaciar_carrito_route():

    vaciar_carrito(
        session["usuario_id"]
    )

    flash(
        "Carrito vaciado correctamente.",
        "success"
    )

    return redirect(
        url_for("carrito")
    )


# ==========================================================
# CHECKOUT
# ==========================================================

@app.route(
    "/checkout",
    methods=["GET", "POST"]
)
@login_requerido
def checkout():

    usuario_id = session["usuario_id"]

    carrito_items = obtener_carrito(
        usuario_id
    )

    if not carrito_items:

        flash(
            "Tu carrito está vacío.",
            "warning"
        )

        return redirect(
            url_for("carrito")
        )

    total = calcular_total_carrito(
        usuario_id
    )

    if request.method == "POST":

        pedido_id = crear_pedido(
            usuario_id
        )

        if pedido_id:

            return redirect(
                url_for(
                    "pedido_exitoso",
                    pedido_id=pedido_id
                )
            )

        flash(
            "No se pudo crear el pedido. Revisa el stock disponible.",
            "danger"
        )

        return redirect(
            url_for("carrito")
        )

    return render_template(
        "checkout.html",
        carrito=carrito_items,
        total=total,
        usuario=usuario_actual()
    )


# ==========================================================
# PEDIDO EXITOSO
# ==========================================================

@app.route(
    "/pedido-exitoso/<int:pedido_id>"
)
@login_requerido
def pedido_exitoso(pedido_id):

    pedido = None

    pedidos_usuario = obtener_pedidos_usuario(
        session["usuario_id"]
    )

    for p in pedidos_usuario:

        if p["id"] == pedido_id:

            pedido = p
            break

    if not pedido:

        flash(
            "Pedido no encontrado.",
            "danger"
        )

        return redirect(
            url_for("pedidos")
        )

    detalles = obtener_detalles_pedido(
        pedido_id
    )

    return render_template(
        "pedido_exitoso.html",
        pedido=pedido,
        detalles=detalles,
        usuario=usuario_actual()
    )


# ==========================================================
# MIS PEDIDOS
# ==========================================================

@app.route("/pedidos")
@login_requerido
def pedidos():

    pedidos_usuario = obtener_pedidos_usuario(
        session["usuario_id"]
    )

    return render_template(
        "pedidos.html",
        pedidos=pedidos_usuario,
        usuario=usuario_actual()
    )


# ==========================================================
# ADMINISTRACIÓN
# ==========================================================

@app.route("/admin")
@admin_requerido
def admin_dashboard():

    productos = obtener_productos()
    usuarios = obtener_usuarios()
    pedidos_admin = obtener_pedidos()

    return render_template(
        "admin/dashboard.html",
        productos=productos,
        usuarios=usuarios,
        pedidos=pedidos_admin,
        usuario=usuario_actual()
    )


# ==========================================================
# ADMIN - PRODUCTOS
# ==========================================================

@app.route("/admin/productos")
@admin_requerido
def admin_productos():

    productos = obtener_productos()

    return render_template(
        "admin/productos.html",
        productos=productos,
        usuario=usuario_actual()
    )


# ==========================================================
# ADMIN - NUEVO PRODUCTO
# ==========================================================

@app.route(
    "/admin/productos/nuevo",
    methods=["GET", "POST"]
)
@admin_requerido
def admin_nuevo_producto():

    if request.method == "POST":

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        descripcion = request.form.get(
            "descripcion",
            ""
        ).strip()

        precio = request.form.get(
            "precio",
            type=float
        )

        stock = request.form.get(
            "stock",
            type=int
        )

        imagen = request.form.get(
            "imagen",
            ""
        ).strip()

        categoria_id = request.form.get(
            "categoria_id",
            type=int
        )

        if not nombre:

            flash(
                "El nombre del producto es obligatorio.",
                "danger"
            )

            return redirect(
                url_for("admin_nuevo_producto")
            )

        if precio is None or precio < 0:

            flash(
                "El precio no es válido.",
                "danger"
            )

            return redirect(
                url_for("admin_nuevo_producto")
            )

        if stock is None or stock < 0:

            flash(
                "El stock no es válido.",
                "danger"
            )

            return redirect(
                url_for("admin_nuevo_producto")
            )

        agregar_producto(
            nombre,
            descripcion,
            precio,
            stock,
            imagen,
            categoria_id
        )

        flash(
            "Producto creado correctamente.",
            "success"
        )

        return redirect(
            url_for("admin_productos")
        )

    categorias = obtener_categorias()

    return render_template(
        "admin/producto_form.html",
        producto=None,
        categorias=categorias,
        usuario=usuario_actual()
    )


# ==========================================================
# ADMIN - EDITAR PRODUCTO
# ==========================================================

@app.route(
    "/admin/productos/editar/<int:producto_id>",
    methods=["GET", "POST"]
)
@admin_requerido
def admin_editar_producto(producto_id):

    producto = obtener_producto(
        producto_id
    )

    if not producto:

        flash(
            "Producto no encontrado.",
            "danger"
        )

        return redirect(
            url_for("admin_productos")
        )

    if request.method == "POST":

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        descripcion = request.form.get(
            "descripcion",
            ""
        ).strip()

        precio = request.form.get(
            "precio",
            type=float
        )

        stock = request.form.get(
            "stock",
            type=int
        )

        imagen = request.form.get(
            "imagen",
            ""
        ).strip()

        categoria_id = request.form.get(
            "categoria_id",
            type=int
        )

        actualizar_producto(
            producto_id,
            nombre,
            descripcion,
            precio,
            stock,
            imagen,
            categoria_id
        )

        flash(
            "Producto actualizado correctamente.",
            "success"
        )

        return redirect(
            url_for("admin_productos")
        )

    categorias = obtener_categorias()

    return render_template(
        "admin/producto_form.html",
        producto=producto,
        categorias=categorias,
        usuario=usuario_actual()
    )


# ==========================================================
# ADMIN - ELIMINAR PRODUCTO
# ==========================================================

@app.route(
    "/admin/productos/eliminar/<int:producto_id>",
    methods=["POST"]
)
@admin_requerido
def admin_eliminar_producto(producto_id):

    eliminar_producto(
        producto_id
    )

    flash(
        "Producto eliminado correctamente.",
        "success"
    )

    return redirect(
        url_for("admin_productos")
    )


# ==========================================================
# ADMIN - USUARIOS
# ==========================================================

@app.route("/admin/usuarios")
@admin_requerido
def admin_usuarios():

    usuarios = obtener_usuarios()

    return render_template(
        "admin/usuarios.html",
        usuarios=usuarios,
        usuario=usuario_actual()
    )


# ==========================================================
# ADMIN - PEDIDOS
# ==========================================================

@app.route("/admin/pedidos")
@admin_requerido
def admin_pedidos():

    pedidos_admin = obtener_pedidos()

    return render_template(
        "admin/pedidos.html",
        pedidos=pedidos_admin,
        usuario=usuario_actual()
    )


# ==========================================================
# ADMIN - DETALLE PEDIDO
# ==========================================================

@app.route(
    "/admin/pedidos/<int:pedido_id>"
)
@admin_requerido
def admin_detalle_pedido(pedido_id):

    pedido = None

    pedidos_admin = obtener_pedidos()

    for p in pedidos_admin:

        if p["id"] == pedido_id:

            pedido = p
            break

    if not pedido:

        flash(
            "Pedido no encontrado.",
            "danger"
        )

        return redirect(
            url_for("admin_pedidos")
        )

    detalles = obtener_detalles_pedido(
        pedido_id
    )

    return render_template(
        "admin/pedido_detalle.html",
        pedido=pedido,
        detalles=detalles,
        usuario=usuario_actual()
    )


# ==========================================================
# ADMIN - CAMBIAR ESTADO DEL PEDIDO
# ==========================================================

@app.route(
    "/admin/pedidos/<int:pedido_id>/estado",
    methods=["POST"]
)
@admin_requerido
def admin_actualizar_estado(pedido_id):

    estado = request.form.get(
        "estado"
    )

    estados_validos = [
        "pendiente",
        "pagado",
        "enviado",
        "entregado",
        "cancelado"
    ]

    if estado not in estados_validos:

        flash(
            "Estado no válido.",
            "danger"
        )

        return redirect(
            url_for("admin_pedidos")
        )

    resultado = actualizar_estado_pedido(
        pedido_id,
        estado
    )

    if resultado:

        flash(
            "Estado actualizado correctamente.",
            "success"
        )

    else:

        flash(
            "No se pudo actualizar el estado.",
            "danger"
        )

    return redirect(
        url_for("admin_pedidos")
    )


# ==========================================================
# ERROR 404
# ==========================================================

@app.errorhandler(404)
def error_404(error):

    return render_template(
        "404.html"
    ), 404


# ==========================================================
# ERROR 500
# ==========================================================

@app.errorhandler(500)
def error_500(error):

    return render_template(
        "500.html"
    ), 500


# ==========================================================
# INICIALIZAR BASE DE DATOS
# ==========================================================

def inicializar():

    print("Inicializando base de datos...")

    crear_tablas()

    datos_iniciales()

    crear_admin()

    print("Base de datos lista.")


# ==========================================================
# EJECUTAR
# ==========================================================

if __name__ == "__main__":

    inicializar()

    print()
    print("========================================")
    print("       MI TIENDA ONLINE")
    print("========================================")
    print()
    print("Servidor:")
    print("http://127.0.0.1:5000")
    print()
    print("Administrador:")
    print("admin@tienda.com")
    print("Admin123")
    print()
    print("========================================")

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )