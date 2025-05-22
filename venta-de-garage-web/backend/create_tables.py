from models import Base, engine

def create_tables():
    print("[DEBUG] Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("[DEBUG] Tablas creadas exitosamente.")

if __name__ == "__main__":
    create_tables() 