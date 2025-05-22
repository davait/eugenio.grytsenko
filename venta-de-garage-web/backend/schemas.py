from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from datetime import datetime

class LocalityBase(BaseModel):
    id: int
    name: str
    province_id: int
    province_name: Optional[str] = None
    class Config:
        orm_mode = True

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    whatsapp: Optional[str] = None
    locality_id: Optional[int] = None
    created_at: datetime
    is_active: bool

    class Config:
        orm_mode = True

class ProductImageBase(BaseModel):
    filename: str

class ProductImage(ProductImageBase):
    id: int
    product_id: int

    class Config:
        orm_mode = True

class CategoryBase(BaseModel):
    name: str

class Category(CategoryBase):
    id: int
    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    title: str
    description: str
    price: float
    condition: str
    ends_at: datetime
    available: bool
    featured: bool

    @validator('condition', pre=True, always=True)
    def condition_to_str(cls, v):
        if isinstance(v, str):
            return v
        return v.value if v is not None else None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    created_at: datetime
    locality: Optional[LocalityBase]
    seller: User
    images: List[ProductImage] = []
    views: int
    searches: int
    categories: List[Category]

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
