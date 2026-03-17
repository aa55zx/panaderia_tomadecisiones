"""
database.py — Modulo de acceso a SQLite para la Panaderia El Ranchero
Esquema simple con datos crudos: Ventas, Productos, Insumos.
"""
import sqlite3
import pandas as pd
import re
import random
from datetime import date, timedelta


# ══════════════════════════════════════════════════════════════════════════════
# DDL — Esquema simplificado (solo datos crudos)
# ══════════════════════════════════════════════════════════════════════════════

DDL_SCHEMA = """
-- Productos disponibles en la panaderia
CREATE TABLE IF NOT EXISTS Productos (
    producto_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT    NOT NULL UNIQUE,
    categoria       TEXT    NOT NULL,
    precio_unitario REAL    NOT NULL
);

-- Registro de ventas diarias por producto
CREATE TABLE IF NOT EXISTS Ventas (
    venta_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha           TEXT    NOT NULL,
    producto        TEXT    NOT NULL,
    categoria       TEXT    NOT NULL,
    cantidad        INTEGER NOT NULL,
    precio_unitario REAL    NOT NULL,
    total           REAL    NOT NULL
);

-- Precios de insumos por fecha
CREATE TABLE IF NOT EXISTS Insumos (
    insumo_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha           TEXT    NOT NULL,
    huevo_kg        REAL    NOT NULL,
    harina_kg       REAL    NOT NULL,
    azucar_kg       REAL    NOT NULL
);
"""

# ══════════════════════════════════════════════════════════════════════════════
# Datos de semilla
# ══════════════════════════════════════════════════════════════════════════════

PRODUCTOS = [
    # (nombre, categoria, precio)
    ("Bolillo",            "Salado",     2.50),
    ("Telera",             "Salado",     3.00),
    ("Cuernito",           "Salado",     4.00),
    ("Concha",             "Dulce",      6.00),
    ("Hojaldra",           "Dulce",      7.00),
    ("Polvoron",           "Reposteria", 5.00),
    ("Dona Glaseada",      "Reposteria", 8.00),
    ("Cubilete",           "Reposteria", 9.00),
    ("Pan de Muerto",      "Temporada", 18.00),
    ("Rosca de Reyes",     "Temporada", 45.00),
    ("Pan de Canela",      "Dulce",      5.50),
    ("Empanada de Cajeta", "Reposteria",10.00),
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
        self.conn = None
        self.path = None

    # ── Conexion ───────────────────────────────────────────────────────────────
    def connect(self, path: str):
        if self.conn:
            self.conn.close()
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.path = path

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.path = None

    @property
    def is_connected(self):
        return self.conn is not None

    # ── Tablas ─────────────────────────────────────────────────────────────────
    def list_tables(self) -> list:
        if not self.is_connected:
            return []
        cur = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        return [r[0] for r in cur.fetchall()]

    def list_views(self) -> list:
        if not self.is_connected:
            return []
        cur = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
        return [r[0] for r in cur.fetchall()]

    def table_row_count(self, table: str) -> int:
        try:
            cur = self.conn.execute(f'SELECT COUNT(*) FROM "{table}"')
            return cur.fetchone()[0]
        except Exception:
            return 0

    def drop_table(self, table: str):
        self.conn.execute(f'DROP TABLE IF EXISTS "{table}"')
        self.conn.commit()

    # ── Importar DataFrame ─────────────────────────────────────────────────────
    def import_dataframe(self, df: pd.DataFrame, table_name: str,
                         if_exists: str = "replace") -> int:
        clean = _clean_table_name(table_name)
        df.to_sql(clean, self.conn, if_exists=if_exists, index=False)
        self.conn.commit()
        return len(df)

    # ── Consultas ──────────────────────────────────────────────────────────────
    def execute_query(self, sql: str):
        sql = sql.strip()
        if not sql:
            raise ValueError("La consulta esta vacia.")
        cur = self.conn.execute(sql)
        if cur.description:
            cols = [d[0] for d in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=cols)
        self.conn.commit()
        return None

    def read_table(self, table: str) -> pd.DataFrame:
        return pd.read_sql_query(f'SELECT * FROM "{table}"', self.conn)

    # ══════════════════════════════════════════════════════════════════════════
    # INICIALIZACION DE LA BD
    # ══════════════════════════════════════════════════════════════════════════

    def init_panaderia(self, dias: int = 180):
        """Crea las tablas y genera datos de ejemplo para N dias."""

        # 1. Crear tablas
        self.conn.executescript(DDL_SCHEMA)
        self.conn.commit()

        # 2. Insertar catalogo de productos
        self.conn.executemany(
            "INSERT OR IGNORE INTO Productos (nombre, categoria, precio_unitario) VALUES (?,?,?)",
            PRODUCTOS
        )
        self.conn.commit()

        # 3. Generar ventas e insumos por dia
        hoy    = date.today()
        inicio = hoy - timedelta(days=dias - 1)

        huevo  = 48.0
        harina = 12.0
        azucar = 22.0

        for delta in range(dias):
            dia       = inicio + timedelta(days=delta)
            fecha_iso = dia.isoformat()
            num_dia   = dia.weekday()   # 0=Lunes, 6=Domingo

            # ── Insumos del dia ───────────────────────────────────────────────
            huevo  = round(huevo  * random.uniform(0.98, 1.03), 2)
            harina = round(harina * random.uniform(0.99, 1.02), 2)
            azucar = round(azucar * random.uniform(0.99, 1.01), 2)

            self.conn.execute(
                "INSERT INTO Insumos (fecha, huevo_kg, harina_kg, azucar_kg) VALUES (?,?,?,?)",
                (fecha_iso, huevo, harina, azucar)
            )

            # ── Ventas del dia por producto ───────────────────────────────────
            for nombre, categoria, precio in PRODUCTOS:
                base = BASES_PRODUCCION.get(nombre, 100)

                # Temporada especial
                if nombre == "Pan de Muerto" and dia.month in (10, 11):
                    base = random.randint(100, 400)
                elif nombre == "Rosca de Reyes" and dia.month == 1 and dia.day <= 8:
                    base = random.randint(15, 50)
                elif base == 0:
                    continue

                # Fin de semana vende mas
                if num_dia in (5, 6):
                    base = int(base * random.uniform(1.1, 1.3))

                cantidad = int(base * random.uniform(0.75, 0.98))
                total    = round(cantidad * precio, 2)

                self.conn.execute(
                    "INSERT INTO Ventas (fecha, producto, categoria, cantidad, precio_unitario, total) "
                    "VALUES (?,?,?,?,?,?)",
                    (fecha_iso, nombre, categoria, cantidad, precio, total)
                )

        self.conn.commit()

    def is_panaderia_ready(self) -> bool:
        """True si las tablas ya existen y tienen datos."""
        tables = set(self.list_tables())
        required = {"Productos", "Ventas", "Insumos"}
        if not required.issubset(tables):
            return False
        return self.table_row_count("Ventas") > 0


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _clean_table_name(name: str) -> str:
    clean = re.sub(r"[^\w]", "_", name.strip())
    if clean and clean[0].isdigit():
        clean = "t_" + clean
    return clean or "tabla"
