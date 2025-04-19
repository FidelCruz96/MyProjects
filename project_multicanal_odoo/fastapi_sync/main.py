# main.py (fastapi_sync)
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import xmlrpc.client
import secrets
import datetime

load_dotenv()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Microservicio de Sincronización de Pedidos",
    description="Este microservicio recibe pedidos desde canales externos y los crea automáticamente en Odoo.",
    version="1.0.0"
)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"error": "Demasiadas solicitudes. Intenta más tarde."})

security = HTTPBasic()
API_USER = os.getenv("API_USER", "admin")
API_PASSWORD = os.getenv("API_PASSWORD", "admin123")

# Configuración de Odoo
ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, API_USER)
    correct_password = secrets.compare_digest(credentials.password, API_PASSWORD)
    if not (correct_username and correct_password):
        registrar_log(credentials.username, 'login', 'error', 'Autenticación fallida')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    registrar_log(credentials.username, 'login', 'success', 'Autenticación correcta')
    return credentials.username

def get_odoo_env():
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    if not uid:
        raise Exception("Fallo de autenticación con Odoo")
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
    return uid, models

def registrar_log(usuario, tipo, estado, mensaje):
    try:
        uid, models = get_odoo_env()
        models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'audit.log', 'create',
            [{
                'name': f"{tipo.upper()} - {datetime.datetime.now().isoformat()}",
                'user': usuario,
                'action_type': tipo,
                'status': estado,
                'message': mensaje
            }]
        )
    except Exception as e:
        print(f"No se pudo registrar en audit.log: {e}")

class OrderLine(BaseModel):
    product_id: int
    quantity: float

class ExternalOrder(BaseModel):
    partner_id: int
    channel_code: str
    order_ref: str
    order_lines: list[OrderLine]

@app.get("/", summary="Ping de estado")
def read_root(user: str = Depends(authenticate)):
    return {"msg": f"Bienvenido, {user}. FastAPI Sync Service is running."}

@app.get("/status", summary="Estado del sistema")
def system_status(user: str = Depends(authenticate)):
    try:
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
        version = common.version()
        return {
            "estado": "OK",
            "hora_servidor": datetime.datetime.utcnow().isoformat(),
            "odoo_version": version.get("server_version"),
            "usuario_api": user
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando estado: {e}")

@app.post("/crear_pedido", summary="Crear Pedido en Odoo")
@limiter.limit("5/minute")
def crear_pedido(request: Request, order: ExternalOrder, user: str = Depends(authenticate)):
    try:
        uid, models = get_odoo_env()

        channel_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'sale.channel', 'search',
            [[('code', '=', order.channel_code)]],
            {'limit': 1}
        )
        if not channel_ids:
            raise HTTPException(status_code=404, detail="Canal externo no encontrado")

        lines = [
            (0, 0, {
                'product_id': l.product_id,
                'product_uom_qty': l.quantity,
            }) for l in order.order_lines
        ]

        sale_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'sale.order', 'create',
            [{
                'partner_id': order.partner_id,
                'external_channel_id': channel_ids[0],
                'external_order_ref': order.order_ref,
                'synced_from_api': True,
                'order_line': lines,
            }]
        )

        models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'sync.log', 'create',
            [{
                'name': f"Pedido desde API: {order.order_ref}",
                'channel_id': channel_ids[0],
                'order_id': sale_id,
                'status': 'success',
                'message': f"Pedido creado exitosamente por el usuario {user}"
            }]
        )

        return {"pedido_creado": sale_id, "creado_por": user}

    except Exception as e:
        try:
            uid, models = get_odoo_env()
            models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'sync.log', 'create',
                [{
                    'name': f"Error pedido {order.order_ref}",
                    'channel_id': channel_ids[0] if 'channel_ids' in locals() and channel_ids else None,
                    'status': 'error',
                    'message': str(e)
                }]
            )
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Error al crear pedido: {e}")
