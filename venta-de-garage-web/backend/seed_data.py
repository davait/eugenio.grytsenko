from sqlalchemy.orm import Session
from models import Base, engine, User, Product, ProductImage, Category, ProductCondition, Locality
from database import SessionLocal
import shutil
import os
import requests
from random import randint
from datetime import datetime, timedelta
import random
from sentence_transformers import SentenceTransformer
import numpy as np
from sqlalchemy import func
import re

def download_image(url, filepath):
    print(f"[DEBUG] Descargando imagen de {url} a {filepath}")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filepath, 'wb') as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
        return True
    return False

def seed_database():
    # Borrar y crear tablas
    # Base.metadata.drop_all(bind=engine)
    # Base.metadata.create_all(bind=engine)
    db = Session(engine)
    print(f"[DEBUG] Total de localidades en la base: {db.query(Locality).count()}")
    # Buscar localidades por nombre
    def get_locality_id(nombre):
        loc = db.query(Locality).filter(Locality.name.ilike(f'%{nombre}%')).first()
        if not loc:
            similares = db.query(Locality).filter(Locality.name.ilike(f'%{nombre.split()[0]}%')).all()
            print(f"[DEBUG] No se encontró '{nombre}'. Sugerencias: {[l.name for l in similares]}")
            # Si no existe, usar una localidad aleatoria de Buenos Aires
            loc = db.query(Locality).filter(Locality.province.has(name.ilike('%Buenos Aires%'))).order_by(func.random()).first()
        return loc.id if loc else None

    # Usuarios de ejemplo
    users = [
        User(id=random.randint(1000000000, 9999999999), name="Juan Pérez", email="juan@example.com", whatsapp="+5491122334455", locality_id=get_locality_id("Palermo")),
        User(id=random.randint(1000000000, 9999999999), name="María García", email="maria@example.com", whatsapp="+5491166778899", locality_id=get_locality_id("Belgrano")),
        User(id=random.randint(1000000000, 9999999999), name="Carlos Rodríguez", email="carlos@example.com", whatsapp="+5491165478932", locality_id=get_locality_id("Recoleta")),
        User(id=random.randint(1000000000, 9999999999), name="Ana Martínez", email="ana@example.com", whatsapp="+5491143215678", locality_id=get_locality_id("Vicente López")),
        User(id=random.randint(1000000000, 9999999999), name="Luis García", email="luis@example.com", whatsapp="+5491198765432", locality_id=get_locality_id("San Isidro")),
        User(id=random.randint(1000000000, 9999999999), name="Sofía López", email="sofia@example.com", whatsapp="+5491176543210", locality_id=get_locality_id("Pilar")),
    ]
    for u in users:
        u.set_password("clave")
        print(f"[DEBUG] Insertando usuario: {u.name} - {u.email} - id: {u.id}")
        db.query(User).filter_by(email=u.email).delete()  # Eliminar duplicados antes de insertar
    db.add_all(users)
    db.flush()
    # Crear categorías reales evitando duplicados
    category_names = [
        "Electrónica", "Muebles", "Ropa y Accesorios", "Deportes", "Hogar y Jardín",
        "Juguetes", "Libros", "Instrumentos Musicales", "Otros"
    ]
    categories = []
    for name in category_names:
        cat = db.query(Category).filter_by(name=name).first()
        if not cat:
            cat = Category(name=name)
            db.add(cat)
            db.flush()
        categories.append(cat)
    category_dict = {c.name: c for c in categories}
    # Imágenes de ejemplo (puedes agregar más urls si quieres)
    example_images = [
        "https://images.unsplash.com/photo-1532298229144-0ec0c57515c7",
        "https://images.unsplash.com/photo-1485965120184-e220f721d03e",
        "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9",
        "https://images.unsplash.com/photo-1592750475338-74b7b21085ab",
        "https://images.unsplash.com/photo-1517336714731-489689fd1ca8",
        "https://images.unsplash.com/photo-1611186871348-b1ce696e52c9",
        "https://images.unsplash.com/photo-1601944179066-29786cb9d32a",
        "https://images.unsplash.com/photo-1461151304267-38535e780c79",
        "https://images.unsplash.com/photo-1606813907291-d86efa9b94db",
        "https://images.unsplash.com/photo-1605901309584-818e25960a8f",
        "https://images.unsplash.com/photo-1516035069371-29a1b244cc32",
        "https://images.unsplash.com/photo-1502920917128-1aa500764cbd",
        "https://images.unsplash.com/photo-1564186763535-ebb21ef5277f",
        "https://images.unsplash.com/photo-1550291652-6ea9114a47b1",
        "https://images.unsplash.com/photo-1584568694244-14fbdf83bd30",
        "https://images.unsplash.com/photo-1585771724684-38269d6639fd",
        "https://images.unsplash.com/photo-1506439773649-6e0eb8cfb237",
        "https://images.unsplash.com/photo-1550226891-ef816aed4a98",
        "https://images.unsplash.com/photo-1577140917170-285929fb55b7",
        "https://images.unsplash.com/photo-1533090481720-856c6e3c1fdc",
    ]
    titulos = [
        ("Bicicleta Mountain Bike", ["Deportes"]),
        ("Mesa de Comedor", ["Muebles"]),
        ("iPhone 13 Pro", ["Electrónica"]),
        ("MacBook Pro 2021", ["Electrónica"]),
        ("Smart TV Samsung 55'", ["Electrónica"]),
        ("PlayStation 5", ["Electrónica", "Juguetes"]),
        ("Cámara Sony A7 III", ["Electrónica"]),
        ("Guitarra Fender Stratocaster", ["Instrumentos Musicales"]),
        ("Heladera Samsung French Door", ["Hogar y Jardín"]),
        ("Sillón Reclinable", ["Muebles"]),
        ("Silla de Oficina", ["Muebles"]),
        ("Libro: Cien Años de Soledad", ["Libros"]),
        ("Zapatillas Nike Air", ["Deportes", "Ropa y Accesorios"]),
        ("Vestido de Fiesta", ["Ropa y Accesorios"]),
        ("Juego de Sábanas", ["Hogar y Jardín"]),
        ("Lámpara de Pie", ["Hogar y Jardín"]),
        ("Teclado Yamaha PSR", ["Instrumentos Musicales", "Electrónica"]),
        ("Muñeca Barbie", ["Juguetes"]),
        ("Raqueta de Tenis", ["Deportes"]),
        ("Libro: El Principito", ["Libros"]),
        ("Cochecito de Bebé", ["Juguetes", "Hogar y Jardín"]),
        ("Mesa Ratona", ["Muebles"]),
        ("Sofá 3 cuerpos", ["Muebles"]),
        ("Batería Electrónica", ["Instrumentos Musicales", "Electrónica"]),
        ("Cámara GoPro Hero", ["Electrónica"]),
        ("Pantalón Jean", ["Ropa y Accesorios"]),
        ("Remera Adidas", ["Ropa y Accesorios"]),
        ("Juego de Ollas", ["Hogar y Jardín"]),
        ("Bicicleta Infantil", ["Deportes", "Juguetes"]),
        ("Guitarra Criolla", ["Instrumentos Musicales"]),
        ("Libro: Rayuela", ["Libros"]),
        ("Auriculares Bluetooth", ["Electrónica"]),
        ("Cámara Polaroid", ["Electrónica"]),
        ("Mesa de Luz", ["Muebles"]),
        ("Silla Gamer", ["Muebles", "Electrónica"]),
        ("Teclado Mecánico", ["Electrónica"]),
        ("Bicicleta de Ruta", ["Deportes"]),
        ("Batería Acústica", ["Instrumentos Musicales"]),
        ("Libro: Don Quijote", ["Libros"]),
        ("Muñeco de Star Wars", ["Juguetes"]),
        ("Camiseta de Fútbol", ["Deportes", "Ropa y Accesorios"]),
        ("Mesa Plegable", ["Muebles"]),
        ("Silla Plegable", ["Muebles"]),
        ("Heladera Whirlpool", ["Hogar y Jardín"]),
        ("Guitarra Eléctrica Ibanez", ["Instrumentos Musicales"]),
        ("Bicicleta BMX", ["Deportes"]),
        ("Libro: Harry Potter", ["Libros"]),
        ("Juguete Didáctico", ["Juguetes"]),
        ("Mesa de Jardín", ["Muebles", "Hogar y Jardín"]),
        ("Silla de Jardín", ["Muebles", "Hogar y Jardín"]),
        ("Batería Infantil", ["Instrumentos Musicales", "Juguetes"]),
    ]
    # Diccionario de palabras clave por categoría
    CATEGORIA_KEYWORDS = {
        'Electrónica': ['iphone', 'samsung', 'celular', 'smartphone', 'android', 'móvil', 'telefono', 'teléfono', 'macbook', 'notebook', 'laptop', 'computadora', 'pc', 'ordenador', 'portátil', 'tv', 'televisor', 'pantalla', 'auriculares', 'bluetooth', 'cámara', 'polaroid'],
        'Muebles': ['silla', 'mesa', 'sillón', 'sofá', 'placard', 'escritorio', 'ratona', 'luz', 'gamer', 'plegable', 'jardín', 'mesa de luz', 'mesa de jardín', 'silla de jardín'],
        'Ropa y Accesorios': ['zapatillas', 'camiseta', 'pantalón', 'remera', 'vestido', 'ropa', 'jean', 'adidas', 'nike'],
        'Deportes': ['bicicleta', 'bici', 'mountain bike', 'bmx', 'ruta', 'raqueta', 'tenis', 'fútbol', 'deporte', 'pelota'],
        'Hogar y Jardín': ['sábanas', 'ollas', 'lámpara', 'heladera', 'refrigerador', 'microondas', 'lavarropas', 'licuadora', 'batidora', 'cocina', 'jardín', 'mesa de jardín', 'silla de jardín'],
        'Juguetes': ['muñeca', 'juguete', 'lego', 'barbie', 'star wars', 'didáctico', 'cochecito', 'batería infantil'],
        'Libros': ['libro', 'novela', 'cuento', 'harry potter', 'rayuela', 'principito', 'don quijote'],
        'Instrumentos Musicales': ['guitarra', 'batería', 'teclado', 'piano', 'fender', 'ibanez', 'yamaha'],
        'Otros': []
    }
    def normalize(s):
        return re.sub(r'[^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9 ]', '', s.lower())
    def categorizar_producto(titulo, descripcion):
        texto = normalize(titulo + ' ' + descripcion)
        found = []
        for cat, keywords in CATEGORIA_KEYWORDS.items():
            for kw in keywords:
                if kw in texto:
                    found.append(cat)
                    break
        if not found:
            found.append('Otros')
        return found[:2]  # máximo 2 categorías
    # Generar 50 productos
    productos = []
    for i in range(50):
        titulo, posibles_cats = random.choice(titulos)
        user = random.choice(users)
        precio = random.randint(0, 800000)
        descripcion = f"{titulo} en excelente estado. Ideal para regalar o usar en casa."
        location = user.locality_id
        images = random.sample(example_images, k=random.randint(1, 2))
        # Asignar categorías realistas
        categorias_asignadas = categorizar_producto(titulo, descripcion)
        producto = Product(
            title=titulo,
            description=descripcion,
            price=precio,
            locality_id=location,
            categories=[category_dict[n] for n in categorias_asignadas if n in category_dict],
            condition=random.choice([ProductCondition.NUEVO, ProductCondition.USADO]),
            ends_at=datetime.utcnow() + timedelta(days=random.randint(1, 60)),
            seller_id=user.id,
            available=True,
            views=random.randint(1, 120),
            searches=random.randint(1, 80),
            featured=random.choice([True, False])
        )
        db.add(producto)
        db.flush()
        for idx, img_url in enumerate(images):
            filename = f"{user.id}_{i}_{idx}.jpg"
            filepath = f"uploads/{user.id}/{filename}"
            os.makedirs(f"uploads/{user.id}", exist_ok=True)
            if download_image(img_url, filepath):
                db.add(ProductImage(filename=f"{user.id}/{filename}", product_id=producto.id))
        texto = f"{producto.title}|{producto.description}|{' '.join([c.name for c in producto.categories])}"
        producto.embedding = get_local_embedding(texto).tobytes()
    db.commit()
    print("Base de datos poblada con 50 productos de ejemplo.")

def get_local_embedding(text):
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return model.encode([text])[0].astype('float32')

if __name__ == "__main__":
    seed_database()
