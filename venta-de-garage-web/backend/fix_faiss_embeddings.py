from sqlalchemy.orm import Session
from models import engine, Product, Category
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
def get_local_embedding(text):
    emb = model.encode([text])[0].astype('float32')
    return emb / np.linalg.norm(emb)

def fix_embeddings():
    with Session(engine) as db:
        productos = db.query(Product).all()
        for p in productos:
            categorias = ' - '.join([c.name for c in p.categories]) if p.categories else ''
            texto = f"{p.title}|{p.description}|{categorias}"
            emb = get_local_embedding(texto)
            p.embedding = emb.tobytes()
            print(f"Producto {p.id} - '{p.title}' embedding actualizado.")
        db.commit()
    print("Todos los embeddings han sido recalculados y normalizados.")

if __name__ == "__main__":
    fix_embeddings()
