import time
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product

if __name__ == '__main__':
    print("[Batch Destacados] Iniciando proceso batch de actualización de destacados...")
    while True:
        try:
            db: Session = SessionLocal()
            now = datetime.utcnow()
            # Solo productos no expirados
            products = db.query(Product).filter(Product.ends_at > now).all()
            # Ordenar por búsquedas descendente
            sorted_products = sorted(products, key=lambda p: p.searches or 0, reverse=True)
            # Solo los 6 primeros pueden ser featured
            top6_ids = set(p.id for p in sorted_products[:6])
            changes = []
            for p in products:
                should_be_featured = p.id in top6_ids
                if p.featured != should_be_featured:
                    changes.append((p.id, p.featured, should_be_featured))
                    p.featured = should_be_featured
            # Además, asegurarse de que ningún producto expirado esté como featured
            expired = db.query(Product).filter(Product.ends_at <= now, Product.featured == True).all()
            for p in expired:
                changes.append((p.id, True, False))
                p.featured = False
            db.commit()
            if changes:
                print(f"[{datetime.now()}] Actualización de destacados: {changes}")
            else:
                print(f"[{datetime.now()}] Sin cambios en destacados.")
            db.close()
        except Exception as e:
            print(f"[{datetime.now()}] Error en batch de destacados: {e}")
        time.sleep(60) 