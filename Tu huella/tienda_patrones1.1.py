# tienda_backend.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Callable, Any, Optional, Tuple
from colorama import Fore, Style, init

# Inicializa colorama para consola
init(autoreset=True)

# =========================
# Infraestructura (Singletons, BusEventos, PasarelaPago)
# =========================
class ConexionBaseDatos:  # <<Singleton>>
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            print(Fore.CYAN + "Inicializando ConexionBaseDatos (Singleton)...")
            cls._instancia = super().__new__(cls)
            # "Tablas" en memoria para demo
            cls._instancia.productos: Dict[int, Dict[str, Any]] = {}
            cls._instancia.clientes: Dict[int, Dict[str, Any]] = {}
            cls._instancia.carritos: Dict[int, 'Carrito'] = {}
            cls._instancia.facturas: Dict[int, 'Factura'] = {}
            cls._instancia.usuarios: Dict[str, Dict[str, Any]] = {}
            cls._instancia.seq_factura: int = 1
        return cls._instancia

    # API mínima de "conexión"
    def obtenerConexion(self):
        return self  # simulación

class Logger:  # <<Singleton>>
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            print(Fore.CYAN + "Inicializando Logger (Singleton)...")
            cls._instancia = super().__new__(cls)
        return cls._instancia

    def info(self, mensaje: str):
        print(Fore.GREEN + f"[INFO] {mensaje}")

    def error(self, mensaje: str):
        print(Fore.RED + f"[ERROR] {mensaje}")

class BusEventos:
    def __init__(self):
        self.suscriptores: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def publicar(self, nombreEvento: str, datos: Dict[str, Any]):
        Logger().info(f"Publicando evento '{nombreEvento}' con datos: {datos}")
        for handler in self.suscriptores.get(nombreEvento, []):
            handler(datos)

    def suscribir(self, nombreEvento: str, handler: Callable[[Dict[str, Any]], None]):
        self.suscriptores.setdefault(nombreEvento, []).append(handler)
        Logger().info(f"Suscrito handler a evento '{nombreEvento}'")

class PasarelaPago:
    def procesarPago(self, monto: float, datosPago) -> Dict[str, Any]:  # ResultadoPago simulado
        Logger().info(f"Procesando pago por {monto:.2f}")
        # Simulación aprobada
        return {"ok": True, "autorizacion": f"AUTH-{datetime.now().strftime('%H%M%S')}", "monto": monto}

# =========================
# Observadores
# =========================
class IObservadorProducto(ABC):
    @abstractmethod
    def actualizar(self, idProducto: int, evento: str) -> None:
        pass

class ObservadorCarrito(IObservadorProducto):
    def actualizar(self, idProducto: int, evento: str) -> None:
        print(Fore.YELLOW + f"[Carrito] Producto {idProducto} - {evento} → Actualizando carritos activos...")

class ObservadorContabilidad(IObservadorProducto):
    ingresos_acumulados: float = 0.0

    def actualizar(self, idProducto: int, evento: str) -> None:
        db = ConexionBaseDatos()
        prod = db.productos.get(idProducto)
        if not prod:
            return
        # Para simplicidad, sumamos 1 unidad por evento
        ObservadorContabilidad.ingresos_acumulados += prod["precio"]
        print(Fore.MAGENTA + f"[Contabilidad] Ingreso +${prod['precio']:.2f} | Total: ${ObservadorContabilidad.ingresos_acumulados:.2f}")

class ObservadorAuditoria(IObservadorProducto):
    historial: List[Tuple[int, str, datetime]] = []

    def actualizar(self, idProducto: int, evento: str) -> None:
        registro = (idProducto, evento, datetime.now())
        ObservadorAuditoria.historial.append(registro)
        print(Fore.BLUE + f"[Auditoría] Registro: Producto {idProducto} - {evento} - {registro[2].isoformat(timespec='seconds')}")

class ObservadorNotificacion(IObservadorProducto):
    def actualizar(self, idProducto: int, evento: str) -> None:
        db = ConexionBaseDatos()
        prod = db.productos.get(idProducto)
        nombre = prod["nombre"] if prod else f"#{idProducto}"
        print(Fore.GREEN + f"[Notificación] Email/SMS: '{nombre}' → {evento}")

# =========================
# Dominio
# =========================
class Usuario:
    def __init__(self, idUsuario: int, nombre: str, email: str, contrasena: str):
        self.idUsuario = idUsuario
        self.nombre = nombre
        self.email = email
        self.contrasena = contrasena
        self._token: Optional[str] = None

    def iniciarSesion(self) -> bool:
        db = ConexionBaseDatos()
        db.usuarios[self.email] = {"id": self.idUsuario, "nombre": self.nombre, "pass": self.contrasena}
        self._token = f"TOKEN-{self.idUsuario}"
        Logger().info(f"Usuario {self.nombre} inició sesión")
        return True

    def cerrarSesion(self) -> None:
        Logger().info(f"Usuario {self.nombre} cerró sesión")
        self._token = None

class Administrador:
    def __init__(self, rol: str = "ADMIN"):
        self.rol = rol

    def gestionarProducto(self) -> None: Logger().info("Gestionando producto...")
    def gestionarProveedor(self) -> None: Logger().info("Gestionando proveedor...")
    def gestionarCliente(self) -> None: Logger().info("Gestionando cliente...")
    def gestionarInventario(self) -> None: Logger().info("Gestionando inventario...")
    def gestionarContabilidad(self) -> None: Logger().info("Gestionando contabilidad...")
    def revisarAuditoria(self) -> None: Logger().info("Revisando auditoría...")

    def generarReporte(self) -> 'Reporte':
        r = Reporte("Reporte Admin", "Resumen del sistema", datetime.now())
        Logger().info("Reporte generado por administrador")
        return r

    def realizarRespaldo(self) -> None:
        Logger().info("Respaldo realizado correctamente")

class Auditoria:
    def __init__(self):
        self.registros: List[str] = []

    def registrarAccion(self, accion: str) -> None:
        self.registros.append(accion)
        Logger().info(f"Auditoría: {accion}")

    def generarAuditoria(self) -> 'Reporte':
        contenido = "\n".join(self.registros) if self.registros else "Sin registros"
        return Reporte("Auditoría", contenido, datetime.now())

@dataclass
class Reporte:
    titulo: str
    contenido: str
    fechaGeneracion: datetime
    def exportarPDF(self) -> None:
        print(Fore.CYAN + f"[Reporte] Exportando '{self.titulo}' a PDF...")
    def mostrar(self) -> None:
        print(Fore.CYAN + f"[Reporte] {self.titulo} ({self.fechaGeneracion.date()}):\n{self.contenido}")

class Cliente:
    def __init__(self, idCliente: int, nombre: str, direccion: str, telefono: str):
        self.idCliente = idCliente
        self.nombre = nombre
        self.direccion = direccion
        self.telefono = telefono

    def visualizarCatalogo(self) -> List[Dict[str, Any]]:
        db = ConexionBaseDatos()
        return list(db.productos.values())

    def agregarAlCarrito(self, idProducto: int, cantidad: int) -> None:
        db = ConexionBaseDatos()
        carrito = db.carritos.setdefault(self.idCliente, Carrito(self.idCliente))
        carrito.agregar(idProducto, cantidad)

    def realizarPago(self) -> 'Factura':
        raise NotImplementedError("Usa OrdenServiceImpl a través de la FachadaTienda")

class ClienteRegistro:
    def __init__(self, idCliente: int, nombre: str, direccion: str, telefono: str):
        self.idCliente = idCliente
        self.nombre = nombre
        self.direccion = direccion
        self.telefono = telefono
    def actualizarDatos(self) -> None:
        Logger().info(f"Cliente {self.idCliente} actualizó sus datos")

class Carrito(IObservadorProducto):
    def __init__(self, idCliente: int):
        self.idCarrito = idCliente  # 1:1 para demo
        self.productos: List[Tuple[int, int]] = []  # (idProducto, cantidad)
        self.total: float = 0.0

    def calcularTotal(self) -> float:
        db = ConexionBaseDatos()
        total = 0.0
        for idP, cant in self.productos:
            p = db.productos.get(idP, {})
            total += p.get("precio", 0) * cant
        self.total = total
        Logger().info(f"Total carrito {self.idCarrito}: ${total:.2f}")
        return total

    def vaciarCarrito(self) -> None:
        self.productos.clear()
        self.total = 0.0
        Logger().info(f"Carrito {self.idCarrito} vaciado")

    def onProductoActualizado(self, idProducto: int, evento: str) -> None:
        # Ejemplo: si se agota, eliminar del carrito
        if "agotado" in evento.lower():
            antes = len(self.productos)
            self.productos = [(p, c) for (p, c) in self.productos if p != idProducto]
            if len(self.productos) < antes:
                Logger().info(f"Carrito {self.idCarrito}: producto {idProducto} removido por agotado")

    # Implementación de IObservadorProducto
    def actualizar(self, idProducto: int, evento: str) -> None:
        self.onProductoActualizado(idProducto, evento)

class Factura:
    def __init__(self, idFactura: int, cliente: Cliente, productos: List[Tuple[int, int]], total: float, fecha: datetime):
        self.idFactura = idFactura
        self.cliente = cliente
        self.productos = productos
        self.total = total
        self.fecha = fecha
    def generarFactura(self) -> None:
        print(Fore.WHITE + f"Factura #{self.idFactura} | Cliente: {self.cliente.nombre} | Total: ${self.total:.2f} | Fecha: {self.fecha}")

class Producto:
    def __init__(self, idProducto: int, nombre: str, descripcion: str, precio: float, inventario: int):
        self.idProducto = idProducto
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio = precio
        self.inventario = inventario

    def actualizarInventario(self, cantidad: int) -> None:
        self.inventario += cantidad
        Logger().info(f"Producto {self.idProducto} '{self.nombre}' inventario: {self.inventario}")

    def verificarDisponibilidad(self, cantidad: int) -> bool:
        return self.inventario >= cantidad

class Inventario:
    def __init__(self):
        self.listaProductos: List[int] = []
    def ingresarProducto(self, productoDto) -> None:
        Logger().info("Inventario.ingresarProducto llamado (use el servicio para lógica real)")
    def darSalidaProducto(self, idProducto: int, cantidad: int) -> None:
        Logger().info("Inventario.darSalidaProducto llamado (use el servicio para lógica real)")
    def generarReporteInventario(self) -> Reporte:
        return Reporte("Reporte Inventario", "Estado actual del inventario", datetime.now())

class Contabilidad:
    def __init__(self):
        self.ingresos: float = 0.0
        self.egresos: float = 0.0
    def registrarIngreso(self, venta: Factura) -> None:
        self.ingresos += venta.total
        Logger().info(f"Contabilidad: ingreso registrado ${venta.total:.2f}")
    def registrarEgreso(self, compra) -> None:
        self.egresos += float(compra or 0)
        Logger().info(f"Contabilidad: egreso registrado ${float(compra or 0):.2f}")
    def calcularBalance(self) -> float:
        balance = self.ingresos - self.egresos
        Logger().info(f"Balance: ${balance:.2f}")
        return balance

class Proveedor:
    def __init__(self, idProveedor: int, nombre: str, contacto: str, direccion: str):
        self.idProveedor = idProveedor
        self.nombre = nombre
        self.contacto = contacto
        self.direccion = direccion
    def enviarProducto(self) -> List[Dict[str, Any]]:
        Logger().info(f"Proveedor {self.nombre} envió productos")
        return []

# =========================
# Servicios (Interfaces y Implementaciones)
# =========================
class IProductoRepositorio(ABC):
    @abstractmethod
    def obtenerPorId(self, idProducto: int) -> Producto: ...
    @abstractmethod
    def guardar(self, producto) -> None: ...
    @abstractmethod
    def actualizarInventario(self, idProducto: int, delta: int) -> None: ...
    @abstractmethod
    def buscar(self, consulta: str) -> List[Producto]: ...

class IInventarioService(ABC):
    @abstractmethod
    def ingresarProducto(self, productoDto) -> None: ...
    @abstractmethod
    def darSalidaProducto(self, idProducto: int, cantidad: int) -> None: ...
    @abstractmethod
    def consultarInventario(self, idProducto: int) -> int: ...

class IContabilidadService(ABC):
    @abstractmethod
    def registrarIngreso(self, factura: Factura) -> None: ...
    @abstractmethod
    def registrarEgreso(self, compra) -> None: ...
    @abstractmethod
    def calcularBalance(self) -> float: ...

class IOrdenService(ABC):
    @abstractmethod
    def verificar(self, idCliente: int, idCarrito: int, infoPago) -> Factura: ...

class ICatalogoService(ABC):
    @abstractmethod
    def listarProductos(self, filtros) -> List[Dict[str, Any]]: ...
    @abstractmethod
    def buscar(self, consulta: str) -> List[Dict[str, Any]]: ...

class ProductoRepositorioImpl(IProductoRepositorio):
    def __init__(self):
        self.db = ConexionBaseDatos()
        self.log = Logger()

    def obtenerPorId(self, idProducto: int) -> Producto:
        row = self.db.productos.get(idProducto)
        if not row:
            raise ValueError("Producto no encontrado")
        return Producto(idProducto, row["nombre"], row.get("descripcion", ""), row["precio"], row["stock"])

    def guardar(self, producto) -> None:
        self.db.productos[producto["idProducto"]] = {
            "idProducto": producto["idProducto"],
            "nombre": producto["nombre"],
            "descripcion": producto.get("descripcion", ""),
            "precio": float(producto["precio"]),
            "stock": int(producto["stock"]),
        }
        self.log.info(f"Producto guardado: {producto['nombre']}")

    def actualizarInventario(self, idProducto: int, delta: int) -> None:
        if idProducto not in self.db.productos:
            raise ValueError("Producto no existe")
        self.db.productos[idProducto]["stock"] += delta
        nuevo = self.db.productos[idProducto]["stock"]
        self.log.info(f"Inventario actualizado producto {idProducto}: {nuevo}")

    def buscar(self, consulta: str) -> List[Dict[str, Any]]:
        q = consulta.lower()
        return [p for p in self.db.productos.values() if q in p["nombre"].lower() or q in p.get("descripcion", "").lower()]

class InventarioServiceImpl(IInventarioService):
    def __init__(self, repo: IProductoRepositorio, busEventos: BusEventos):
        self.repo = repo
        self.busEventos = busEventos
        self.log = Logger()

    def ingresarProducto(self, productoDto) -> None:
        self.repo.guardar(productoDto)
        self.busEventos.publicar("producto_actualizado", {"idProducto": productoDto["idProducto"], "evento": "Ingreso a inventario"})

    def darSalidaProducto(self, idProducto: int, cantidad: int) -> None:
        self.repo.actualizarInventario(idProducto, -cantidad)
        # Evento por cada unidad para ejemplificar notificaciones
        for _ in range(cantidad):
            self.busEventos.publicar("venta_realizada", {"idProducto": idProducto, "evento": "Venta realizada"})
        # Si se agotó, emitir evento
        stock = self.consultarInventario(idProducto)
        if stock <= 0:
            self.busEventos.publicar("producto_actualizado", {"idProducto": idProducto, "evento": "Producto agotado"})

    def consultarInventario(self, idProducto: int) -> int:
        p = self.repo.obtenerPorId(idProducto)
        return p.inventario

class ContabilidadServiceImpl(IContabilidadService):
    def __init__(self, repo: IProductoRepositorio):
        self.repo = repo
        self.conta = Contabilidad()

    def registrarIngreso(self, factura: Factura) -> None:
        self.conta.registrarIngreso(factura)

    def registrarEgreso(self, compra) -> None:
        self.conta.registrarEgreso(compra)

    def calcularBalance(self) -> float:
        return self.conta.calcularBalance()

class OrdenServiceImpl(IOrdenService):
    def __init__(self, repo: IProductoRepositorio, inventario: IInventarioService, contabilidad: IContabilidadService, busEventos: BusEventos, pasarelaPago: PasarelaPago):
        self.repo = repo
        self.inventario = inventario
        self.contabilidad = contabilidad
        self.busEventos = busEventos
        self.pasarelaPago = pasarelaPago
        self.db = ConexionBaseDatos()
        self.log = Logger()

    def verificar(self, idCliente: int, idCarrito: int, infoPago) -> Factura:
        # 1. Calcular total
        carrito = self.db.carritos.get(idCarrito)
        if not carrito or not carrito.productos:
            raise ValueError("Carrito vacío o inexistente")
        total = carrito.calcularTotal()

        # 2. Procesar pago
        resultado = self.pasarelaPago.procesarPago(total, infoPago)
        if not resultado.get("ok"):
            raise RuntimeError("Pago rechazado")

        # 3. Descontar inventario
        for idP, cant in carrito.productos:
            self.inventario.darSalidaProducto(idP, cant)

        # 4. Crear factura
        idFactura = self.db.seq_factura
        self.db.seq_factura += 1
        cliente_row = self.db.clientes.get(idCliente, {"idCliente": idCliente, "nombre": f"Cliente {idCliente}", "direccion": "-", "telefono": "-"})
        cliente = Cliente(cliente_row["idCliente"], cliente_row["nombre"], cliente_row["direccion"], cliente_row["telefono"])
        factura = Factura(idFactura, cliente, carrito.productos.copy(), total, datetime.now())
        self.db.facturas[idFactura] = factura
        factura.generarFactura()

        # 5. Registrar ingreso
        self.contabilidad.registrarIngreso(factura)

        # 6. Notificar evento de orden completada
        self.busEventos.publicar("orden_completada", {"idProducto": 0, "evento": f"Orden #{idFactura} completada"})

        # 7. Vaciar carrito
        carrito.vaciarCarrito()

        return factura

class CatalogoServiceImpl(ICatalogoService):
    def __init__(self, repo: IProductoRepositorio):
        self.repo = repo

    def listarProductos(self, filtros) -> List[Dict[str, Any]]:
        db = ConexionBaseDatos()
        # Filtros simples por rango de precio o disponibilidad
        prods = list(db.productos.values())
        if filtros:
            minp = filtros.get("min_precio")
            maxp = filtros.get("max_precio")
            dispo = filtros.get("disponibles")
            if minp is not None:
                prods = [p for p in prods if p["precio"] >= minp]
            if maxp is not None:
                prods = [p for p in prods if p["precio"] <= maxp]
            if dispo:
                prods = [p for p in prods if p["stock"] > 0]
        return prods

    def buscar(self, consulta: str) -> List[Dict[str, Any]]:
        return self.repo.buscar(consulta)

class AutenticacionService:
    def acceder(self, email: str, contrasena: str) -> str:
        db = ConexionBaseDatos()
        if email in db.usuarios and db.usuarios[email]["pass"] == contrasena:
            token = f"TOKEN-{db.usuarios[email]['id']}"
            Logger().info(f"Acceso concedido a {email}")
            return token
        Logger().error("Credenciales inválidas")
        return ""

    def cerrar_sesion(self, token: str) -> None:
        Logger().info(f"Token invalidado: {token}")

# =========================
# Fachada
# =========================
class FachadaTienda:
    def __init__(self, ordenService: IOrdenService, catalogoService: ICatalogoService, authService: AutenticacionService):
        self.ordenService = ordenService
        self.catalogoService = catalogoService
        self.authService = authService
        self.db = ConexionBaseDatos()
        self.log = Logger()

    def verCatalogo(self, filtros) -> List[Dict[str, Any]]:
        items = self.catalogoService.listarProductos(filtros)
        print(Fore.CYAN + "Catálogo:")
        for p in items:
            print(Fore.CYAN + f" - {p['idProducto']}: {p['nombre']} | ${p['precio']:.2f} | Stock: {p['stock']}")
        return items

    def agregarAlCarrito(self, idCliente: int, idProducto: int, cantidad: int) -> None:
        # aseguremos cliente y carrito
        self.db.clientes.setdefault(idCliente, {"idCliente": idCliente, "nombre": f"Cliente {idCliente}", "direccion": "-", "telefono": "-"})
        carrito = self.db.carritos.setdefault(idCliente, Carrito(idCliente))
        # validar stock
        prod = self.db.productos.get(idProducto)
        if not prod:
            self.log.error("Producto no encontrado")
            return
        if prod["stock"] < cantidad:
            self.log.error("Stock insuficiente")
            return
        carrito.productos.append((idProducto, cantidad))
        carrito.calcularTotal()
        self.log.info(f"Agregado al carrito {idCliente}: {prod['nombre']} x{cantidad}")

    def finalizarCompra(self, idCliente: int, idCarrito: int, infoPago) -> Factura:
        return self.ordenService.verificar(idCliente, idCarrito, infoPago)

    def adminAgregarProducto(self, productoDto) -> None:
        # Esta operación se realiza vía InventarioServiceImpl (inyectado en Orden o externamente).
        # Para simplificar la demo, usaremos un repositorio directo si existe en el DTO el flag.
        Logger().info(f"Administrador agregando producto: {productoDto.get('nombre')}")


# =========================
# DEMO de uso por consola
# =========================
def demo():
    log = Logger()
    db = ConexionBaseDatos()
    bus = BusEventos()

    # Suscribir observadores a eventos relevantes
    obs_carrito = ObservadorCarrito()
    obs_conta = ObservadorContabilidad()
    obs_audi = ObservadorAuditoria()
    obs_notif = ObservadorNotificacion()
    # Eventos de producto e inventario
    bus.suscribir("producto_actualizado", lambda datos: obs_carrito.actualizar(**datos))
    bus.suscribir("producto_actualizado", lambda datos: obs_audi.actualizar(**datos))
    bus.suscribir("producto_actualizado", lambda datos: obs_notif.actualizar(**datos))
    # Eventos de venta
    bus.suscribir("venta_realizada", lambda datos: obs_carrito.actualizar(**datos))
    bus.suscribir("venta_realizada", lambda datos: obs_conta.actualizar(**datos))
    bus.suscribir("venta_realizada", lambda datos: obs_audi.actualizar(**datos))
    bus.suscribir("venta_realizada", lambda datos: obs_notif.actualizar(**datos))
    # Evento de orden
    bus.suscribir("orden_completada", lambda datos: obs_audi.actualizar(**datos))

    # Repos y servicios
    repo = ProductoRepositorioImpl()
    inv_srv = InventarioServiceImpl(repo, bus)
    conta_srv = ContabilidadServiceImpl(repo)
    pasarela = PasarelaPago()
    orden_srv = OrdenServiceImpl(repo, inv_srv, conta_srv, bus, pasarela)
    catalogo_srv = CatalogoServiceImpl(repo)
    auth_srv = AutenticacionService()

    # Fachada
    fachada = FachadaTienda(orden_srv, catalogo_srv, auth_srv)

    # Admin registra productos (vía servicio de inventario)
    inv_srv.ingresarProducto({"idProducto": 101, "nombre": "Zapatilla Deportiva", "descripcion": "Running pro", "precio": 120000, "stock": 10})
    inv_srv.ingresarProducto({"idProducto": 102, "nombre": "Zapatilla Casual",   "descripcion": "Daily",      "precio":  95000, "stock": 5})
    inv_srv.ingresarProducto({"idProducto": 103, "nombre": "Zapatilla Urbana",   "descripcion": "Street",     "precio": 130000, "stock": 2})

    # Usuario/Cliente
    usuario = Usuario(1, "Yeison", "yeison@tienda.com", "1234")
    usuario.iniciarSesion()
    token = auth_srv.acceder("yeison@tienda.com", "1234")

    # Ver catálogo completo y filtrado
    fachada.verCatalogo(filtros={"disponibles": True})
    print()
    print(Fore.WHITE + "Búsqueda 'Zapatilla':", catalogo_srv.buscar("Zapatilla"))

    # Agregar al carrito y finalizar compra
    idCliente = 1
    fachada.agregarAlCarrito(idCliente, 101, 2)
    fachada.agregarAlCarrito(idCliente, 102, 1)

    print()
    print(Fore.WHITE + "Total previo a pagar:")
    db.carritos[idCliente].calcularTotal()

    print()
    print(Fore.WHITE + "Procesando compra...")
    factura = fachada.finalizarCompra(idCliente, idCliente, {"metodo": "tarjeta", "numero": "4111-****"})
    print()

    # Mostrar catálogo actualizado
    print(Fore.WHITE + "Catálogo tras la compra:")
    fachada.verCatalogo({})

    # Balance contable
    print()
    print(Fore.WHITE + "Balance contable:")
    conta_srv.calcularBalance()

    # Auditoría
    print()
    print(Fore.WHITE + "Resumen de auditoría:")
    rep = Auditoria().generarAuditoria()  # Genera vacío (auditoría directa arriba es por ObservadorAuditoria)
    for (idProd, ev, fecha) in ObservadorAuditoria.historial[-5:]:
        print(Fore.BLUE + f" - {fecha.strftime('%H:%M:%S')} | Producto {idProd} | {ev}")

    usuario.cerrarSesion()
    auth_srv.cerrar_sesion(token)

if __name__ == "__main__":
    demo()
