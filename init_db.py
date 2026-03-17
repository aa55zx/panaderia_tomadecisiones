"""
init_db.py — Inicializa panaderia.db con datos de ejemplo.
Ejecutar: python init_db.py
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database import Database

DB_PATH = os.path.join(BASE_DIR, "panaderia.db")

print("=" * 50)
print("  Panaderia El Ranchero — Inicializar BD")
print("=" * 50)
print(f"  Archivo: {DB_PATH}")
print()

db = Database()
db.connect(DB_PATH)

if db.is_panaderia_ready():
    filas = db.table_row_count("Ventas")
    print(f"  La BD ya tiene datos ({filas:,} registros en Ventas).")
    resp = input("  Borrar todo y regenerar? (s/N): ").strip().lower()
    if resp != "s":
        print("  Cancelado.")
        db.close()
        sys.exit(0)
    db.conn.executescript("""
        DROP TABLE IF EXISTS Ventas;
        DROP TABLE IF EXISTS Productos;
        DROP TABLE IF EXISTS Insumos;
    """)
    db.conn.commit()
    print("  Tablas eliminadas. Regenerando...")
    print()

print("  Creando tablas...")
print("  Generando 180 dias de datos...")
print()

db.init_panaderia(dias=180)

print("  Listo!\n")
print("  Tablas creadas:")
for tabla in db.list_tables():
    n = db.table_row_count(tabla)
    print(f"    {tabla:<20} {n:>8,} filas")

db.close()
print()
print("=" * 50)
input("  Presiona Enter para cerrar...")
