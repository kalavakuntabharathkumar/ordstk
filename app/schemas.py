from pydantic import BaseModel, Field, ConfigDict

class ProductCreate(BaseModel):
    sku: str = Field(min_length=2, max_length=60)
    name: str = Field(min_length=2, max_length=160)
    quantity: int = Field(ge=0)
    unit_price: float = Field(ge=0)

class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    name: str
    quantity: int
    unit_price: float
    active: bool

class OrderLineIn(BaseModel):
    sku: str
    quantity: int = Field(gt=0)

class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=160)
    items: list[OrderLineIn] = Field(min_length=1)

class OrderOut(BaseModel):
    id: int
    customer_name: str
    status: str
    total: float

# Schemas enforce API boundaries before persistence.
