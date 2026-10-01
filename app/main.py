from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from .database import Base, engine, get_db
from .models import Product, Order, OrderItem
from .schemas import ProductCreate, ProductOut, OrderCreate, OrderOut
from .security import issue_token, require_user, require_roles

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Order and Inventory Management API", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/auth/demo-login")
def demo_login(username: str = "manager", role: str = "manager"):
    if role not in {"admin", "manager", "staff"}:
        raise HTTPException(400, "Unsupported role")
    return {"access_token": issue_token(username, role), "token_type": "bearer"}

@app.get("/api/auth/me")
def me(user=Depends(require_user)):
    return {"username": user["sub"], "role": user["role"]}

@app.post("/api/products", response_model=ProductOut, status_code=201)
def create_product(data: ProductCreate, db: Session = Depends(get_db), _=Depends(require_roles("admin", "manager"))):
    if db.scalar(select(Product).where(Product.sku == data.sku)):
        raise HTTPException(409, "SKU already exists")
    product = Product(**data.model_dump())
    db.add(product); db.commit(); db.refresh(product)
    return product

@app.get("/api/products", response_model=list[ProductOut])
def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), _=Depends(require_user)):
    if limit < 1 or limit > 200:
        raise HTTPException(400, "limit must be between 1 and 200")
    return list(db.scalars(select(Product).where(Product.active.is_(True)).offset(skip).limit(limit)))

@app.get("/api/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db), _=Depends(require_user)):
    product = db.get(Product, product_id)
    if not product or not product.active:
        raise HTTPException(404, "Product not found")
    return product

@app.patch("/api/products/{product_id}/stock")
def adjust_stock(product_id: int, delta: int, db: Session = Depends(get_db), _=Depends(require_roles("admin", "manager"))):
    product = db.get(Product, product_id)
    if not product or not product.active:
        raise HTTPException(404, "Product not found")
    if product.quantity + delta < 0:
        raise HTTPException(409, "Insufficient stock")
    product.quantity += delta
    db.commit()
    return {"sku": product.sku, "quantity": product.quantity}

@app.delete("/api/products/{product_id}", status_code=204)
def deactivate_product(product_id: int, db: Session = Depends(get_db), _=Depends(require_roles("admin"))):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    product.active = False
    db.commit()

@app.post("/api/orders", response_model=OrderOut, status_code=201)
def create_order(data: OrderCreate, db: Session = Depends(get_db), _=Depends(require_roles("admin", "manager", "staff"))):
    # Validate all lines before changing inventory, so a rejected order has no partial stock changes.
    resolved = []
    for line in data.items:
        product = db.scalar(select(Product).where(Product.sku == line.sku, Product.active.is_(True)))
        if not product:
            raise HTTPException(404, f"Unknown SKU: {line.sku}")
        if product.quantity < line.quantity:
            raise HTTPException(409, f"Insufficient stock for {line.sku}")
        resolved.append((product, line.quantity))
    total = sum(product.unit_price * qty for product, qty in resolved)
    order = Order(customer_name=data.customer_name, total=round(total, 2), status="confirmed")
    db.add(order); db.flush()
    for product, qty in resolved:
        product.quantity -= qty
        order.items.append(OrderItem(product_id=product.id, quantity=qty, unit_price=product.unit_price))
    db.commit(); db.refresh(order)
    return order

@app.get("/api/orders", response_model=list[OrderOut])
def list_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), _=Depends(require_user)):
    return list(db.scalars(select(Order).order_by(Order.id.desc()).offset(skip).limit(min(limit, 200))))

@app.get("/api/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), _=Depends(require_user)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return order

@app.patch("/api/orders/{order_id}/status", response_model=OrderOut)
def update_order_status(order_id: int, new_status: str, db: Session = Depends(get_db), _=Depends(require_roles("admin", "manager"))):
    if new_status not in {"pending", "confirmed", "packed", "dispatched", "cancelled"}:
        raise HTTPException(400, "Invalid order status")
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    order.status = new_status
    db.commit(); db.refresh(order)
    return order
