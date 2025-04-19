# main.py (product_recommender)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib
from typing import List
import os
import xmlrpc.client
from dotenv import load_dotenv
import datetime

load_dotenv()

app = FastAPI(
    title="Recomendador de Productos con Odoo",
    description="Microservicio que entrena un modelo de recomendaciones basado en órdenes históricas y sugiere productos por cliente.",
    version="1.0.0"
)

# Configuración Odoo desde .env
ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

# Validar conexión a Odoo
try:
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
except Exception as e:
    print(f"Error conectando a Odoo: {e}")
    raise

# Registrar auditoría de uso del recomendador
def registrar_log(usuario, tipo, estado, mensaje):
    try:
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
        print(f"Error registrando auditoría: {e}")

# Cargar modelo entrenado
MODEL_PATH = "recommender/model.pkl"
def load_model():
    try:
        return joblib.load(MODEL_PATH)
    except:
        return None

model = load_model()

class RecommendationRequest(BaseModel):
    partner_id: int
    top_n: int = 5
    user: str = "anonymous"

@app.get("/")
def read_root():
    return {"msg": "Product Recommender Service is running"}

@app.get("/demo")
def demo():
    return {
        "demo": True,
        "mensaje": "Este endpoint simula una respuesta de recomendación",
        "recomendaciones": [201, 202, 203]
    }

@app.get("/status", summary="Estado del servicio de recomendaciones")
def status():
    try:
        version = common.version()
        modelo_activo = os.path.exists(MODEL_PATH)
        return {
            "estado": "OK",
            "hora_servidor": datetime.datetime.utcnow().isoformat(),
            "modelo_cargado": modelo_activo,
            "odoo_version": version.get("server_version")
        }
    except Exception as e:
        return {"estado": "Error", "detalle": str(e)}

@app.post("/recomendar", summary="Obtener productos recomendados")
def recomendar(data: RecommendationRequest):
    try:
        if not model:
            productos_populares = [101, 102, 103, 104, 105]
            registrar_log(data.user, "recomendar", "success", "Modelo no entrenado, se retornan valores por defecto")
            return {"recomendaciones": productos_populares[:data.top_n]}

        recomendaciones = model.get(data.partner_id, [])[:data.top_n]
        registrar_log(data.user, "recomendar", "success", f"Recomendaciones generadas para partner {data.partner_id}")
        return {"recomendaciones": recomendaciones}
    except Exception as e:
        registrar_log(data.user, "recomendar", "error", str(e))
        raise HTTPException(status_code=500, detail=f"Error en recomendación: {e}")
