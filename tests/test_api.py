from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def token(role="manager"):
    r = client.post("/api/auth/demo-login", params={"username":"tester", "role":role})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_health_and_me():
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/api/auth/me", headers=token()).status_code == 200

def test_create_product_and_duplicate_sku():
    headers = token()
    sku = "TEST-" + str(__import__("time").time_ns())
    payload = {"sku":sku, "name":"Test Widget", "quantity":8, "unit_price":12.5}
    first = client.post("/api/products", json=payload, headers=headers)
    assert first.status_code == 201
    assert client.post("/api/products", json=payload, headers=headers).status_code == 409

def test_stock_cannot_go_negative():
    headers = token()
    sku = "STOCK-" + str(__import__("time").time_ns())
    r = client.post("/api/products", json={"sku":sku,"name":"Stock Item","quantity":1,"unit_price":3}, headers=headers)
    pid = r.json()["id"]
    assert client.patch(f"/api/products/{pid}/stock", params={"delta":-2}, headers=headers).status_code == 409

def test_role_restriction():
    assert client.post("/api/products", json={"sku":"X-1","name":"Widget","quantity":1,"unit_price":1}, headers=token("staff")).status_code == 403

def test_order_decrements_inventory():
    headers = token()
    sku = "ORDER-" + str(__import__("time").time_ns())
    client.post("/api/products", json={"sku":sku,"name":"Order Item","quantity":5,"unit_price":4}, headers=headers)
    order = client.post("/api/orders", json={"customer_name":"Example Customer","items":[{"sku":sku,"quantity":2}]}, headers=headers)
    assert order.status_code == 201
    assert order.json()["total"] == 8
    products = client.get("/api/products", headers=headers).json()
    assert next(p for p in products if p["sku"] == sku)["quantity"] == 3
