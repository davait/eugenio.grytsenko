from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, create_engine, Enum, Boolean, Table, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

class ProductCondition(enum.Enum):
    NUEVO = "Nuevo"
    USADO = "Usado"

class Country(Base):
    __tablename__ = 'countries'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    code = Column(String, unique=True, nullable=False)
    provinces = relationship("Province", back_populates="country")

class Province(Base):
    __tablename__ = 'provinces'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    country_id = Column(Integer, ForeignKey('countries.id'))
    country = relationship("Country", back_populates="provinces")
    localities = relationship("Locality", back_populates="province")

class Locality(Base):
    __tablename__ = 'localities'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    province_id = Column(Integer, ForeignKey('provinces.id'))
    province = relationship("Province", back_populates="localities")
    products = relationship("Product", back_populates="locality")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    whatsapp = Column(String)
    locality_id = Column(Integer, ForeignKey('localities.id'))
    locality = relationship("Locality")
    products = relationship("Product", back_populates="seller")
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Elimino ProductCategory Enum y creo modelo Category
class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

# Tabla intermedia para la relación muchos a muchos
product_categories = Table(
    'product_categories', Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    locality_id = Column(Integer, ForeignKey('localities.id'))
    locality = relationship("Locality", back_populates="products")
    condition = Column(Enum(ProductCondition), nullable=False, default=ProductCondition.USADO)
    available = Column(Boolean, default=True)
    views = Column(Integer, default=0)
    searches = Column(Integer, default=0)
    featured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    ends_at = Column(DateTime, nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"))
    seller = relationship("User", back_populates="products")
    images = relationship("ProductImage", back_populates="product")
    categories = relationship("Category", secondary=product_categories)
    embedding = Column(LargeBinary, nullable=True)

class ProductImage(Base):
    __tablename__ = "product_images"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    product_id = Column(Integer, ForeignKey("products.id"))
    product = relationship("Product", back_populates="images")

# Configuración de la base de datos SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./garage_sale.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}) 