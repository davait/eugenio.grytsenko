from datetime import datetime, timedelta
from models import Base, engine, User, Product, ProductImage, Category, ProductCondition, Locality
import os
import requests
from PIL import Image
from io import BytesIO
from random import randint
from sentence_transformers import SentenceTransformer
import numpy as np

# Definir modelo y función de embedding antes de cualquier uso
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
def get_local_embedding(text):
    return model.encode([text])[0].astype('float32')

# Crear todas las tablas (borrando antes si existen)
# Base.metadata.drop_all(bind=engine)
# Base.metadata.create_all(bind=engine)

# Función para descargar y guardar imágenes
def download_and_save_image(url, user_id, timestamp):
    response = requests.get(url)
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))
        
        # Crear directorio si no existe
        user_upload_dir = f"uploads/{user_id}"
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # Guardar imagen
        filename = f"{timestamp}_product.jpg"
        file_path = f"{user_upload_dir}/{filename}"
        img.save(file_path, "JPEG")
        
        return f"{user_id}/{filename}"
    return None

# Crear algunos usuarios de ejemplo
from sqlalchemy.orm import Session

with Session(engine) as db:
    # Buscar localidades por nombre
    san_isidro = db.query(Locality).filter(Locality.name.ilike('%San Isidro%')).first()
    belgrano = db.query(Locality).filter(Locality.name.ilike('%Belgrano%')).first()
    print(f"[DEBUG] Total de localidades en la base: {db.query(Locality).count()}")
    if not san_isidro:
        similares = db.query(Locality).filter(Locality.name.ilike('%San%')).all()
        print(f"[DEBUG] No se encontró 'San Isidro'. Sugerencias: {[l.name for l in similares]}")
    if not belgrano:
        similares = db.query(Locality).filter(Locality.name.ilike('%Bel%')).all()
        print(f"[DEBUG] No se encontró 'Belgrano'. Sugerencias: {[l.name for l in similares]}")
    if not san_isidro or not belgrano:
        raise Exception('No se encontraron las localidades San Isidro o Belgrano. Ejecuta primero load_geonames_locations.py')

    # Crear categorías reales
    category_names = [
        "Electrónica", "Muebles", "Ropa y Accesorios", "Deportes", "Hogar y Jardín",
        "Juguetes", "Libros", "Instrumentos Musicales", "Otros"
    ]
    categories = [Category(name=name) for name in category_names]
    db.add_all(categories)
    db.flush()
    category_dict = {c.name: c for c in categories}

    # Imágenes de ejemplo
    example_images = {
        "iphone": "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?auto=format&fit=crop&w=500&q=80",
        "guitarra": "https://images.unsplash.com/photo-1564186763535-ebb21ef5277f?auto=format&fit=crop&w=500&q=80",
        "sillon": "https://images.unsplash.com/photo-1506439773649-6e0eb8cfb237?auto=format&fit=crop&w=500&q=80",
        "bici": "https://images.unsplash.com/photo-1532298229144-0ec0c57515c7?auto=format&fit=crop&w=500&q=80"
    }

    # Crear usuarios
    user1 = User(
        name="Juan Pérez",
        email="juan@example.com",
        locality_id=san_isidro.id,
        whatsapp="+5491122334455"
    )
    user1.set_password("123456")
    user2 = User(
        name="María García",
        email="maria@example.com",
        locality_id=belgrano.id,
        whatsapp="+5491166778899"
    )
    user2.set_password("123456")
    db.add_all([user1, user2])
    db.flush()

    # Crear productos
    products = [
        Product(
            title="Sillón Reclinable",
            description="Sillón reclinable de cuero en excelente estado",
            price=50000,
            locality_id=san_isidro.id,
            categories=[category_dict["Muebles"]],
            condition=ProductCondition.USADO,
            ends_at=datetime.utcnow() + timedelta(days=30),
            seller_id=user1.id,
            available=True,
            views=randint(10, 100),
            searches=randint(5, 50),
            featured=True
        ),
        Product(
            title="Guitarra Eléctrica",
            description="Guitarra eléctrica Fender Stratocaster",
            price=150000,
            locality_id=belgrano.id,
            categories=[category_dict["Instrumentos Musicales"]],
            condition=ProductCondition.USADO,
            ends_at=datetime.utcnow() + timedelta(days=15),
            seller_id=user2.id,
            available=False,
            views=randint(10, 100),
            searches=randint(5, 50),
            featured=True
        ),
        Product(
            title="iPhone 12",
            description="iPhone 12 64GB en perfecto estado",
            price=200000,
            locality_id=san_isidro.id,
            categories=[category_dict["Electrónica"]],
            condition=ProductCondition.NUEVO,
            ends_at=datetime.utcnow() + timedelta(days=7),
            seller_id=user1.id,
            available=True,
            views=randint(10, 100),
            searches=randint(5, 50),
            featured=True
        ),
        Product(
            title="Bicicleta Mountain Bike",
            description="Bicicleta Mountain Bike rodado 29",
            price=80000,
            locality_id=belgrano.id,
            categories=[category_dict["Deportes"]],
            condition=ProductCondition.USADO,
            ends_at=datetime.utcnow() - timedelta(days=1),  # Producto expirado
            seller_id=user2.id,
            available=False,
            views=randint(10, 100),
            searches=randint(5, 50),
            featured=False
        )
    ]
    db.add_all(products)
    db.flush()

    # Agregar imágenes a los productos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # iPhone
    if filename := download_and_save_image(example_images["iphone"], user1.id, f"{timestamp}_1"):
        db.add(ProductImage(filename=filename, product_id=products[2].id))
    
    # Guitarra
    if filename := download_and_save_image(example_images["guitarra"], user2.id, f"{timestamp}_2"):
        db.add(ProductImage(filename=filename, product_id=products[1].id))
    
    # Sillón
    if filename := download_and_save_image(example_images["sillon"], user1.id, f"{timestamp}_3"):
        db.add(ProductImage(filename=filename, product_id=products[0].id))
    
    # Bicicleta
    if filename := download_and_save_image(example_images["bici"], user2.id, f"{timestamp}_4"):
        db.add(ProductImage(filename=filename, product_id=products[3].id))

    # Al crear cada producto:
    # producto.embedding = get_local_embedding(f"{producto.title}|{producto.description}|{' '.join([c.name for c in producto.categories])}").tobytes()

    for producto in products:
        texto = f"{producto.title}|{producto.description}|{' '.join([c.name for c in producto.categories])}"
        producto.embedding = get_local_embedding(texto).tobytes()

    db.commit()

print("Base de datos inicializada con datos de ejemplo")
