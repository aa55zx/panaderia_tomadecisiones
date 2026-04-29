"""
init_db.py — Inicializa la base de datos MongoDB para Panaderia El Ranchero.
Ejecutar: python init_db.py
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database import Database

URI     = "mongodb://localhost:27017"
DB_NAME = "panaderia"

print("=" * 52)
print("  Panaderia El Ranchero — Inicializar MongoDB")
print("=" * 52)
print(f"  URI     : {URI}")
print(f"  Base DB : {DB_NAME}")
print()

db = Database()

try:
    db.connect(uri=URI, db_name=DB_NAME)
    print("  Conexion a MongoDB: OK")
except Exception as e:
    print(f"\n  [ERROR] No se pudo conectar a MongoDB:")
    print(f"  {e}")
    print()
    print("  Asegurate de que MongoDB este corriendo.")
    print("  Descargalo en: https://www.mongodb.com/try/download/community")
    print()
    input("  Presiona Enter para cerrar...")
    sys.exit(1)

if db.is_panaderia_ready():
    filas = db.table_row_count("Ventas")
    print(f"  La BD ya tiene datos ({filas:,} registros en Ventas).")
    resp = input("  Borrar todo y regenerar? (s/N): ").strip().lower()
    if resp != "s":
        print("  Cancelado.")
        db.close()
        sys.exit(0)
    print("  Eliminando colecciones existentes...")
    for col in ["Ventas", "Productos", "Insumos"]:
        db.drop_table(col)
    print()

print("  Creando colecciones...")
print("  Generando 180 dias de datos de ejemplo...")
print()

db.init_panaderia(dias=180)

print("  Listo!\n")
print("  Colecciones creadas:")
for tabla in db.list_tables():
    n = db.table_row_count(tabla)
    print(f"    {tabla:<20} {n:>8,} documentos")

db.close()
print()
print("=" * 52)
input("  Presiona Enter para cerrar...")
