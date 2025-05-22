from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from models import Base, engine
from database import get_db, SessionLocal
from schemas import ProductCreate, Product
from routes import router, build_faiss_index

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    build_faiss_index(db)
    db.close()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Origen del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Asegurarse de que los directorios existen
os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Montar los directorios de archivos estáticos
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Incluir las rutas
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 