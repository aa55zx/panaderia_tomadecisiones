import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import os
import json
import urllib.request
import urllib.parse
import random
from datetime import datetime, timedelta
from collections import Counter
from database import Database

# Colores
BG      = "#F7F3EE"
HDR     = "#2D1B0E"
ACCENT  = "#C8622A"
BLUE    = "#4A7FA5"
PURPLE  = "#6B4E8A"
TEXT    = "#1A1008"
TEXT2   = "#7A5C4A"
BORDER  = "#DDD0C4"
ROW_ALT = "#FAF6F2"
WHITE   = "#FFFFFF"
SUCCESS = "#2D7A4F"
WARNING = "#B07D1A"
DANGER  = "#B03030"

PALABRAS_NEGATIVAS = [
    "seco","duro","frio","frio","malo","feo","terrible","horrible","pesimo",
    "tardaron","tarde","sucio","quemado","crudo","insipido","caro","raro",
    "viejo","desagradable","amargo","salado","grasoso","desabrido","triste",
    "decepcionante","error","pequeno","viejo","pesado",
]
PALABRAS_POSITIVAS = [
    "rico","delicioso","bueno","excelente","fresco","suave","sabroso","perfecto",
    "increible","maravilloso","espectacular","genial","recomiendo","rapido",
    "amable","limpio","caliente","esponjoso","crujiente","barato","bien",
    "gracias","encanta","favorito","siempre","vuelvo","buenisimo","rico",
]


# Datos demo de clima para Oaxaca
CLIMAS_DEMO = [
    ("Lluvia ligera",  14.2, 12.0, 68, 4.2, "Rain"),
    ("Nublado",        18.5, 16.0, 55, 2.1, "Clouds"),
    ("Soleado",        26.3, 24.0, 38, 1.8, "Clear"),
    ("Tormenta",       13.0, 11.0, 82, 7.5, "Thunderstorm"),
    ("Frio extremo",    9.8,  7.0, 70, 3.0, "Clouds"),
    ("Caluroso",       31.5, 29.0, 25, 1.2, "Clear"),
    ("Nublado",        20.1, 17.5, 60, 2.8, "Clouds"),
    ("Lluvia fuerte",  12.5, 10.0, 90, 8.0, "Rain"),
    ("Parcialmente nublado", 23.0, 20.5, 45, 2.0, "Clouds"),
]


def _alerta_ventas(temp, lluvia, condicion):
    alertas = []
    if condicion in ("Rain", "Drizzle", "Thunderstorm") or lluvia > 0:
        alertas.append("Subir produccion pan dulce")
    if temp < 15:
        alertas.append("Alta demanda pan y cafe")
    if temp > 28:
        alertas.append("Menor demanda pan caliente")
    return " | ".join(alertas) if alertas else "Demanda normal"


def _clima_demo(ciudad):
    ahora = datetime.now()
    rows = []
    presiones = [1012, 1008, 1018, 1003, 1005, 1020, 1010, 1001, 1015]
    for i, (cond, tmax, tmin, hum, viento, main) in enumerate(CLIMAS_DEMO):
        momento = "Ahora" if i == 0 else (ahora + timedelta(hours=i*3)).strftime("%Y-%m-%d %H:%M")
        lluvia  = round(random.uniform(0.5, 5.0), 1) if main in ("Rain","Thunderstorm") else 0.0
        rows.append({
            "Momento"       : momento,
            "Ciudad"        : ciudad,
            "Temperatura C" : tmax,
            "Sensacion C"   : tmin,
            "Humedad %"     : hum,
            "Condicion"     : cond,
            "Lluvia mm"     : lluvia,
            "Viento km/h"   : viento,
            "Presion hPa"   : presiones[i],
        })
    return pd.DataFrame(rows)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Panaderia El Ranchero")
        self.geometry("1150x700")
        self.minsize(900, 520)
        self.configure(bg=BG)
        self.db  = Database()
        self.df  = None

        self._setup_styles()
        self._build_ui()
        self._autoconnect()

    def _setup_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("App.Treeview",
                    background=WHITE, foreground=TEXT,
                    fieldbackground=WHITE, rowheight=30,
                    font=("Segoe UI", 10), borderwidth=0)
        s.configure("App.Treeview.Heading",
                    background=HDR, foreground=WHITE,
                    font=("Segoe UI", 10, "bold"), relief="flat", padding=[10,8])
        s.map("App.Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", WHITE)])
        s.configure("TScrollbar", background=BORDER,
                    troughcolor=BG, borderwidth=0, relief="flat")

    def _build_ui(self):
        # Encabezado
        hdr = tk.Frame(self, bg=HDR, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Panaderia El Ranchero",
                 font=("Segoe UI", 16, "bold"),
                 bg=HDR, fg=WHITE).pack(side="left", padx=24)
        self.lbl_fuente = tk.Label(hdr, text="Sin datos cargados",
                                   font=("Segoe UI", 10),
                                   bg=HDR, fg="#C8A080")
        self.lbl_fuente.pack(side="right", padx=24)

        # Barra de botones
        bar = tk.Frame(self, bg=BG, pady=14)
        bar.pack(fill="x", padx=20)

        def btn(text, desc, cmd, color):
            outer = tk.Frame(bar, bg=BG)
            outer.pack(side="left", padx=(0,10))
            tk.Button(outer, text=text, command=cmd,
                      bg=color, fg=WHITE, relief="flat",
                      font=("Segoe UI", 10, "bold"),
                      cursor="hand2", padx=16, pady=9,
                      activebackground=HDR, activeforeground=WHITE
                      ).pack()
            tk.Label(outer, text=desc, font=("Segoe UI", 8),
                     fg=TEXT2, bg=BG).pack(pady=(3,0))

        btn("Base de Datos",  "Tablas de la BD",         self.importar_bd,         ACCENT)
        btn("Excel",          "Archivo .xlsx / .xls",    self.importar_excel,       ACCENT)
        btn("URL / CSV",      "Datos desde internet",    self.importar_externo,     BLUE)
        btn("Clima",          "OpenWeather en tiempo real", self.importar_clima,    "#2E86AB")
        btn("Comentarios",    "Analizar redes sociales", self.analizar_comentarios, PURPLE)
        btn("Calidad de Datos", "Explorar, limpiar y normalizar", self.calidad_datos, SUCCESS)

        tk.Frame(bar, bg=BORDER, width=1).pack(side="left", fill="y", padx=14)
        info = tk.Frame(bar, bg=BG)
        info.pack(side="left")
        self.lbl_filas = tk.Label(info, text="", font=("Segoe UI", 10, "bold"),
                                  fg=ACCENT, bg=BG)
        self.lbl_filas.pack(anchor="w")
        self.lbl_cols  = tk.Label(info, text="", font=("Segoe UI", 9),
                                  fg=TEXT2, bg=BG)
        self.lbl_cols.pack(anchor="w")

        sf = tk.Frame(bar, bg=BG)
        sf.pack(side="right")
        tk.Label(sf, text="Buscar:", font=("Segoe UI", 10),
                 fg=TEXT2, bg=BG).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._filtrar)
        tk.Entry(sf, textvariable=self.search_var,
                 bg=WHITE, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=("Segoe UI", 10),
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT, width=22
                 ).pack(side="left", padx=(6,0), ipady=5)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # Tabla
        tf = tk.Frame(self, bg=WHITE)
        tf.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tf, style="App.Treeview",
                                 show="headings", selectmode="browse")
        vsb = ttk.Scrollbar(tf, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tf.rowconfigure(0, weight=1); tf.columnconfigure(0, weight=1)

        # Barra de estado
        status = tk.Frame(self, bg=HDR, pady=5)
        status.pack(fill="x")
        self.lbl_status = tk.Label(status, text="Listo",
                                   font=("Segoe UI", 9),
                                   bg=HDR, fg="#C8A080")
        self.lbl_status.pack(side="left", padx=16)

    # ── Boton 1: Base de Datos ────────────────────────────────────────────────
    def importar_bd(self):
        if not self.db.is_connected:
            path = filedialog.askopenfilename(
                title="Abrir base de datos",
                filetypes=[("SQLite","*.db *.sqlite"),("All","*.*")])
            if not path: return
            self.db.connect(path)

        EXCLUIR = {"Dim_Clima"}
        tablas = [t for t in self.db.list_tables() if t not in EXCLUIR]
        tablas += self.db.list_views()
        if not tablas:
            messagebox.showinfo("Sin tablas",
                "La BD no tiene tablas.\nEjecuta init_db.py primero.")
            return
        self._dialogo_lista("Seleccionar tabla", tablas,
            lambda t: self._cargar_df(self.db.read_table(t), "BD: " + t),
            info_fn=lambda t: str(self.db.table_row_count(t)) + " filas")

    # ── Boton 2: Excel ────────────────────────────────────────────────────────
    def importar_excel(self):
        path = filedialog.askopenfilename(
            title="Abrir archivo Excel",
            filetypes=[("Excel","*.xlsx *.xls *.xlsm"),("All","*.*")])
        if not path: return
        try:
            sheets  = pd.read_excel(path, sheet_name=None)
            nombres = list(sheets.keys())
            if len(nombres) == 1:
                self._cargar_df(sheets[nombres[0]], "Excel: " + nombres[0])
            else:
                self._dialogo_lista("Seleccionar hoja", nombres,
                    lambda n: self._cargar_df(sheets[n], "Excel: " + n))
        except Exception as e:
            messagebox.showerror("Error", "No se pudo abrir:\n" + str(e))

    # ── Boton 3: URL / CSV ────────────────────────────────────────────────────
    def importar_externo(self):
        win = self._ventana("Importar desde URL", 500, 200)
        tk.Label(win, text="URL del archivo CSV:",
                 font=("Segoe UI", 11, "bold"), fg=TEXT, bg=BG
                 ).pack(pady=(20,4), padx=20, anchor="w")
        tk.Label(win, text="Ejemplo: https://datos.gob.mx/archivo.csv",
                 font=("Segoe UI", 9), fg=TEXT2, bg=BG
                 ).pack(padx=20, anchor="w")
        url_var = tk.StringVar()
        tk.Entry(win, textvariable=url_var, bg=WHITE, fg=TEXT,
                 insertbackground=TEXT, relief="flat",
                 font=("Segoe UI", 10),
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT
                 ).pack(fill="x", padx=20, pady=(10,4), ipady=6)
        lbl_err = tk.Label(win, text="", font=("Segoe UI", 9),
                           fg=DANGER, bg=BG)
        lbl_err.pack(padx=20, anchor="w")

        def cargar():
            url = url_var.get().strip()
            if not url:
                lbl_err.config(text="Escribe una URL."); return
            try:
                lbl_err.config(text="Descargando...", fg=TEXT2); win.update()
                df = pd.read_csv(url)
                win.destroy()
                self._cargar_df(df, "URL: " + url.split("/")[-1])
            except Exception as e:
                lbl_err.config(text="Error: " + str(e), fg=DANGER)

        self._btn_win(win, "Cargar datos", cargar, BLUE)

    # ── Boton 4: Clima ────────────────────────────────────────────────────────
    def importar_clima(self):
        win = self._ventana("Consultar Clima", 480, 310)

        tk.Label(win, text="Datos de Clima en Tiempo Real",
                 font=("Segoe UI", 12, "bold"), fg=TEXT, bg=BG
                 ).pack(pady=(16,2), padx=20, anchor="w")
        tk.Label(win,
                 text="Dias frios o lluviosos = mayor demanda de pan dulce y cafe.\n"
                      "Si aun no tienes API Key usa el boton Demo.",
                 font=("Segoe UI", 9), fg=TEXT2, bg=BG, justify="left"
                 ).pack(padx=20, anchor="w", pady=(0,10))

        r1 = tk.Frame(win, bg=BG); r1.pack(fill="x", padx=20, pady=3)
        tk.Label(r1, text="Ciudad:", font=("Segoe UI", 10),
                 fg=TEXT2, bg=BG, width=12, anchor="w").pack(side="left")
        ciudad_var = tk.StringVar(value="Oaxaca,MX")
        tk.Entry(r1, textvariable=ciudad_var, bg=WHITE, fg=TEXT,
                 relief="flat", font=("Segoe UI", 10),
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT
                 ).pack(side="left", fill="x", expand=True, ipady=5)

        r2 = tk.Frame(win, bg=BG); r2.pack(fill="x", padx=20, pady=3)
        tk.Label(r2, text="API Key:", font=("Segoe UI", 10),
                 fg=TEXT2, bg=BG, width=12, anchor="w").pack(side="left")
        api_var = tk.StringVar()
        tk.Entry(r2, textvariable=api_var, bg=WHITE, fg=TEXT,
                 relief="flat", font=("Segoe UI", 10),
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT
                 ).pack(side="left", fill="x", expand=True, ipady=5)

        tk.Label(win,
                 text="Clave gratuita en: openweathermap.org/api  "
                      "(las claves nuevas tardan hasta 2 h en activarse)",
                 font=("Segoe UI", 8), fg=WARNING, bg=BG
                 ).pack(padx=20, anchor="w", pady=(2,4))

        lbl_err = tk.Label(win, text="", font=("Segoe UI", 9),
                           fg=DANGER, bg=BG, wraplength=440, justify="left")
        lbl_err.pack(padx=20, anchor="w")

        def consultar_real():
            ciudad  = ciudad_var.get().strip()
            api_key = api_var.get().strip()
            if not ciudad:
                lbl_err.config(text="Escribe una ciudad.", fg=DANGER); return
            if not api_key:
                lbl_err.config(
                    text="Escribe tu API Key o usa el boton Demo.", fg=DANGER)
                return
            lbl_err.config(text="Consultando...", fg=TEXT2); win.update()
            try:
                url_actual = (
                    "https://api.openweathermap.org/data/2.5/weather"
                    "?q=" + urllib.parse.quote(ciudad) +
                    "&appid=" + api_key + "&units=metric&lang=es"
                )
                with urllib.request.urlopen(url_actual, timeout=8) as r:
                    data = json.loads(r.read())

                url_forecast = (
                    "https://api.openweathermap.org/data/2.5/forecast"
                    "?q=" + urllib.parse.quote(ciudad) +
                    "&appid=" + api_key + "&units=metric&lang=es&cnt=8"
                )
                with urllib.request.urlopen(url_forecast, timeout=8) as r:
                    forecast = json.loads(r.read())

                win.destroy()
                rows = []
                temp   = data["main"]["temp"]
                lluvia = data.get("rain", {}).get("1h", 0.0)
                rows.append({
                    "Momento"       : "Ahora",
                    "Ciudad"        : data["name"],
                    "Temperatura C" : round(temp, 1),
                    "Sensacion C"   : round(data["main"]["feels_like"], 1),
                    "Humedad %"     : data["main"]["humidity"],
                    "Condicion"     : data["weather"][0]["description"].capitalize(),
                    "Lluvia mm"     : lluvia,
                    "Viento km/h"   : round(data["wind"]["speed"] * 3.6, 1),
                    "Presion hPa"   : data["main"]["pressure"],
                })
                for item in forecast["list"]:
                    t  = item["main"]["temp"]
                    ll = item.get("rain", {}).get("3h", 0.0)
                    rows.append({
                        "Momento"       : item["dt_txt"],
                        "Ciudad"        : data["name"],
                        "Temperatura C" : round(t, 1),
                        "Sensacion C"   : round(item["main"]["feels_like"], 1),
                        "Humedad %"     : item["main"]["humidity"],
                        "Condicion"     : item["weather"][0]["description"].capitalize(),
                        "Lluvia mm"     : ll,
                        "Viento km/h"   : round(item["wind"]["speed"] * 3.6, 1),
                        "Presion hPa"   : item["main"]["pressure"],
                    })
                self._cargar_df(pd.DataFrame(rows), "Clima: " + data["name"])

            except Exception as e:
                msg = str(e)
                if "401" in msg:
                    lbl_err.config(
                        text="API Key invalida o aun no activada (puede tardar 2 h).\n"
                             "Usa el boton 'Demo sin key' para datos simulados.",
                        fg=DANGER)
                else:
                    lbl_err.config(text="Error: " + msg, fg=DANGER)

        def consultar_demo():
            ciudad = ciudad_var.get().strip() or "Oaxaca"
            win.destroy()
            self._cargar_df(_clima_demo(ciudad), "Clima demo: " + ciudad)

        brow = tk.Frame(win, bg=BG)
        brow.pack(fill="x", padx=20, pady=(8,16))
        tk.Button(brow, text="  Consultar clima  ",
                  command=consultar_real,
                  bg="#2E86AB", fg=WHITE, relief="flat",
                  font=("Segoe UI", 11, "bold"), cursor="hand2",
                  pady=9, activebackground=HDR, activeforeground=WHITE
                  ).pack(side="left", fill="x", expand=True, padx=(0,6))
        

    # ── Boton 5: Comentarios ──────────────────────────────────────────────────
    def analizar_comentarios(self):
        base = datetime.now()
        comentarios = [
            "El pan de yema estaba muy seco hoy",
            "Las conchas siempre frescas y esponjosas, me encanta",
            "Tardaron mucho en atenderme pero el pan estaba rico",
            "Hoy el bolillo estaba quemado, malo",
            "El pan de muerto estaba delicioso, el mejor de Oaxaca",
            "La hojaldra estaba muy dura y fria",
            "Excelente servicio y pan fresco, siempre vuelvo",
            "El cubilete estaba desabrido y grasoso",
            "Que rico pan, el mejor del barrio",
            "Habia poca variedad pero lo que habia estaba bueno",
        ]
        # Dias unicos y distintos dentro del ultimo mes, orden cronologico
        dias_atras = sorted(random.sample(range(1, 31), len(comentarios)))
        rows = [
            {
                "#": i,
                "Fecha": (base - timedelta(
                              days=d,
                              hours=random.randint(8, 21),
                              minutes=random.randint(0, 59)
                          )).strftime("%Y-%m-%d %H:%M"),
                "Comentario": com,
            }
            for i, (com, d) in enumerate(zip(comentarios, dias_atras), 1)
        ]
        self._cargar_df(pd.DataFrame(rows),
                        "Comentarios: " + str(len(rows)) + " registros")

    # ══════════════════════════════════════════════════════════════════════════
    # BOTON 6: CALIDAD DE DATOS
    # ══════════════════════════════════════════════════════════════════════════
    def calidad_datos(self):
        if self.df is None or self.df.empty:
            messagebox.showinfo("Sin datos",
                "Primero carga datos usando alguno de los botones superiores.")
            return

        df_original = self.df.copy()

        win = tk.Toplevel(self)
        win.title("Calidad de Datos")
        win.configure(bg=BG)
        win.geometry("820x620")
        win.minsize(700, 500)
        win.grab_set()

        # Encabezado
        tk.Label(win, text="Calidad de Datos",
                 font=("Segoe UI", 13, "bold"),
                 bg=HDR, fg=WHITE, pady=12
                 ).pack(fill="x", padx=0)
        tk.Label(win,
                 text="Datos cargados: " + self.lbl_fuente.cget("text"),
                 font=("Segoe UI", 9), fg=TEXT2, bg=BG
                 ).pack(anchor="w", padx=20, pady=(8, 0))

        # Notebook con 3 pestanas
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=14, pady=10)

        tab1 = tk.Frame(nb, bg=BG)
        tab2 = tk.Frame(nb, bg=BG)
        tab3 = tk.Frame(nb, bg=BG)
        nb.add(tab1, text="  1. Exploracion  ")
        nb.add(tab2, text="  2. Limpieza  ")
        nb.add(tab3, text="  3. Normalizacion  ")

        # ── Contenedor de texto reutilizable ─────────────────────────────────
        def text_area(parent):
            f = tk.Frame(parent, bg=WHITE,
                         highlightthickness=1, highlightbackground=BORDER)
            f.pack(fill="both", expand=True, padx=12, pady=(8, 4))
            t = scrolledtext.ScrolledText(
                f, font=("Consolas", 9), bg=WHITE, fg=TEXT,
                relief="flat", wrap="word", state="disabled",
                padx=10, pady=8)
            t.pack(fill="both", expand=True)
            return t

        def escribir(t, texto):
            t.configure(state="normal")
            t.delete("1.0", "end")
            t.insert("end", texto)
            t.configure(state="disabled")

        # ══════════════════════════════════════════════════════════════════════
        # PESTANA 1: EXPLORACION
        # ══════════════════════════════════════════════════════════════════════
        txt1 = text_area(tab1)

        def explorar():
            df  = df_original
            sep = "-" * 60
            out = []

            # a) Tipos de datos
            out.append(sep)
            out.append("A)  TIPOS DE DATOS")
            out.append(sep)
            for col in df.columns:
                tipo  = str(df[col].dtype)
                muestra = str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else "(vacio)"
                out.append(f"  {col:<25} tipo: {tipo:<12}  ejemplo: {muestra}")

            # b) Valores nulos
            out.append("")
            out.append(sep)
            out.append("B)  VALORES NULOS O VACIOS")
            out.append(sep)
            hay_nulos = False
            for col in df.columns:
                nulos  = df[col].isnull().sum()
                vacios = (df[col].astype(str).str.strip() == "").sum()
                total  = nulos + vacios
                if total > 0:
                    hay_nulos = True
                    pct = round(100 * total / len(df), 1)
                    out.append(f"  {col:<25} {total:>4} valores nulos/vacios  ({pct}%)")
            if not hay_nulos:
                out.append("  Sin valores nulos o vacios detectados.")

            # c) Duplicados
            out.append("")
            out.append(sep)
            out.append("C)  FILAS DUPLICADAS")
            out.append(sep)
            n_dup = df.duplicated().sum()
            if n_dup > 0:
                out.append(f"  Se encontraron {n_dup} filas completamente duplicadas.")
                out.append("  Ejemplo de duplicado:")
                dup_example = df[df.duplicated(keep=False)].head(2)
                for _, r in dup_example.iterrows():
                    out.append("    " + "  |  ".join(str(v) for v in r.values))
            else:
                out.append("  Sin filas duplicadas.")

            # d) Inconsistencias
            out.append("")
            out.append(sep)
            out.append("D)  INCONSISTENCIAS DETECTADAS")
            out.append(sep)
            inconsistencias = []
            for col in df.select_dtypes(include="object").columns:
                vals = df[col].dropna().astype(str)
                # Mezcla de mayusculas/minusculas
                unicos = vals.unique()
                normalizados = [v.strip().lower() for v in unicos]
                if len(set(normalizados)) < len(set(unicos)):
                    inconsistencias.append(
                        f"  '{col}': valores con distinta capitalizacion")
                    ejemplos = [v for v in unicos if v.lower() in
                                [x.lower() for x in unicos if x != v]][:4]
                    if ejemplos:
                        inconsistencias.append("    Ejemplos: " + ", ".join(ejemplos))
                # Espacios extra
                con_espacios = vals[vals != vals.str.strip()]
                if not con_espacios.empty:
                    inconsistencias.append(
                        f"  '{col}': {len(con_espacios)} valores con espacios al inicio/final")
                # Valores mixtos numericos en columna de texto
                if col.lower() in ("cantidad", "total", "precio"):
                    no_num = vals[pd.to_numeric(vals, errors="coerce").isnull()]
                    if not no_num.empty:
                        inconsistencias.append(
                            f"  '{col}': contiene valores no numericos: {list(no_num[:3])}")
            # Columnas numericas con valores negativos sospechosos
            for col in df.select_dtypes(include="number").columns:
                negativos = (df[col] < 0).sum()
                if negativos > 0:
                    inconsistencias.append(
                        f"  '{col}': {negativos} valores negativos")

            if inconsistencias:
                out.extend(inconsistencias)
            else:
                out.append("  Sin inconsistencias detectadas.")

            out.append("")
            out.append(sep)
            out.append(f"  Total de filas analizadas : {len(df):,}")
            out.append(f"  Total de columnas         : {len(df.columns)}")
            out.append(sep)

            escribir(txt1, "\n".join(out))

        tk.Button(tab1, text="  Explorar datos  ",
                  command=explorar,
                  bg=ACCENT, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"), cursor="hand2",
                  pady=7, activebackground=HDR, activeforeground=WHITE
                  ).pack(padx=12, pady=(10, 4), anchor="w")
        explorar()   # ejecutar automaticamente al abrir

        # ══════════════════════════════════════════════════════════════════════
        # PESTANA 2: LIMPIEZA
        # ══════════════════════════════════════════════════════════════════════
        txt2  = text_area(tab2)
        self._df_limpio = None

        def limpiar():
            df  = df_original.copy()
            log = []
            sep = "-" * 60

            log.append(sep)
            log.append("LIMPIEZA DE DATOS")
            log.append(sep)
            log.append(f"  Filas originales: {len(df):,}")

            # 1. Eliminar duplicados
            antes = len(df)
            df.drop_duplicates(inplace=True)
            df.reset_index(drop=True, inplace=True)
            eliminados = antes - len(df)
            log.append(f"")
            log.append(f"  [1] Duplicados eliminados       : {eliminados}")

            # 2. Eliminar filas completamente vacias
            antes = len(df)
            df.dropna(how="all", inplace=True)
            df.reset_index(drop=True, inplace=True)
            log.append(f"  [2] Filas completamente vacias  : {antes - len(df)}")

            # 3. Rellenar nulos en texto con 'Sin datos'
            cols_texto = df.select_dtypes(include="object").columns
            n_rellenos = df[cols_texto].isnull().sum().sum()
            df[cols_texto] = df[cols_texto].fillna("Sin datos")
            log.append(f"  [3] Nulos en texto rellenados   : {n_rellenos}")

            # 4. Rellenar nulos numericos con 0
            cols_num = df.select_dtypes(include="number").columns
            n_num = df[cols_num].isnull().sum().sum()
            df[cols_num] = df[cols_num].fillna(0)
            log.append(f"  [4] Nulos numericos rellenados  : {n_num}")

            # 5. Eliminar espacios en texto
            n_espacios = 0
            for col in cols_texto:
                antes_col = df[col].copy()
                df[col] = df[col].astype(str).str.strip()
                n_espacios += (antes_col != df[col]).sum()
            log.append(f"  [5] Espacios eliminados         : {n_espacios}")

            log.append("")
            log.append(sep)
            log.append(f"  Filas despues de limpieza: {len(df):,}")
            log.append(sep)

            self._df_limpio = df
            escribir(txt2, "\n".join(log))

        def aplicar_limpieza():
            if self._df_limpio is None:
                messagebox.showinfo("", "Primero haz clic en 'Limpiar datos'.")
                return
            self._cargar_df(self._df_limpio, "[Limpio] " + self.lbl_fuente.cget("text"))
            win.destroy()

        bf2 = tk.Frame(tab2, bg=BG)
        bf2.pack(padx=12, pady=(10, 4), anchor="w")
        tk.Button(bf2, text="  Limpiar datos  ",
                  command=limpiar,
                  bg=ACCENT, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"), cursor="hand2",
                  pady=7, activebackground=HDR, activeforeground=WHITE
                  ).pack(side="left")
        tk.Button(bf2, text="  Aplicar y ver en tabla  ",
                  command=aplicar_limpieza,
                  bg=SUCCESS, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"), cursor="hand2",
                  pady=7, activebackground=HDR, activeforeground=WHITE,
                  padx=12
                  ).pack(side="left", padx=(10, 0))

        # ══════════════════════════════════════════════════════════════════════
        # PESTANA 3: NORMALIZACION
        # ══════════════════════════════════════════════════════════════════════
        txt3 = text_area(tab3)
        self._df_normalizado = None

        def normalizar():
            df  = (self._df_limpio if self._df_limpio is not None
                   else df_original).copy()
            log = []
            sep = "-" * 60

            log.append(sep)
            log.append("NORMALIZACION Y ESTANDARIZACION")
            log.append(sep)

            cambios_total = 0

            # 1. Estandarizar mayusculas/minusculas en columnas de texto
            cols_texto = df.select_dtypes(include="object").columns
            log.append("")
            log.append("  [1] Estandarizacion de texto (Title Case):")
            for col in cols_texto:
                antes = df[col].copy()
                # Title case: primera letra de cada palabra en mayuscula
                df[col] = df[col].astype(str).str.strip().str.title()
                n = (antes != df[col]).sum()
                cambios_total += n
                if n > 0:
                    log.append(f"      '{col}': {n} valores corregidos")
                    # Mostrar ejemplos
                    diff = antes[antes != df[col]]
                    for orig, nuevo in zip(diff.head(3), df[col][diff.index].head(3)):
                        log.append(f"        '{orig}'  ->  '{nuevo}'")

            # 2. Corregir errores tipograficos comunes en categorias conocidas
            CORRECCIONES = {
                "Salado":     ["salado","Salado","SALADO","Saladoo","salados"],
                "Dulce":      ["dulce","Dulce","DULCE","Dulces","dulces"],
                "Reposteria": ["reposteria","Reposteria","REPOSTERIA",
                               "Reposterias","repostería","Repostería"],
                "Temporada":  ["temporada","Temporada","TEMPORADA","temporadas"],
            }
            log.append("")
            log.append("  [2] Correccion de valores de categoria:")
            n_corr = 0
            for col in cols_texto:
                for correcto, variantes in CORRECCIONES.items():
                    mask = df[col].isin(variantes) & (df[col] != correcto)
                    if mask.any():
                        n = mask.sum()
                        n_corr += n
                        cambios_total += n
                        log.append(f"      '{col}': {n} valores -> '{correcto}'")
                        df.loc[mask, col] = correcto
            if n_corr == 0:
                log.append("      Sin errores tipograficos en categorias.")

            # 3. Normalizar fechas al formato YYYY-MM-DD
            log.append("")
            log.append("  [3] Normalizacion de fechas (YYYY-MM-DD):")
            n_fechas = 0
            for col in df.columns:
                if "fecha" in col.lower() or "date" in col.lower():
                    try:
                        convertidas = pd.to_datetime(df[col], errors="coerce")
                        validas = convertidas.notna().sum()
                        if validas > 0:
                            df[col] = convertidas.dt.strftime("%Y-%m-%d").fillna(df[col])
                            n_fechas += validas
                            log.append(f"      '{col}': {validas} fechas normalizadas")
                    except Exception:
                        pass
            if n_fechas == 0:
                log.append("      Sin columnas de fecha detectadas.")

            # 4. Estandarizar columnas numericas: quitar simbolos de moneda
            log.append("")
            log.append("  [4] Limpieza de columnas numericas:")
            n_num = 0
            for col in df.select_dtypes(include="object").columns:
                col_limpia = (df[col].astype(str)
                              .str.replace(r"[$,\s]", "", regex=True)
                              .str.replace(",", "."))
                convertido = pd.to_numeric(col_limpia, errors="coerce")
                if convertido.notna().sum() > len(df) * 0.7:
                    df[col] = convertido
                    n_num += 1
                    log.append(f"      '{col}': convertida a numero")
            if n_num == 0:
                log.append("      Sin columnas de texto convertibles a numero.")

            log.append("")
            log.append(sep)
            log.append(f"  Total de cambios aplicados: {cambios_total}")
            log.append(f"  Filas finales            : {len(df):,}")
            log.append(sep)

            self._df_normalizado = df
            escribir(txt3, "\n".join(log))

        def aplicar_normalizacion():
            if self._df_normalizado is None:
                messagebox.showinfo("", "Primero haz clic en 'Normalizar'.")
                return
            self._cargar_df(self._df_normalizado,
                            "[Normalizado] " + self.lbl_fuente.cget("text"))
            win.destroy()

        bf3 = tk.Frame(tab3, bg=BG)
        bf3.pack(padx=12, pady=(10, 4), anchor="w")
        tk.Button(bf3, text="  Normalizar  ",
                  command=normalizar,
                  bg=ACCENT, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"), cursor="hand2",
                  pady=7, activebackground=HDR, activeforeground=WHITE
                  ).pack(side="left")
        tk.Button(bf3, text="  Aplicar y ver en tabla  ",
                  command=aplicar_normalizacion,
                  bg=SUCCESS, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"), cursor="hand2",
                  pady=7, activebackground=HDR, activeforeground=WHITE,
                  padx=12
                  ).pack(side="left", padx=(10, 0))

    # ── Helpers de UI ─────────────────────────────────────────────────────────
    def _ventana(self, titulo, w, h):
        win = tk.Toplevel(self)
        win.title(titulo)
        win.configure(bg=BG)
        win.geometry(str(w) + "x" + str(h))
        win.resizable(False, False)
        win.grab_set()
        return win

    def _btn_win(self, win, texto, cmd, color):
        tk.Button(win, text="  " + texto + "  ", command=cmd,
                  bg=color, fg=WHITE, relief="flat",
                  font=("Segoe UI", 11, "bold"), cursor="hand2",
                  pady=9, activebackground=HDR, activeforeground=WHITE
                  ).pack(fill="x", padx=20, pady=(8,16))

    def _dialogo_lista(self, titulo, items, on_select, info_fn=None):
        win = self._ventana(titulo, 380, 400)
        tk.Label(win, text="Elige una opcion:",
                 font=("Segoe UI", 11, "bold"), fg=TEXT, bg=BG
                 ).pack(pady=(18,8), padx=20, anchor="w")
        lb_frame = tk.Frame(win, bg=WHITE,
                            highlightthickness=1, highlightbackground=BORDER)
        lb_frame.pack(fill="both", expand=True, padx=20)
        lb = tk.Listbox(lb_frame, bg=WHITE, fg=TEXT,
                        selectbackground=ACCENT, selectforeground=WHITE,
                        font=("Segoe UI", 11), relief="flat",
                        borderwidth=0, activestyle="none",
                        highlightthickness=0, cursor="hand2")
        vsb = ttk.Scrollbar(lb_frame, command=lb.yview)
        lb.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        lb.pack(fill="both", expand=True)
        for it in items:
            sufijo = "  (" + info_fn(it) + ")" if info_fn else ""
            lb.insert("end", "  " + it + sufijo)
        lb.selection_set(0)

        def cargar():
            sel = lb.curselection()
            if not sel: return
            item = items[sel[0]]
            win.destroy()
            try:
                on_select(item)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        lb.bind("<Double-Button-1>", lambda e: cargar())
        self._btn_win(win, "Cargar", cargar, ACCENT)

    # ── Tabla ─────────────────────────────────────────────────────────────────
    def _cargar_df(self, df, fuente=""):
        self.df = df.copy()
        self.search_var.set("")
        self._llenar_tabla(self.df)
        self.lbl_fuente.config(text=fuente)
        self.lbl_status.config(text="Datos cargados: " + fuente)

    def _llenar_tabla(self, df):
        self.tree.delete(*self.tree.get_children())
        cols = list(df.columns.astype(str))
        self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=c,
                              command=lambda _c=c: self._ordenar(_c, False))
            ancho = max(90, min(260, len(c)*11+24))
            self.tree.column(c, width=ancho, minwidth=60, anchor="w")
        for i, (_, row) in enumerate(df.iterrows()):
            tag = "alt" if i % 2 else ""
            self.tree.insert("", "end", tags=(tag,),
                             values=[str(v) if pd.notna(v) else "" for v in row])
        self.tree.tag_configure("alt", background=ROW_ALT)
        self.lbl_filas.config(text=str(len(df)) + " filas")
        self.lbl_cols.config(text=str(len(cols)) + " columnas")

    def _filtrar(self, *_):
        if self.df is None: return
        q = self.search_var.get().lower()
        if not q:
            self._llenar_tabla(self.df); return
        mask = self.df.apply(
            lambda c: c.astype(str).str.lower()
                       .str.contains(q, na=False)).any(axis=1)
        self._llenar_tabla(self.df[mask])

    def _ordenar(self, col, reverse):
        if self.df is None: return
        try:
            self.df.sort_values(col, ascending=not reverse,
                                inplace=True, ignore_index=True)
            self._llenar_tabla(self.df)
            self.tree.heading(col,
                command=lambda: self._ordenar(col, not reverse))
        except Exception:
            pass

    def _autoconnect(self):
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "panaderia.db")
        if os.path.exists(ruta):
            self.db.connect(ruta)
            self.lbl_status.config(text="Base de datos conectada: panaderia.db")


if __name__ == "__main__":
    app = App()
    app.mainloop()
