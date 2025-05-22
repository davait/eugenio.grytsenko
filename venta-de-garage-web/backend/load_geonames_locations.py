import os
import requests
import zipfile
from sqlalchemy.orm import Session
from models import engine, Country, Province, Locality

GEONAMES_ADMIN1_URL = 'https://download.geonames.org/export/dump/admin1CodesASCII.txt'
GEONAMES_AR_ZIP_URL = 'https://download.geonames.org/export/dump/AR.zip'

ADMIN1_FILE = 'admin1CodesASCII.txt'
AR_ZIP_FILE = 'AR.zip'
AR_FILE = 'AR.txt'

# Descargar archivos si no existen
def download_file(url, filename):
    if not os.path.exists(filename):
        print(f"[DEBUG] Descargando {filename}...")
        r = requests.get(url)
        with open(filename, 'wb') as f:
            f.write(r.content)
        print(f"[DEBUG] Descargado {filename} ({os.path.getsize(filename)} bytes)")
    else:
        print(f"[DEBUG] {filename} ya existe.")

def ensure_ar_txt():
    if not os.path.exists(AR_FILE):
        print(f"[DEBUG] Descomprimiendo {AR_ZIP_FILE}...")
        with zipfile.ZipFile(AR_ZIP_FILE, 'r') as zip_ref:
            zip_ref.extract(AR_FILE)
        print(f"[DEBUG] Extraído {AR_FILE} ({os.path.getsize(AR_FILE)} bytes)")
    else:
        print(f"[DEBUG] {AR_FILE} ya existe.")

def load_geonames():
    download_file(GEONAMES_ADMIN1_URL, ADMIN1_FILE)
    download_file(GEONAMES_AR_ZIP_URL, AR_ZIP_FILE)
    ensure_ar_txt()

    with Session(engine) as db:
        # Crear país Argentina
        country = db.query(Country).filter_by(code='AR').first()
        if not country:
            country = Country(name='Argentina', code='AR')
            db.add(country)
            db.flush()
        # Provincias
        prov_map = {}
        print("[DEBUG] Procesando provincias...")
        with open(ADMIN1_FILE, encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if parts[0].startswith('AR.'):
                    prov_code = parts[0].split('.')[1]
                    prov_name = parts[1]
                    prov = Province(name=prov_name, country_id=country.id)
                    db.add(prov)
                    db.flush()
                    prov_map[prov_code] = prov
        print(f"[DEBUG] Provincias cargadas: {len(prov_map)}")
        # Localidades
        loc_count = 0
        print("[DEBUG] Procesando localidades...")
        with open(AR_FILE, encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) < 11:
                    continue
                name = parts[1]
                admin1 = parts[10]  # provincia code
                latitude = float(parts[4]) if parts[4] else None
                longitude = float(parts[5]) if parts[5] else None
                if admin1 in prov_map:
                    loc = Locality(
                        name=name, 
                        province_id=prov_map[admin1].id,
                        latitude=latitude,
                        longitude=longitude
                    )
                    db.add(loc)
                    loc_count += 1
                    if loc_count % 1000 == 0:
                        db.flush()
                        print(f"[DEBUG] Localidades procesadas: {loc_count}")
        db.commit()
        print(f"[DEBUG] Cargadas {len(prov_map)} provincias y {loc_count} localidades de Argentina.")

if __name__ == "__main__":
    load_geonames() 