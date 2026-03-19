"""
database.py — Modulo de acceso a MongoDB para la Panaderia El Ranchero
Colecciones: Ventas, Productos, Insumos
"""
import pandas as pd
import re
import random
from datetime import date, timedelta
from pymongo import MongoClient


# ══════════════════════════════════════════════════════════════════════════════
# Datos de semilla
# ══════════════════════════════════════════════════════════════════════════════

PRODUCTOS = [
    ("Bolillo",            "Salado",      2.50),
    ("Telera",             "Salado",      3.00),
    ("Cuernito",           "Salado",      4.00),
    ("Concha",             "Dulce",       6.00),
    ("Hojaldra",           "Dulce",       7.00),
    ("Polvoron",           "Reposteria",  5.00),
    ("Dona Glaseada",      "Reposteria",  8.00),
    ("Cubilete",           "Reposteria",  9.00),
    ("Pan de Muerto",      "Temporada",  18.00),
    ("Rosca de Reyes",     "Temporada",  45.00),
    ("Pan de Canela",      "Dulce",       5.50),
    ("Empanada de Cajeta", "Reposteria", 10.00),
]

BASES_PRODUCCION = {
    "Bolillo": 800, "Telera": 400, "Cuernito": 200,
    "Concha": 300, "Hojaldra": 250, "Polvoron": 150,
    "Dona Glaseada": 120, "Cubilete": 100,
    "Pan de Muerto": 0, "Rosca de Reyes": 0,
    "Pan de Canela": 180, "Empanada de Cajeta": 90,
}


# ══════════════════════════════════════════════════════════════════════════════
# Clase principal
# ══════════════════════════════════════════════════════════════════════════════

class Database:
    def __init__(self):
        self.client   = None
        self.db_mongo = None
        self.uri      = None

    # ── Conexion ───────────────────────────────────────────────────────────────
    def connect(self, uri: str = "mongodb://localhost:27017",
                db_name: str = "panaderia"):
        if self.client:
            self.client.close()
        self.client   = MongoClient(uri, serverSelectionTimeoutMS=3000)
        # Forzar conexion para detectar errores rapido
        self.client.admin.command("ping")
        self.db_mongo = self.client[db_name]
        self.uri      = uri

    def close(self):
        if self.client:
            self.client.close()
            self.client   = None
            self.db_mongo = None

    @property
    def is_connected(self):
        return self.client is not None

    # ── Colecciones (equivalente a tablas) ────────────────────────────────────
    def list_tables(self) -> list:
        if not self.is_connected:
            return []
        return sorted(self.db_mongo.list_collection_names())

    def list_views(self) -> list:
        # MongoDB no tiene vistas SQL; retornamos lista vacia
        return []

    def table_row_count(self, collection: str) -> int:
        try:
            return self.db_mongo[collection].count_documents({})
        except Exception:
            return 0

    def drop_table(self, collection: str):
        self.db_mongo[collection].drop()

    # ── Leer coleccion como DataFrame ─────────────────────────────────────────
    def read_table(self, collection: str) -> pd.DataFrame:
        docs = list(self.db_mongo[collection].find({}, {"_id": 0}))
        if not docs:
            return pd.DataFrame()
        return pd.DataFrame(docs)

    # ── Importar DataFrame como coleccion ─────────────────────────────────────
    def import_dataframe(self, df: pd.DataFrame, collection_name: str,
                         if_exists: str = "replace") -> int:
        clean = _clean_table_name(collection_name)
        col   = self.db_mongo[clean]
        if if_exists == "replace":
            col.drop()
        records = df.to_dict(orient="records")
        if records:
            col.insert_many(records)
        return len(records)

    # ── Consulta libre (pipeline de agregacion o find) ────────────────────────
    def execute_query(self, sql: str):
        raise NotImplementedError(
            "MongoDB no usa SQL. Usa read_table() para leer colecciones.")

    # ══════════════════════════════════════════════════════════════════════════
    # INICIALIZACION DE LA BD
    # ══════════════════════════════════════════════════════════════════════════

    def init_panaderia(self, dias: int = 180):
        """Crea las colecciones y genera datos de ejemplo para N dias."""

        # 1. Catalogo de productos
        col_prod = self.db_mongo["Productos"]
        col_prod.drop()
        col_prod.insert_many([
            {"producto_id": i + 1, "nombre": n,
             "categoria": c, "precio_unitario": p}
            for i, (n, c, p) in enumerate(PRODUCTOS)
        ])

        # 2. Ventas e Insumos por dia
        col_ventas  = self.db_mongo["Ventas"]
        col_insumos = self.db_mongo["Insumos"]
        col_ventas.drop()
        col_insumos.drop()

        hoy    = date.today()
        inicio = hoy - timedelta(days=dias - 1)

        huevo  = 48.0
        harina = 12.0
        azucar = 22.0

        ventas_batch  = []
        insumos_batch = []
        venta_id  = 1
        insumo_id = 1

        for delta in range(dias):
            dia       = inicio + timedelta(days=delta)
            fecha_iso = dia.isoformat()
            num_dia   = dia.weekday()   # 0=Lunes, 6=Domingo

            # Insumos
            huevo  = round(huevo  * random.uniform(0.98, 1.03), 2)
            harina = round(harina * random.uniform(0.99, 1.02), 2)
            azucar = round(azucar * random.uniform(0.99, 1.01), 2)

            insumos_batch.append({
                "insumo_id": insumo_id,
                "fecha":     fecha_iso,
                "huevo_kg":  huevo,
                "harina_kg": harina,
                "azucar_kg": azucar,
            })
            insumo_id += 1

            # Ventas por producto
            for nombre, categoria, precio in PRODUCTOS:
                base = BASES_PRODUCCION.get(nombre, 100)

                if nombre == "Pan de Muerto" and dia.month in (10, 11):
                    base = random.randint(100, 400)
                elif nombre == "Rosca de Reyes" and dia.month == 1 and dia.day <= 8:
                    base = random.randint(15, 50)
                elif base == 0:
                    continue

                if num_dia in (5, 6):
                    base = int(base * random.uniform(1.1, 1.3))

                cantidad = int(base * random.uniform(0.75, 0.98))
                total    = round(cantidad * precio, 2)

                ventas_batch.append({
                    "venta_id":       venta_id,
                    "fecha":          fecha_iso,
                    "producto":       nombre,
                    "categoria":      categoria,
                    "cantidad":       cantidad,
                    "precio_unitario": precio,
                    "total":          total,
                })
                venta_id += 1

        # Insertar en lotes
        if ventas_batch:
            col_ventas.insert_many(ventas_batch)
        if insumos_batch:
            col_insumos.insert_many(insumos_batch)

    def is_panaderia_ready(self) -> bool:
        """True si las colecciones ya existen y tienen datos."""
        collections = set(self.list_tables())
        required    = {"Productos", "Ventas", "Insumos"}
        if not required.issubset(collections):
            return False
        return self.table_row_count("Ventas") > 0


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _clean_table_name(name: str) -> str:
    clean = re.sub(r"[^\w]", "_", name.strip())
    if clean and clean[0].isdigit():
        clean = "t_" + clean
    return clean or "coleccion"
