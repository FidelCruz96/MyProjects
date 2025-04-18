# main.py (product_recommender)
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import joblib
from typing import List
import os
import xmlrpc.client
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configuración Odoo desde .env
ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

# Conexión con Odoo XML-RPC
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

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

@app.get("/")
def read_root():
    return {"msg": "Product Recommender Service is running"}

@app.post("/recomendar")
def recomendar(data: RecommendationRequest):
    if not model:
        productos_populares = [101, 102, 103, 104, 105]
        return {"recomendaciones": productos_populares[:data.top_n]}
    recomendaciones = model.get(data.partner_id, [])[:data.top_n]
    return {"recomendaciones": recomendaciones}

# Entrenar modelo desde Odoo
if __name__ == "__main__":
    try:
        order_lines = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'sale.order.line', 'search_read',
            [[('state', 'in', ['sale', 'done'])]],
            {'fields': ['order_id', 'product_id'], 'limit': 5000}
        )

        order_ids = [line['order_id'][0] for line in order_lines if line['order_id']]
        partner_map = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'sale.order', 'read',
            order_ids,
            ['partner_id']
        )
        order_partner = {item['id']: item['partner_id'][0] for item in partner_map if item['partner_id']}

        data = []
        for line in order_lines:
            if line['order_id'] and line['product_id']:
                order_id = line['order_id'][0]
                partner_id = order_partner.get(order_id)
                if partner_id:
                    data.append((partner_id, line['product_id'][0]))

        df = pd.DataFrame(data, columns=['partner_id', 'product_id'])
        grouped = df.groupby(['partner_id', 'product_id']).size().reset_index(name='count')

        recomendaciones = {}
        for pid in grouped['partner_id'].unique():
            productos = grouped[grouped['partner_id'] == pid]
            productos = productos.sort_values(by='count', ascending=False)
            recomendaciones[pid] = productos['product_id'].tolist()

        os.makedirs("recommender", exist_ok=True)
        joblib.dump(recomendaciones, MODEL_PATH)
        print("Modelo entrenado y guardado exitosamente.")

    except Exception as e:
        print(f"Error entrenando el modelo: {e}")
