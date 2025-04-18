# main.py (fastapi_sync)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import xmlrpc.client

load_dotenv()

app = FastAPI()

ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

class OrderLine(BaseModel):
    product_id: int
    quantity: float

class ExternalOrder(BaseModel):
    partner_id: int
    channel_code: str
    order_ref: str
    order_lines: list[OrderLine]

@app.get("/")
def read_root():
    return {"msg": "FastAPI Sync Service is running"}

@app.post("/crear_pedido")
def crear_pedido(order: ExternalOrder):
    try:
        # Buscar canal externo
        channel_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'sale.channel', 'search',
            [[('code', '=', order.channel_code)]],
            {'limit': 1}
        )
        if not channel_ids:
            raise HTTPException(status_code=404, detail="Canal externo no encontrado")

        # Preparar líneas de pedido
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
        return {"pedido_creado": sale_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear pedido: {e}")
