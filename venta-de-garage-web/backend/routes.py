from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body, FastAPI, status
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime, timedelta
from sqlalchemy import desc, and_
import unicodedata
import numpy as np
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
import faiss
from fastapi.encoders import jsonable_encoder
from symspellpy.symspellpy import SymSpell, Verbosity
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

from database import get_db
from models import Product, User, ProductImage, Category, ProductCondition, Locality, Province
from schemas import ProductCreate, Product as ProductSchema, User as UserSchema, UserCreate, Token, TokenData

router = APIRouter()

class FeaturedRequest(BaseModel):
    featured: bool

class ProductListResponse(BaseModel):
    items: List[ProductSchema]
    total: int

# Cargar el modelo una sola vez al iniciar el backend
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# FAISS index y mapeo de product_id a posición
faiss_index = None
product_id_map = []
similarity_threshold = 0.35

# Inicializar SymSpell (parámetros recomendados)
sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
# Cargar diccionario grande en español si existe
symspell_dict_path = os.path.join(os.path.dirname(__file__), 'frequency_dictionary_es.txt')
if os.path.exists(symspell_dict_path):
    sym_spell.load_dictionary(symspell_dict_path, term_index=0, count_index=1, encoding="utf-8")
else:
    print(f"[WARN] No se encontró el diccionario frequency_dictionary_es.txt en {symspell_dict_path}")

# Función para obtener todos los embeddings y reconstruir el índice
def build_faiss_index(db):
    global faiss_index, product_id_map
    products = db.query(Product).all()
    embeddings = []
    product_id_map = []
    for p in products:
        if p.embedding:
            emb = np.frombuffer(p.embedding, dtype=np.float32)
            embeddings.append(emb)
            product_id_map.append(p.id)
    if embeddings:
        xb = np.stack(embeddings).astype('float32')
        faiss_index = faiss.IndexFlatIP(xb.shape[1])
        faiss_index.add(xb)
    else:
        faiss_index = None

def get_local_embedding(text):
    emb = model.encode([text])[0].astype('float32')
    return emb / np.linalg.norm(emb)

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

@router.post("/products/", response_model=ProductSchema)
async def create_product(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    locality_id: int = Form(...),
    categories: List[str] = Form(...),
    condition: ProductCondition = Form(...),
    ends_at: datetime = Form(...),
    seller_name: str = Form(...),
    seller_whatsapp: str = Form(...),
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    # Crear o obtener el usuario
    user = db.query(User).filter(User.whatsapp == seller_whatsapp).first()
    if not user:
        user = User(
            name=seller_name,
            whatsapp=seller_whatsapp,
            locality_id=locality_id
        )
        db.add(user)
        db.flush()

    # Buscar instancias de Category por nombre
    db_categories = db.query(Category).filter(Category.name.in_(categories)).all()
    product = Product(
        title=title,
        description=description,
        price=price,
        locality_id=locality_id,
        condition=condition,
        ends_at=ends_at,
        seller_id=user.id,
        categories=db_categories
    )
    db.add(product)
    db.flush()

    # Crear el directorio para las imágenes si no existe
    user_upload_dir = f"uploads/{user.id}"
    os.makedirs(user_upload_dir, exist_ok=True)

    # Guardar las imágenes
    for image in images:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{image.filename}"
        file_path = f"{user_upload_dir}/{filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        db_image = ProductImage(
            filename=f"{user.id}/{filename}",
            product_id=product.id
        )
        db.add(db_image)

    # Calcular embedding y guardar
    texto = f"{title}|{description}|{' - '.join(categories)}"
    emb = get_local_embedding(texto)
    product.embedding = emb.tobytes()
    db.commit()
    db.refresh(product)
    # Actualizar índice FAISS
    build_faiss_index(db)
    return product

@router.get("/products/", response_model=ProductListResponse)
def get_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    condition: Optional[str] = None,
    location: Optional[str] = None,
    seller_id: Optional[int] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    ends_in: Optional[str] = None,  # '30+', '7+', '1', '0'
    active_only: bool = True,
    featured_only: bool = False,
    page: int = 1,
    page_size: int = 15,
    db: Session = Depends(get_db)
):
    query = db.query(Product).order_by(desc(Product.searches), desc(Product.views), desc(Product.id))
    now = datetime.utcnow()

    suggestion = None
    print(f"[DEBUG] seller_id recibido: {seller_id} (tipo: {type(seller_id)})")
    if search:
        # Corrección ortográfica automática con SymSpell
        suggestions = sym_spell.lookup_compound(search, max_edit_distance=2)
        if suggestions:
            corrected_search = suggestions[0].term
            if corrected_search != search:
                print(f"[DEBUG] Corrección ortográfica (SymSpell): '{search}' -> '{corrected_search}'")
                suggestion = corrected_search
            else:
                print(f"[DEBUG] Sin corrección ortográfica para: '{search}'")
            search = corrected_search
        else:
            print(f"[DEBUG] SymSpell no encontró sugerencias para: '{search}'")
        print(f"[DEBUG] Invocando FAISS para búsqueda semántica: '{search}'")
        consulta_emb = get_local_embedding(search)
        if faiss_index is not None and len(product_id_map) > 0:
            consulta_emb = consulta_emb.reshape(1, -1)
            D, I = faiss_index.search(consulta_emb, 100)
            results = [(product_id_map[idx], score) for idx, score in zip(I[0], D[0]) if idx >= 0 and score > similarity_threshold]
            ids = [id for id, score in results]
            print(f"[DEBUG] FAISS encontró {len(ids)} ids similares para la consulta (score > {similarity_threshold}).")
            for rank, (id, score) in enumerate(results[:10]):
                print(f"[DEBUG]   Rank {rank+1}: id={id}, score={score:.4f}")
            productos = db.query(Product).filter(Product.id.in_(ids)).all()
            productos_ordenados = sorted(productos, key=lambda p: ids.index(p.id))
            filtered = productos_ordenados
        else:
            print("[DEBUG] FAISS no tiene índice o productos para buscar.")
            filtered = []
        if category:
            filtered = [p for p in filtered if any(c.name == category for c in p.categories)]
        if condition:
            try:
                try:
                    condition_enum = ProductCondition[condition.upper()]
                except KeyError:
                    condition_enum = next(
                        c for c in ProductCondition if c.value.lower() == condition.lower()
                    )
                filtered = [p for p in filtered if p.condition == condition_enum]
            except Exception:
                raise HTTPException(status_code=422, detail="Condición inválida. Las condiciones válidas son: Nuevo, Usado")
        if location:
            # Buscar si location es una provincia
            province = db.query(Province).filter(Province.name == location).first()
            if province:
                # Filtrar productos cuya localidad pertenezca a esa provincia
                query = query.join(Product.locality).filter(Locality.province_id == province.id)
            else:
                # Buscar si location es una localidad
                locality = db.query(Locality).filter(Locality.name == location).first()
                if locality:
                    query = query.join(Product.locality).filter(Locality.id == locality.id)
                else:
                    # Si no es ni provincia ni localidad, no filtrar
                    pass
        if price_min is not None:
            filtered = [p for p in filtered if p.price >= price_min]
        if price_max is not None:
            filtered = [p for p in filtered if p.price <= price_max]
        if ends_in:
            if ends_in == '30+':
                filtered = [p for p in filtered if p.ends_at > now + timedelta(days=30)]
            elif ends_in == '7+':
                filtered = [p for p in filtered if p.ends_at > now + timedelta(days=7)]
            elif ends_in == '1':
                filtered = [p for p in filtered if p.ends_at > now + timedelta(days=1) and p.ends_at <= now + timedelta(days=7)]
            elif ends_in == '0':
                filtered = [p for p in filtered if p.ends_at <= now + timedelta(days=1)]
        if active_only:
            filtered = [p for p in filtered if p.ends_at > now]
        if featured_only:
            filtered = [p for p in filtered if p.featured]
        if seller_id is not None:
            print(f"[DEBUG] Filtrando por seller_id en búsqueda: {seller_id}")
            filtered = [p for p in filtered if p.seller_id == seller_id]
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        items = []
        for p in filtered[start:end]:
            if p.seller is None:
                print(f"[DEBUG] Producto con id={p.id} sin seller, se omite del resultado.")
                continue
            prod_dict = ProductSchema.model_validate(p).model_dump()
            if p.locality:
                loc_dict = prod_dict['locality']
                loc_dict['province_name'] = p.locality.province.name if p.locality.province else None
                prod_dict['locality'] = loc_dict
            items.append(prod_dict)
        response_json = {"items": items, "total": total, "suggestion": suggestion}
        print(f"[DEBUG] Respuesta /products: {response_json}")
        return response_json
    
    if category:
        query = query.join(Product.categories).filter(Category.name == category)
    
    if condition:
        try:
            # Permitir tanto el nombre del Enum como el valor
            try:
                condition_enum = ProductCondition[condition.upper()]
            except KeyError:
                # Buscar por valor
                condition_enum = next(
                    c for c in ProductCondition if c.value.lower() == condition.lower()
                )
            query = query.filter(Product.condition == condition_enum)
        except Exception:
            raise HTTPException(status_code=422, detail="Condición inválida. Las condiciones válidas son: Nuevo, Usado")
    
    if location:
        # Buscar si location es una provincia
        province = db.query(Province).filter(Province.name == location).first()
        if province:
            # Filtrar productos cuya localidad pertenezca a esa provincia
            query = query.join(Product.locality).filter(Locality.province_id == province.id)
        else:
            # Buscar si location es una localidad
            locality = db.query(Locality).filter(Locality.name == location).first()
            if locality:
                query = query.join(Product.locality).filter(Locality.id == locality.id)
            else:
                # Si no es ni provincia ni localidad, no filtrar
                pass
    
    if price_min is not None:
        query = query.filter(Product.price >= price_min)
    
    if price_max is not None:
        query = query.filter(Product.price <= price_max)
    
    if ends_in:
        if ends_in == '30+':
            query = query.filter(Product.ends_at > now + timedelta(days=30))
        elif ends_in == '7+':
            query = query.filter(Product.ends_at > now + timedelta(days=7))
        elif ends_in == '1':
            query = query.filter(Product.ends_at > now + timedelta(days=1), Product.ends_at <= now + timedelta(days=7))
        elif ends_in == '0':
            query = query.filter(Product.ends_at <= now + timedelta(days=1))
    
    if active_only:
        query = query.filter(Product.ends_at > now)
    
    if featured_only:
        query = query.filter(Product.featured == True)
        print(f"[DEBUG] Query de destacados: {str(query)}")
    if seller_id is not None:
        print(f"[DEBUG] Filtrando por seller_id en query: {seller_id}")
        query = query.filter(Product.seller_id == seller_id)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    print(f"[DEBUG] Productos destacados devueltos: {[p.id for p in items]}")
    items_out = []
    for p in items:
        if p.seller is None:
            print(f"[DEBUG] Producto con id={p.id} sin seller, se omite del resultado.")
            continue
        prod_dict = ProductSchema.model_validate(p).model_dump()
        if p.locality:
            loc_dict = prod_dict['locality']
            loc_dict['province_name'] = p.locality.province.name if p.locality.province else None
            prod_dict['locality'] = loc_dict
        items_out.append(prod_dict)
    return {"items": items_out, "total": total, "suggestion": suggestion}

@router.get("/search/suggestions")
def get_search_suggestions(
    query: str,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if not query or len(query) < 2:
        return {"suggestions": []}
    
    def normalize(s):
        return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c)).lower()
    norm_query = normalize(query)
    # Traer todos los productos activos
    all_products = db.query(Product).filter(Product.ends_at > datetime.utcnow()).all()
    suggestions = []
    vendedores_agregados = set()
    ubicaciones_agregadas = set()
    productos_agregados = set()
    for p in all_products:
        # Sugerencias de productos (sin duplicados por título y categoría)
        prod_key = (normalize(p.title), p.categories[0].name if p.categories else "Otros")
        if norm_query in normalize(p.title) and prod_key not in productos_agregados:
            suggestions.append({
                "text": p.title,
                "type": "producto",
                "category": p.categories[0].name if p.categories else "Otros"
            })
            productos_agregados.add(prod_key)
        # Sugerencias de ubicación (sin duplicados)
        if p.locality and norm_query in normalize(p.locality.name):
            loc = p.locality.name.strip().lower()
            if loc not in ubicaciones_agregadas:
                suggestions.append({
                    "text": p.locality.name,
                    "type": "ubicación"
                })
                ubicaciones_agregadas.add(loc)
        # Sugerencias de vendedor (sin duplicados)
        if p.seller and norm_query in normalize(p.seller.name):
            nombre = p.seller.name.strip().lower()
            if nombre not in vendedores_agregados:
                suggestions.append({
                    "text": p.seller.name,
                    "type": "vendedor",
                    "seller_id": p.seller.id
                })
                vendedores_agregados.add(nombre)
        if len(suggestions) >= 8:
            break
    # Sugerencia ortográfica con SymSpell
    suggestion = None
    symspell_suggestions = sym_spell.lookup_compound(query, max_edit_distance=2)
    if symspell_suggestions:
        corrected = symspell_suggestions[0].term
        if corrected != query:
            suggestion = corrected
    return {"suggestions": suggestions, "suggestion": suggestion}

@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    cats = db.query(Category).all()
    return {
        "categories": [
            {"value": cat.name, "label": cat.name}
            for cat in cats
        ]
    }

@router.get("/products/{product_id}", response_model=ProductSchema)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    prod_dict = ProductSchema.from_orm(product).dict()
    if product.locality:
        loc_dict = prod_dict['locality']
        loc_dict['province_name'] = product.locality.province.name if product.locality.province else None
        prod_dict['locality'] = loc_dict
    return prod_dict

@router.get("/locations")
def get_locations(db: Session = Depends(get_db)):
    provinces = db.query(Province).all()
    localities = db.query(Locality).all()
    return {
        "provinces": [
            {"id": p.id, "name": p.name} for p in provinces
        ],
        "localities": [
            {"id": l.id, "name": l.name, "province_id": l.province_id} for l in localities
        ]
    }

@router.post("/products/{product_id}/view")
def increment_view(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    product.views += 1
    db.commit()
    return {"views": product.views}

@router.post("/products/{product_id}/search")
def increment_search(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    product.searches += 1
    db.commit()
    return {"searches": product.searches}

@router.post("/products/{product_id}/featured")
def set_featured(
    product_id: int,
    featured: bool = Body(...),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    product.featured = featured
    db.commit()
    return {"id": product.id, "featured": product.featured}

# Configuración de JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/register", response_model=UserSchema)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        name=user.name,
        email=user.email,
        is_active=True
    )
    new_user.set_password(user.password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.check_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
