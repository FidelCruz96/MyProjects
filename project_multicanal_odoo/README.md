# 🧠 Sistema Multicanal + Recomendador Inteligente con Odoo 16 + FastAPI

Este proyecto es una arquitectura basada en microservicios que permite:

✅ Recibir pedidos desde múltiples canales externos (ecommerce, apps, otros sistemas)
✅ Crear pedidos automáticamente en Odoo 16 desde un microservicio
✅ Generar recomendaciones inteligentes de productos según ventas históricas
✅ Arquitectura escalable y desacoplada usando Docker Compose, Redis y FastAPI

---

## 🧱 Estructura del Proyecto

```
project_multicanal_odoo/
├── docker-compose.yml
├── odoo/
│   └── custom_addons/
│       └── pedidos_multicanal/  # Módulo Odoo para gestionar pedidos externos
├── fastapi_sync/               # Microservicio que crea pedidos en Odoo
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── product_recommender/       # Microservicio que sugiere productos a clientes
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
```

---

## 🚀 ¿Qué hace cada microservicio?

### 🔁 `fastapi_sync`
- Recibe pedidos desde API externa
- Busca cliente y canal en Odoo
- Crea el pedido automáticamente usando XML-RPC
- Protegido con autenticación básica

### 🧠 `product_recommender`
- Lee las órdenes históricas de Odoo
- Genera recomendaciones por cliente (partner_id)
- Entrena modelo desde `sale.order.line`
- Responde con top productos usando `/recomendar`

---

## 🐳 Cómo ejecutar

Desde la raíz del proyecto:

```bash
docker-compose up --build -d
```

Luego accede a:
- Odoo: `http://localhost:8069`
- FastAPI Sync: `http://localhost:8001/docs`
- Product Recommender: `http://localhost:8002/docs`

---

## 🔐 Variables de entorno

### `.env` para `fastapi_sync`
```
ODOO_URL=http://odoo:8069
ODOO_DB=odoo_db
ODOO_USER=admin
ODOO_PASSWORD=admin123
API_USER=admin
API_PASSWORD=admin123
```

### `.env` para `product_recommender`
```
ODOO_URL=http://odoo:8069
ODOO_DB=odoo_db
ODOO_USER=admin
ODOO_PASSWORD=admin123
```

---

## 🧪 Probar el sistema

### 🧾 Crear pedido:

```bash
curl -X POST http://localhost:8001/crear_pedido \
  -u admin:admin123 \
  -H "Content-Type: application/json" \
  -d '{
    "partner_id": 3,
    "channel_code": "WEB",
    "order_ref": "WEB-001",
    "order_lines": [
      {"product_id": 25, "quantity": 2}
    ]
  }'
```

### 💡 Obtener recomendaciones:

```bash
curl -X POST http://localhost:8002/recomendar \
  -H "Content-Type: application/json" \
  -d '{"partner_id": 3, "top_n": 3}'
```

---

## 🧠 Entrenar modelo de recomendación

```bash
docker exec -it recommender_service python main.py
```

Esto generará `model.pkl` con las recomendaciones históricas para cada cliente.

---

## 📄 Licencia

Este proyecto fue desarrollado por **Héctor Fidel Cruz Rodríguez** como parte de su portafolio profesional.
Distribuido con fines educativos y demostrativos.
