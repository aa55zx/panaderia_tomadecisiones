"""
main.py — Panaderia El Ranchero | Sistema de Toma de Decisiones
Dashboard principal con KPIs en tiempo real desde MongoDB.
KPIs actualizados segun documento oficial (12 indicadores).
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import json
import urllib.request
import urllib.parse
import random
from datetime import datetime, timedelta
from database import Database

# ══════════════════════════════════════════════════════════════════════════════
# PALETA DE COLORES
# ══════════════════════════════════════════════════════════════════════════════
BG         = "#F4F1ED"
SIDEBAR    = "#1E1108"
CARD       = "#FFFFFF"
ACCENT     = "#C8622A"
BLUE       = "#2E6FA3"
GREEN      = "#2A7A50"
PURPLE     = "#6B4E8A"
GOLD       = "#B8860B"
RED        = "#B03030"
TEAL       = "#1A6B6B"
BROWN      = "#9B5A1A"
OLIVE      = "#4A7A3A"
TEXT       = "#1A1008"
TEXT2      = "#6B5A4E"
TEXT_LIGHT = "#A89080"
BORDER     = "#E0D8D0"
ROW_ALT    = "#FAF7F4"
WHITE      = "#FFFFFF"
HDR_BG     = "#2A1A0C"

CC = [ACCENT, BLUE, PURPLE, GREEN, GOLD, "#2E86AB", TEAL, BROWN, OLIVE, "#5B4A8A", RED, "#8B6914"]

PALABRAS_NEGATIVAS = [
    "seco","duro","frio","malo","feo","terrible","horrible","pesimo",
    "tardaron","tarde","sucio","quemado","crudo","insipido","caro","raro",
    "viejo","desagradable","amargo","salado","grasoso","desabrido","triste",
    "decepcionante","error","pequeno","pesado",
]
PALABRAS_POSITIVAS = [
    "rico","delicioso","bueno","excelente","fresco","suave","sabroso","perfecto",
    "increible","maravilloso","espectacular","genial","recomiendo","rapido",
    "amable","limpio","caliente","esponjoso","crujiente","barato","bien",
    "gracias","encanta","favorito","siempre","vuelvo","buenisimo",
]

CLIMAS_DEMO = [
    ("Lluvia ligera", 14.2, 12.0, 68, 4.2, "Rain"),
    ("Nublado",       18.5, 16.0, 55, 2.1, "Clouds"),
    ("Soleado",       26.3, 24.0, 38, 1.8, "Clear"),
    ("Tormenta",      13.0, 11.0, 82, 7.5, "Thunderstorm"),
    ("Frio extremo",   9.8,  7.0, 70, 3.0, "Clouds"),
    ("Caluroso",      31.5, 29.0, 25, 1.2, "Clear"),
]

def _clima_demo(ciudad):
    ahora = datetime.now(); rows = []
    for i in range(48):
        cond, tmax, tmin, hum, viento, main = CLIMAS_DEMO[i % len(CLIMAS_DEMO)]
        momento = "Ahora" if i == 0 else (ahora + timedelta(minutes=i*30)).strftime("%Y-%m-%d %H:%M")
        lluvia  = round(random.uniform(0.5, 5.0), 1) if main in ("Rain","Thunderstorm") else 0.0
        rows.append({"Momento": momento, "Ciudad": ciudad,
                     "Temperatura C": round(tmax+random.uniform(-1.5, 1.5), 1),
                     "Sensacion C":   round(tmin+random.uniform(-1.0, 1.0), 1),
                     "Humedad %":     min(100, max(0, int(hum+random.randint(-5,5)))),
                     "Condicion": cond, "Lluvia mm": lluvia,
                     "Viento km/h":   round(viento+random.uniform(-0.5, 0.5), 1),
                     "Presion hPa":   random.randint(1000, 1022)})
    return pd.DataFrame(rows)

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS DE ESTILO
# ──────────────────────────────────────────────────────────────────────────────

def _card(parent, **kw):
    d = dict(bg=CARD, padx=0, pady=0, highlightthickness=1, highlightbackground=BORDER)
    d.update(kw); return tk.Frame(parent, **d)

def _btn(parent, text, cmd, bg=ACCENT, fg=WHITE, size=10, px=18, py=8):
    return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                     relief="flat", cursor="hand2",
                     font=("Segoe UI", size, "bold"),
                     activebackground=HDR_BG, activeforeground=WHITE,
                     padx=px, pady=py)

def _scroll_frame(parent):
    """Devuelve (canvas, inner_frame) con scroll vertical y rueda del ratón."""
    cv  = tk.Canvas(parent, bg=BG, highlightthickness=0)
    vsb = ttk.Scrollbar(parent, orient="vertical", command=cv.yview)
    cv.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y"); cv.pack(side="left", fill="both", expand=True)
    inn = tk.Frame(cv, bg=BG)
    wid = cv.create_window((0,0), window=inn, anchor="nw")
    inn.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
    cv.bind("<Configure>",  lambda e: cv.itemconfig(wid, width=e.width))
    cv.bind("<Enter>", lambda e: cv.bind_all("<MouseWheel>",
        lambda ev: cv.yview_scroll(int(-1*(ev.delta/120)), "units")))
    cv.bind("<Leave>", lambda e: cv.unbind_all("<MouseWheel>"))
    return cv, inn


# ══════════════════════════════════════════════════════════════════════════════
# APLICACION PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Panaderia El Ranchero — Sistema de Decisiones")
        self.geometry("1380x820")
        self.minsize(1024, 700)
        self.configure(bg=BG)
        self.db         = Database()
        self.df         = None
        self._df_fuente = ""
        self._cur_page  = None
        self._setup_styles()
        self._build_shell()
        self._autoconnect()
        self._show_page("dashboard")

    # ──────────────────────────────────────────────────────────────────────────
    def _setup_styles(self):
        s = ttk.Style(self); s.theme_use("clam")
        s.configure("App.Treeview", background=WHITE, foreground=TEXT,
                    fieldbackground=WHITE, rowheight=28, font=("Segoe UI",10), borderwidth=0)
        s.configure("App.Treeview.Heading", background=HDR_BG, foreground=WHITE,
                    font=("Segoe UI",10,"bold"), relief="flat", padding=[10,6])
        s.map("App.Treeview",
              background=[("selected",ACCENT)], foreground=[("selected",WHITE)])
        s.configure("TScrollbar", background=BORDER, troughcolor=BG, borderwidth=0, relief="flat")

    # ──────────────────────────────────────────────────────────────────────────
    def _build_shell(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=SIDEBAR, width=220)
        self.sidebar.pack(side="left", fill="y"); self.sidebar.pack_propagate(False)
        logo_f = tk.Frame(self.sidebar, bg=SIDEBAR, pady=24); logo_f.pack(fill="x")
        tk.Label(logo_f, text="🍞", font=("Segoe UI",28), bg=SIDEBAR, fg=WHITE).pack()
        tk.Label(logo_f, text="El Ranchero", font=("Segoe UI",13,"bold"),
                 bg=SIDEBAR, fg=WHITE).pack()
        tk.Label(logo_f, text="Sistema de Decisiones", font=("Segoe UI",8),
                 bg=SIDEBAR, fg=TEXT_LIGHT).pack()
        tk.Frame(self.sidebar, bg="#3A2A1A", height=1).pack(fill="x", padx=18)

        nav_items = [
            ("dashboard",   "📊  Dashboard",      "Resumen ejecutivo"),
            ("datos",       "🗄️  Datos",           "Importar y explorar"),
            ("kpis",        "📈  KPIs Detallados", "12 indicadores clave"),
            ("comentarios", "💬  Comentarios",     "Análisis de opinión"),
            ("clima",       "🌤️  Clima",           "Impacto climático"),
        ]
        self._nav_btns = {}
        nav_f = tk.Frame(self.sidebar, bg=SIDEBAR); nav_f.pack(fill="x", pady=(12,0))
        for key, label, desc in nav_items:
            bf  = tk.Frame(nav_f, bg=SIDEBAR, cursor="hand2"); bf.pack(fill="x")
            ind = tk.Frame(bf, bg=SIDEBAR, width=4); ind.pack(side="left", fill="y")
            inn = tk.Frame(bf, bg=SIDEBAR, padx=14, pady=10)
            inn.pack(side="left", fill="x", expand=True)
            lm  = tk.Label(inn, text=label, font=("Segoe UI",10,"bold"),
                           bg=SIDEBAR, fg=WHITE, anchor="w"); lm.pack(fill="x")
            ld  = tk.Label(inn, text=desc, font=("Segoe UI",8),
                           bg=SIDEBAR, fg=TEXT_LIGHT, anchor="w"); ld.pack(fill="x")
            for w in (bf,ind,inn,lm,ld):
                w.bind("<Button-1>", lambda e,k=key: self._show_page(k))
                w.configure(cursor="hand2")
            self._nav_btns[key] = (bf, ind, lm, ld)

        tk.Frame(self.sidebar, bg="#3A2A1A", height=1).pack(
            fill="x", padx=18, side="bottom", pady=(0,8))
        self.lbl_conn = tk.Label(self.sidebar, text="⚫  Conectando...",
                                 font=("Segoe UI",8), bg=SIDEBAR, fg=TEXT_LIGHT,
                                 wraplength=190, justify="left")
        self.lbl_conn.pack(side="bottom", padx=16, pady=(0,12), anchor="w")

        # Contenido principal
        self.content = tk.Frame(self, bg=BG); self.content.pack(side="left", fill="both", expand=True)
        topbar = tk.Frame(self.content, bg=WHITE,
                          highlightthickness=1, highlightbackground=BORDER)
        topbar.pack(fill="x")
        self.lbl_page_title = tk.Label(topbar, text="Dashboard",
                                       font=("Segoe UI",14,"bold"),
                                       bg=WHITE, fg=TEXT, padx=24, pady=14)
        self.lbl_page_title.pack(side="left")
        self.lbl_page_sub = tk.Label(topbar, text="", font=("Segoe UI",9),
                                     bg=WHITE, fg=TEXT2, padx=4)
        self.lbl_page_sub.pack(side="left")
        self.lbl_update = tk.Label(topbar, text="", font=("Segoe UI",8),
                                   bg=WHITE, fg=TEXT_LIGHT, padx=16)
        self.lbl_update.pack(side="right")
        self.page_frame = tk.Frame(self.content, bg=BG)
        self.page_frame.pack(fill="both", expand=True)

    # ──────────────────────────────────────────────────────────────────────────
    def _show_page(self, key):
        self._cur_page = key
        for k, (bf,ind,lm,ld) in self._nav_btns.items():
            active = (k == key)
            col = "#3A2010" if active else SIDEBAR
            bf.configure(bg=col); ind.configure(bg=ACCENT if active else SIDEBAR)
            lm.configure(bg=col, fg=WHITE)
            ld.configure(bg=col, fg="#E0C0A0" if active else TEXT_LIGHT)
        for w in self.page_frame.winfo_children(): w.destroy()
        self.page_frame.update_idletasks()
        titles = {
            "dashboard":   ("Dashboard",       "Resumen ejecutivo en tiempo real"),
            "datos":       ("Datos",           "Importar y explorar conjuntos de datos"),
            "kpis":        ("KPIs Detallados", "12 indicadores clave de rendimiento"),
            "comentarios": ("Comentarios",     "Análisis de sentimiento de clientes"),
            "clima":       ("Clima",           "Condiciones climáticas y su impacto"),
        }
        title, sub = titles.get(key, (key.capitalize(), ""))
        self.lbl_page_title.config(text=title)
        self.lbl_page_sub.config(text=sub)
        {"dashboard": self._page_dashboard, "datos": self._page_datos,
         "kpis": self._page_kpis, "comentarios": self._page_comentarios,
         "clima": self._page_clima}.get(key, lambda: None)()

    # ══════════════════════════════════════════════════════════════════════════
    # CÁLCULO DE KPIs — FÓRMULAS OFICIALES DEL PDF
    # ══════════════════════════════════════════════════════════════════════════
    def _calcular_kpis(self):
        if not self.db.is_connected or not self.db.is_panaderia_ready():
            return None
        try:
            df_v = self.db.read_table("Ventas")
            df_i = self.db.read_table("Insumos")
        except Exception:
            return None
        if df_v.empty:
            return None

        def _num(s): return pd.to_numeric(s, errors="coerce").fillna(0)
        df_v["_total"] = _num(df_v["total"])
        df_v["_cant"]  = _num(df_v["cantidad"])
        df_v["_fdt"]   = pd.to_datetime(df_v["fecha"], errors="coerce")
        df_v["_fecha"] = df_v["fecha"].astype(str)
        df_v["_dsem"]  = df_v["_fdt"].dt.dayofweek.fillna(0).astype(int)
        df_v["_mes"]   = df_v["_fdt"].dt.month.fillna(1).astype(int)
        df_v["_sem"]   = df_v["_fdt"].dt.isocalendar().week.fillna(0).astype(int)

        df_i["huevo_kg"]  = _num(df_i.get("huevo_kg",  pd.Series(dtype=float)))
        df_i["harina_kg"] = _num(df_i.get("harina_kg", pd.Series(dtype=float)))
        df_i["azucar_kg"] = _num(df_i.get("azucar_kg", pd.Series(dtype=float)))

        it  = df_v["_total"].sum()
        dp  = max(df_v["_fecha"].nunique(), 1)
        nt  = len(df_v)
        np_ = df_v["producto"].nunique()

        # ── KPI 1: TSC — Tasa de Satisfacción del Cliente ─────────────────────
        # Usa calificacion (1-5) como fuente primaria; texto como respaldo
        tc = cp = cn = 0
        califs = []          # lista de calificaciones numéricas
        fuente_com = "Sin colección Comentarios"
        try:
            df_com = self.db.read_table("Comentarios")
            if not df_com.empty:
                # ── Columna de calificación numérica ──────────────────────────
                col_cal = next((c for c in df_com.columns
                                if any(k in c.lower() for k in
                                       ["calificacion","calificación","rating",
                                        "puntuacion","puntuación","score","stars"])), None)
                # ── Columna de texto (excluye campos que sean IDs numéricos) ──
                col_c = next((c for c in df_com.columns
                              if (any(k in c.lower() for k in
                                     ["comentario","texto","comment","resena","opinion"])
                                  and not c.lower().endswith("_id"))), None)

                tc = len(df_com)
                fuente_com = f"{tc} registros reales"

                # Prioridad 1: calificación numérica
                if col_cal:
                    califs = pd.to_numeric(df_com[col_cal], errors="coerce").dropna().tolist()
                    # 4-5 = positivo, 1-2 = negativo, 3 = neutro (escala 1-5)
                    cp = sum(1 for v in califs if v >= 4)
                    cn = sum(1 for v in califs if v <= 2)
                    tc = len(califs) if califs else tc
                    fuente_com = f"{tc} calificaciones (campo '{col_cal}')"

                # Prioridad 2 / complemento: análisis de texto
                if col_c and not califs:
                    txts = df_com[col_c].dropna().astype(str).tolist()
                    tc   = len(txts)
                    cp   = sum(1 for t in txts if any(p in t.lower() for p in PALABRAS_POSITIVAS))
                    cn   = sum(1 for t in txts if any(p in t.lower() for p in PALABRAS_NEGATIVAS))
                    fuente_com = f"{tc} comentarios de texto"
        except Exception:
            pass
        tsc = round(cp / tc * 100, 1) if tc else None
        cal_prom = round(sum(califs) / len(califs), 2) if califs else None

        # ── KPI 2: PVC — Proyección de Ventas por Día ─────────────────────────
        # PVC = PMC + Ingresos Extraordinarios + ajuste Días Especiales
        # Implementado como: promedio diario ajustado (PMC) + 5% festivos
        pmc = round(it / dp, 2)
        dias_especiales_adj = round(pmc * 0.05, 2)   # ajuste estimado 5%
        pvc = round(pmc + dias_especiales_adj, 2)

        # ── KPI 3: TCL — Tendencia de Categoría Líder ─────────────────────────
        cat_tot = df_v.groupby("categoria")["_total"].sum()
        top_cat = cat_tot.idxmax() if not cat_tot.empty else "N/A"
        tcl     = round(cat_tot[top_cat] / it * 100, 1) if it and top_cat != "N/A" else 0

        # ── KPI 4: RDI — Ratio de Rotación de Insumos ─────────────────────────
        # RDI = Total harina consumida / DP
        total_harina = df_i["harina_kg"].sum() if not df_i.empty else 0
        rdi          = round(total_harina / dp, 2)

        # ── KPI 5: TVFS — Tasa de Variación en Fin de Semana ──────────────────
        # TVFS = ((VFS_actual - VFS_ant) / VFS_ant) × 100
        # Dividimos semanas por número de semana
        fds_mask = df_v["_dsem"].isin([4,5,6])
        df_fds   = df_v[fds_mask].copy()
        semanas  = sorted(df_fds["_sem"].unique())
        if len(semanas) >= 2:
            vfs_act = df_fds[df_fds["_sem"] == semanas[-1]]["_total"].sum()
            vfs_ant = df_fds[df_fds["_sem"] == semanas[-2]]["_total"].sum()
            tvfs    = round((vfs_act - vfs_ant) / vfs_ant * 100, 1) if vfs_ant else 0
        else:
            vfs_tot = df_fds["_total"].sum()
            vfs_act = vfs_tot; vfs_ant = 0
            tvfs    = 0
        tvfs_ok  = tvfs >= 0   # crecimiento o estable

        # ── KPI 6: VVC — Variación de Ventas por Categoría (Fin de Semana) ────
        # RAC = CVFS_dia - PV_dia - EV_dia
        cvfs_dia = df_fds["_total"].sum() / max(len(semanas),1) / 3  # prom diario FDS
        pv_dia   = round(it / dp, 2)
        ev_dia   = round(pv_dia * 0.03, 2)   # estimado eventos extra 3%
        rac      = round(cvfs_dia - pv_dia - ev_dia, 2)
        vvc_ok   = rac > 0

        # ── KPI 7: PMVU — Producto Más Vendido por Unidades ───────────────────
        pc   = df_v.groupby("producto")["_cant"].sum()
        pnom = pc.idxmax() if not pc.empty else "N/A"
        pcan = int(pc.max()) if not pc.empty else 0

        # ── KPI 8: IPT — Ingreso Promedio por Transacción ─────────────────────
        ipt = round(it / nt, 2) if nt else 0

        # ── KPI 9: TCD — Tasa de Calidad de Datos ─────────────────────────────
        tr    = len(df_v) + len(df_i)
        nulos = int(df_v.isnull().sum().sum()) + int(df_i.isnull().sum().sum())
        rc    = tr - nulos
        tcd   = round(rc / tr * 100, 1) if tr else 0

        # ── KPI 10: IEP — Índice de Estacionalidad del Producto ───────────────
        # IEP = VS_mes / IM  (ventas mes evaluado / promedio mensual del producto)
        nm   = max(df_v["_mes"].nunique(), 1)
        ppm  = it / (np_ * nm) if np_ * nm else 1
        pt   = df_v.groupby("producto")["_total"].sum()
        pe   = pt.idxmax() if not pt.empty else None
        iep  = 0.0
        if pe:
            pm_df = df_v[df_v["producto"] == pe]
            iep   = round((pm_df["_total"].sum() / max(pm_df["_mes"].nunique(),1)) / ppm, 2)

        # ── KPI 11: SNP — Sentimiento Negativo por Periodo ────────────────────
        snp = round(cn / tc * 100, 1) if tc else None

        # ── KPI 12: CIB — Costo de Uso de Insumos (ingreso por kg) ───────────
        # CIB = IT / TC  (ingresos totales / total insumos en kg)
        tic = df_i["huevo_kg"].sum() + df_i["harina_kg"].sum() + df_i["azucar_kg"].sum()
        cib = round(it / tic, 2) if tic else 0

        # DataFrames para gráficos
        daily = df_v.groupby("_fecha")["_total"].sum().sort_index()
        cat_data = cat_tot.sort_values(ascending=False)
        prod5    = pc.sort_values(ascending=False).head(5)

        return dict(
            it=it, dp=dp, nt=nt, np=np_,
            # KPI 1
            tsc=tsc, tc=tc, cp=cp, cn=cn, fuente_com=fuente_com, cal_prom=cal_prom,
            # KPI 2
            pvc=pvc, pmc=pmc, dias_adj=dias_especiales_adj,
            # KPI 3
            tcl=tcl, top_cat=top_cat,
            # KPI 4
            rdi=rdi, total_harina=total_harina,
            # KPI 5
            tvfs=tvfs, vfs_act=vfs_act, vfs_ant=vfs_ant, tvfs_ok=tvfs_ok,
            # KPI 6
            rac=rac, cvfs_dia=cvfs_dia, pv_dia=pv_dia, ev_dia=ev_dia, vvc_ok=vvc_ok,
            # KPI 7
            pnom=pnom, pcan=pcan,
            # KPI 8
            ipt=ipt,
            # KPI 9
            tcd=tcd, rc=rc, tr=tr,
            # KPI 10
            iep=iep, pe=pe,
            # KPI 11
            snp=snp,
            # KPI 12
            cib=cib, tic=tic,
            # Gráficos
            daily=daily, cat_data=cat_data, prod5=prod5,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # PÁGINA: DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    def _page_dashboard(self):
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import matplotlib.ticker as mticker
            HAS_MPL = True
        except ImportError:
            HAS_MPL = False

        abar = tk.Frame(self.page_frame, bg=BG, pady=10); abar.pack(fill="x", padx=24)
        lbl_status = tk.Label(abar, text="", font=("Segoe UI",9), bg=BG, fg=TEXT2)
        lbl_status.pack(side="left")
        _btn(abar, "↻  Actualizar", lambda: self._show_page("dashboard"),
             bg=ACCENT, size=9, px=14, py=6).pack(side="right")

        k = self._calcular_kpis()
        if k is None:
            self._render_no_data(self.page_frame); return

        ts = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
        self.lbl_update.config(text=f"Última actualización:  {ts}")
        lbl_status.config(text=f"MongoDB  |  {k['nt']:,} transacciones  |  {k['dp']} días", fg=GREEN)

        _, inn = _scroll_frame(self.page_frame)
        pad = 20

        # ── Fila 1: 4 métricas resumen ────────────────────────────────────────
        f1 = tk.Frame(inn, bg=BG); f1.pack(fill="x", padx=pad, pady=(pad,8))
        for label, valor, icon, color, detalle in [
            ("Ingresos Totales",   f"${k['it']:,.0f}", "💰", GREEN,  f"{k['dp']} días"),
            ("Transacciones",      f"{k['nt']:,}",     "🧾", BLUE,   f"${k['ipt']:,.0f} por transacción"),
            ("Proyección Diaria",  f"${k['pvc']:,.0f}","📅", ACCENT, "PVC ajustado"),
            ("Categoría Líder",    k['top_cat'],       "🏆", GOLD,   f"{k['tcl']}% de ventas totales"),
        ]:
            c = _card(f1); c.pack(side="left", fill="both", expand=True, padx=(0,10))
            tk.Frame(c, bg=color, height=4).pack(fill="x")
            b = tk.Frame(c, bg=CARD, padx=18, pady=14); b.pack(fill="both", expand=True)
            rt = tk.Frame(b, bg=CARD); rt.pack(fill="x")
            tk.Label(rt, text=icon, font=("Segoe UI",18), bg=CARD, fg=color).pack(side="left")
            rf = tk.Frame(rt, bg=CARD); rf.pack(side="right", fill="x", expand=True)
            tk.Label(rf, text=valor, font=("Segoe UI",20,"bold"),
                     bg=CARD, fg=TEXT, anchor="e").pack(fill="x")
            tk.Label(b, text=label, font=("Segoe UI",9,"bold"),
                     bg=CARD, fg=TEXT2, anchor="w").pack(fill="x", pady=(6,0))
            tk.Label(b, text=detalle, font=("Segoe UI",8),
                     bg=CARD, fg=TEXT_LIGHT, anchor="w").pack(fill="x")

        # ── Fila 2: gráfico + semáforo de los 12 KPIs ─────────────────────────
        f2 = tk.Frame(inn, bg=BG); f2.pack(fill="x", padx=pad, pady=(0,8))

        # Gráfico tendencia
        chart_c = _card(f2); chart_c.pack(side="left", fill="both", expand=True, padx=(0,10))
        tk.Frame(chart_c, bg=BLUE, height=4).pack(fill="x")
        ch = tk.Frame(chart_c, bg=CARD, padx=18, pady=12); ch.pack(fill="x")
        tk.Label(ch, text="Tendencia de Ventas Diarias",
                 font=("Segoe UI",11,"bold"), bg=CARD, fg=TEXT).pack(side="left")
        tk.Label(ch, text=f"Últimos {k['dp']} días",
                 font=("Segoe UI",8), bg=CARD, fg=TEXT_LIGHT).pack(side="right")
        if HAS_MPL and len(k["daily"]) >= 2:
            fig1 = Figure(figsize=(6.5, 2.6), facecolor=CARD, dpi=96)
            fig1.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.22)
            ax = fig1.add_subplot(111)
            daily = k["daily"]; x = range(len(daily))
            ax.plot(x, daily.values, color=BLUE, linewidth=2.2,
                    marker="o", markersize=3.5, markerfacecolor=WHITE,
                    markeredgewidth=1.5, markeredgecolor=BLUE)
            ax.fill_between(x, daily.values, alpha=0.10, color=BLUE)
            lbs = list(daily.index); step = max(1, len(lbs)//8)
            ax.set_xticks(list(x)[::step])
            ax.set_xticklabels(lbs[::step], rotation=30, ha="right", fontsize=7, color=TEXT2)
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"${v/1000:.0f}k"))
            ax.tick_params(axis="y", labelsize=7, colors=TEXT2)
            ax.set_facecolor(CARD)
            for sp in ax.spines.values(): sp.set_visible(False)
            ax.yaxis.grid(True, color=BORDER, linewidth=0.6, alpha=0.8)
            ax.set_axisbelow(True)
            cv1 = FigureCanvasTkAgg(fig1, master=chart_c)
            cv1.draw(); cv1.get_tk_widget().pack(fill="both", padx=4, pady=(0,10))
        else:
            tk.Label(chart_c, text="Instala matplotlib:\n  pip install matplotlib",
                     font=("Segoe UI",9), bg=CARD, fg=TEXT2, pady=40).pack()

        # Panel semáforo — los 12 KPIs con sus nombres del PDF
        kp = tk.Frame(f2, bg=BG, width=280); kp.pack(side="right", fill="both")
        kp.pack_propagate(False)
        tk.Label(kp, text="Estado de los 12 KPIs", font=("Segoe UI",10,"bold"),
                 bg=BG, fg=TEXT).pack(anchor="w", padx=2, pady=(0,4))
        # Canvas con scroll para que quepan los 12 KPIs sin que nada los tape
        kpi_cv  = tk.Canvas(kp, bg=BG, highlightthickness=0)
        kpi_vsb = ttk.Scrollbar(kp, orient="vertical", command=kpi_cv.yview)
        kpi_cv.configure(yscrollcommand=kpi_vsb.set)
        kpi_vsb.pack(side="right", fill="y")
        kpi_cv.pack(side="left", fill="both", expand=True)
        kpi_inner = tk.Frame(kpi_cv, bg=BG)
        kpi_wid = kpi_cv.create_window((0, 0), window=kpi_inner, anchor="nw")
        kpi_inner.bind("<Configure>", lambda e: kpi_cv.configure(
            scrollregion=kpi_cv.bbox("all")))
        kpi_cv.bind("<Configure>", lambda e: kpi_cv.itemconfig(kpi_wid, width=e.width))
        kpi_cv.bind("<Enter>", lambda e: kpi_cv.bind_all("<MouseWheel>",
            lambda ev: kpi_cv.yview_scroll(int(-1*(ev.delta/120)), "units")))
        kpi_cv.bind("<Leave>", lambda e: kpi_cv.unbind_all("<MouseWheel>"))
        kp = kpi_inner  # redirigir el resto del código al frame interno

        semaforo_items = [
            ("TSC",  "Satisfacción Cliente",
             f"{k['tsc']}%" if k['tsc'] is not None else "N/D",
             k['tsc'] is not None and k['tsc'] >= 70,
             f"≥4 estrellas | Prom: {k['cal_prom']}/5" if k['cal_prom'] else "≥ 70%"),
            ("PVC",  "Proyección Ventas/Día",
             f"${k['pvc']:,.0f}", True, f"PMC ${k['pmc']:,.0f}"),
            ("TCL",  "Categoría Líder",
             f"{k['tcl']}%", k['tcl'] >= 25, "≥ 25%"),
            ("RDI",  "Rotación Insumos",
             f"{k['rdi']:.1f} kg/día", k['rdi'] >= 12, "≥ 12 kg/día"),
            ("TVFS", "Var. Fin de Semana",
             f"{k['tvfs']:+.1f}%", k['tvfs_ok'], "≥ 0%"),
            ("VVC",  "Var. Ventas Cat.",
             f"${k['rac']:,.0f}", k['vvc_ok'], "> $0"),
            ("PMVU", "Prod. + Vendido",
             k['pnom'][:12], True, f"{k['pcan']:,} u"),
            ("IPT",  "Ingreso/Transacción",
             f"${k['ipt']:,.0f}", True, f"{k['nt']:,} transac."),
            ("TCD",  "Calidad de Datos",
             f"{k['tcd']}%", k['tcd'] >= 95, "≥ 95%"),
            ("IEP",  "Estacionalidad Prod.",
             f"{k['iep']:.2f}×", k['iep'] >= 1, "> 1×"),
            ("SNP",  "Sentim. Negativo",
             f"{k['snp']}%" if k['snp'] is not None else "N/D",
             k['snp'] is not None and k['snp'] <= 20, "≤ 20%"),
            ("CIB",  "Costo Uso Insumos",
             f"${k['cib']:,.2f}/kg", k['cib'] > 0, "Mayor = mejor"),
        ]
        for sigla, nombre, valor, ok, meta in semaforo_items:
            ic = _card(kp); ic.pack(fill="x", pady=(0,4))
            dot = GREEN if ok else RED
            b2 = tk.Frame(ic, bg=CARD, padx=10, pady=5); b2.pack(fill="x")
            # Indicador de color lateral
            tk.Frame(b2, bg=dot, width=3).pack(side="left", fill="y", padx=(0,8))
            l2 = tk.Frame(b2, bg=CARD); l2.pack(side="left", fill="x", expand=True)
            tk.Label(l2, text=sigla, font=("Segoe UI",8,"bold"),
                     bg=CARD, fg=dot, anchor="w").pack(fill="x")
            tk.Label(l2, text=nombre, font=("Segoe UI",7),
                     bg=CARD, fg=TEXT2, anchor="w").pack(fill="x")
            r2 = tk.Frame(b2, bg=CARD); r2.pack(side="right")
            tk.Label(r2, text=valor, font=("Segoe UI",9,"bold"),
                     bg=CARD, fg=dot).pack(anchor="e")
            tk.Label(r2, text=meta, font=("Segoe UI",7),
                     bg=CARD, fg=TEXT_LIGHT).pack(anchor="e")

        # ── Fila 3: categorías + donut productos ──────────────────────────────
        if HAS_MPL:
            f3 = tk.Frame(inn, bg=BG); f3.pack(fill="x", padx=pad, pady=(0,pad))

            cc = _card(f3); cc.pack(side="left", fill="both", expand=True, padx=(0,10))
            tk.Frame(cc, bg=ACCENT, height=4).pack(fill="x")
            tk.Label(cc, text="Ventas por Categoría — TCL",
                     font=("Segoe UI",11,"bold"), bg=CARD, fg=TEXT,
                     padx=18, pady=12).pack(anchor="w")
            cat = k["cat_data"]
            n_cats = len(k["cat_data"]) if not k["cat_data"].empty else 1
            fig2_h = max(2.4, n_cats * 0.38)
            fig2 = Figure(figsize=(4.5, fig2_h), facecolor=CARD, dpi=96)
            # Margen izquierdo proporcional al largo de la etiqueta más larga
            max_lbl = max((len(str(lb)) for lb in k["cat_data"].index), default=8)
            left_margin = min(0.55, max(0.30, max_lbl * 0.022))
            fig2.subplots_adjust(left=left_margin, right=0.97, top=0.97, bottom=0.05)
            ax2 = fig2.add_subplot(111)
            if not cat.empty:
                cols2 = [CC[i%len(CC)] for i in range(len(cat))]
                bars  = ax2.barh(cat.index.tolist(), cat.values, color=cols2, height=0.55)
                for bar, val in zip(bars, cat.values):
                    ax2.text(bar.get_width()+max(cat.values)*0.01,
                             bar.get_y()+bar.get_height()/2,
                             f"${val/1000:.1f}k", va="center", fontsize=7, color=TEXT2)
                ax2.xaxis.set_visible(False)
                ax2.tick_params(axis="y", labelsize=8, colors=TEXT)
            ax2.set_facecolor(CARD)
            for sp in ax2.spines.values(): sp.set_visible(False)
            cv2 = FigureCanvasTkAgg(fig2, master=cc); cv2.draw()
            cv2.get_tk_widget().pack(fill="both", padx=4, pady=(0,10))

            pc2 = _card(f3); pc2.pack(side="left", fill="both", expand=True)
            tk.Frame(pc2, bg=PURPLE, height=4).pack(fill="x")
            tk.Label(pc2, text="Top 5 Productos — PMVU",
                     font=("Segoe UI",11,"bold"), bg=CARD, fg=TEXT,
                     padx=18, pady=12).pack(anchor="w")
            p5   = k["prod5"]
            fig3 = Figure(figsize=(4.5, 2.4), facecolor=CARD, dpi=96)
            fig3.subplots_adjust(left=0.02, right=0.98, top=0.95, bottom=0.05)
            ax3 = fig3.add_subplot(111)
            if not p5.empty:
                pc3 = [CC[i%len(CC)] for i in range(len(p5))]
                _, _, at = ax3.pie(
                    p5.values, labels=[str(p)[:14] for p in p5.index],
                    colors=pc3, autopct="%1.0f%%", startangle=90,
                    wedgeprops={"width":0.55,"edgecolor":CARD,"linewidth":2},
                    textprops={"fontsize":7,"color":TEXT})
                for a in at: a.set_fontsize(7); a.set_color(WHITE)
            ax3.set_facecolor(CARD)
            cv3 = FigureCanvasTkAgg(fig3, master=pc2); cv3.draw()
            cv3.get_tk_widget().pack(fill="both", padx=4, pady=(0,10))

    # ──────────────────────────────────────────────────────────────────────────
    def _render_no_data(self, parent):
        c = tk.Frame(parent, bg=BG); c.pack(expand=True, fill="both")
        inn = tk.Frame(c, bg=CARD, highlightthickness=1, highlightbackground=BORDER,
                       padx=60, pady=50)
        inn.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(inn, text="🗄️", font=("Segoe UI",48), bg=CARD).pack()
        tk.Label(inn, text="Sin datos en MongoDB",
                 font=("Segoe UI",16,"bold"), bg=CARD, fg=TEXT).pack(pady=(10,4))
        tk.Label(inn,
                 text="La base de datos está vacía o MongoDB no está conectado.\n"
                      "Ejecuta 'inicializar_bd.bat' para cargar datos de ejemplo.",
                 font=("Segoe UI",10), bg=CARD, fg=TEXT2, justify="center").pack()
        tk.Frame(inn, bg=BORDER, height=1).pack(fill="x", pady=20)
        _btn(inn, "↻  Reintentar", lambda: self._show_page("dashboard"), bg=ACCENT).pack()

    # ══════════════════════════════════════════════════════════════════════════
    # PÁGINA: KPIs DETALLADOS — LOS 12 SEGÚN EL PDF
    # ══════════════════════════════════════════════════════════════════════════
    def _page_kpis(self):
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import matplotlib.ticker as mticker
            HAS_MPL = True
        except ImportError:
            HAS_MPL = False

        # Barra de herramientas FUERA del scroll
        tb = tk.Frame(self.page_frame, bg=BG, pady=10)
        tb.pack(fill="x", padx=20)
        _btn(tb, "↻  Actualizar", lambda: self._show_page("kpis"),
             bg=ACCENT, size=9, px=14, py=6).pack(side="right")

        k = self._calcular_kpis()
        if k is None:
            self._render_no_data(self.page_frame); return

        # Contenedor scrollable que ocupa todo el espacio restante
        scroll_wrap = tk.Frame(self.page_frame, bg=BG)
        scroll_wrap.pack(fill="both", expand=True)
        _, inn = _scroll_frame(scroll_wrap)
        pad = 16

        # Definición completa de los 12 KPIs según el documento oficial
        kpi_defs = [
            # (num, sigla, nombre_completo, valor, estado_texto, ok, color,
            #  formula, variables, calculo_detalle, descripcion)
            (1, "TSC", "Tasa de Satisfacción del Cliente",
             f"{k['tsc']}%" if k['tsc'] is not None else "Sin datos",
             "Meta > 70%", k['tsc'] is not None and k['tsc'] >= 70,
             GREEN,
             "TSC = (Calif. ≥ 4 / Total) × 100",
             f"Positivas (≥4): {k['cp']}  |  Negativas (≤2): {k['cn']}  |  Total: {k['tc']}",
             f"Fuente: {k['fuente_com']}" + (f"  |  Promedio: {k['cal_prom']}/5" if k['cal_prom'] else ""),
             "Mide la satisfacción real usando calificaciones 1-5 de los clientes."),

            (2, "PVC", "Proyección de Ventas por Día",
             f"${k['pvc']:,.2f}",
             f"Rentable: {k['dp']} días", True,
             BLUE,
             "PVC = PMC + IE + Días Especiales",
             f"PMC = ${k['pmc']:,.2f}  |  Ajuste días especiales = ${k['dias_adj']:,.2f}",
             f"Promedio mensual + ajuste 5% festivos",
             "Proyección del ingreso diario ajustado por eventos extraordinarios."),

            (3, "TCL", "Tendencia de Categoría Líder",
             f"{k['tcl']}%",
             f"Categoría: {k['top_cat']}", True,
             ACCENT,
             "TCL = (VC / VT) × 100",
             f"VC = Ventas de {k['top_cat']}  |  VT = Ventas totales del periodo",
             f"${k['it']*k['tcl']/100:,.0f} / ${k['it']:,.0f} × 100",
             "Identifica la categoría que más aporta a las ventas totales."),

            (4, "RDI", "Ratio de Rotación de Insumos",
             f"{k['rdi']:.2f} kg/día",
             "Buen Consumo: > 12 kg/día", k['rdi'] >= 12,
             "#2E86AB",
             "RDI = Total Insumo / DP",
             f"Total harina: {k['total_harina']:,.1f} kg  |  DP = {k['dp']} días",
             f"{k['total_harina']:,.1f} / {k['dp']} días",
             "Mide el promedio de harina consumida por día de operación."),

            (5, "TVFS", "Tasa de Variación en Fin de Semana",
             f"{k['tvfs']:+.1f}%",
             "Crecimiento ≥ 0%", k['tvfs_ok'],
             PURPLE,
             "TVFS = ((VFS − VFS_ant) / VFS_ant) × 100",
             f"VFS actual = ${k['vfs_act']:,.0f}  |  VFS anterior = ${k['vfs_ant']:,.0f}",
             f"(${k['vfs_act']:,.0f} − ${k['vfs_ant']:,.0f}) / ${k['vfs_ant']:,.0f} × 100",
             "Mide el crecimiento o caída de ventas entre fines de semana consecutivos."),

            (6, "VVC", "Variación de Ventas por Categoría",
             f"${k['rac']:,.2f}",
             "RAC > $0 = rentable", k['vvc_ok'],
             GOLD,
             "RAC = CVFS_día − PV_día − EV_día",
             f"CVFS_día = ${k['cvfs_dia']:,.2f}  |  PV_día = ${k['pv_dia']:,.2f}  |  EV_día = ${k['ev_dia']:,.2f}",
             f"${k['cvfs_dia']:,.2f} − ${k['pv_dia']:,.2f} − ${k['ev_dia']:,.2f}",
             "Evalúa la rentabilidad por categoría en fines de semana."),

            (7, "PMVU", "Producto Más Vendido por Unidades",
             k['pnom'],
             f"{k['pcan']:,} unidades vendidas", True,
             "#5B4A8A",
             "PMVU = MAX( SUPL(art.Lote) )",
             "Unidades = unidades vendidas por producto por periodo",
             f"MAX de {k['np']} productos distintos",
             f"Resultado: {k['pnom']} con {k['pcan']:,} unidades vendidas."),

            (8, "IPT", "Ingreso Promedio por Transacción",
             f"${k['ipt']:,.2f}",
             f"{k['nt']:,} transacciones registradas", True,
             TEAL,
             "IPT = IT / AT",
             f"IT = Ingresos totales: ${k['it']:,.0f}  |  AT = {k['nt']:,} transacciones",
             f"${k['it']:,.0f} / {k['nt']:,}",
             "Mide el ticket promedio por cada venta realizada."),

            (9, "TCD", "Tasa de Calidad de Datos",
             f"{k['tcd']}%",
             "Meta ≥ 95%", k['tcd'] >= 95,
             GREEN,
             "TCD = (RC / TR) × 100",
             f"RC = Registros correctos: {k['rc']:,}  |  TR = Total registros: {k['tr']:,}",
             f"{k['rc']:,} / {k['tr']:,} × 100",
             "Mide consistencia y limpieza de datos almacenados en MongoDB."),

            (10, "IEP", "Índice de Estacionalidad del Producto",
             f"{k['iep']:.2f} ×",
             "IEP > 1 = superior al promedio", k['iep'] >= 1,
             BROWN,
             "IEP = VS_Mes / IM",
             f"VS_Mes = ventas mes del producto estrella  |  IM = promedio mensual",
             f"Producto estrella: {k['pe'] or 'N/A'}",
             "Ratio que expresa cuánto supera el promedio mensual de ventas."),

            (11, "SNP", "Sentimiento Negativo por Periodo",
             f"{k['snp']}%" if k['snp'] is not None else "Sin datos",
             "Alerta crítica si > 20%",
             k['snp'] is not None and k['snp'] <= 20,
             RED,
             "SNP = (TN / TC) × 100",
             f"TN = Comentarios negativos: {k['cn']}  |  TC = Total: {k['tc']}",
             f"{k['cn']} / {k['tc']} × 100  [{k['fuente_com']}]",
             "Mide cuántas quejas de clientes superan el umbral crítico."),

            (12, "CIB", "Costo de Uso de Insumos",
             f"${k['cib']:,.2f} / kg",
             "Mayor valor = mayor eficiencia", True,
             OLIVE,
             "CIB = IT / TC",
             f"IT = Ingresos totales: ${k['it']:,.0f}  |  TC = {k['tic']:,.0f} kg insumos",
             f"${k['it']:,.0f} / {k['tic']:,.0f} kg",
             "Mide el ingreso generado por cada kg de harina utilizado."),
        ]

        # Renderizar tarjetas en filas de 2 usando grid para ancho correcto
        for i in range(0, len(kpi_defs), 2):
            row_f = tk.Frame(inn, bg=BG)
            row_f.pack(fill="x", padx=pad, pady=(pad if i==0 else 0, 8))
            row_f.columnconfigure(0, weight=1, uniform="kpi_col")
            row_f.columnconfigure(1, weight=1, uniform="kpi_col")
            for col_idx, kpi in enumerate(kpi_defs[i:i+2]):
                num, sig, nom, val, meta, ok, col, form, vars_, calc, desc = kpi
                c = _card(row_f)
                c.grid(row=0, column=col_idx, sticky="nsew",
                       padx=(0, 10) if col_idx == 0 else (0, 0), pady=0)

                # Header de color con número, sigla y badge
                hc = tk.Frame(c, bg=col, padx=16, pady=10); hc.pack(fill="x")
                hr = tk.Frame(hc, bg=col); hr.pack(fill="x")
                tk.Label(hr, text=f"KPI {num}  ·  {sig}",
                         font=("Segoe UI",9,"bold"), bg=col, fg=WHITE).pack(side="left")
                bb = "#1A5A35" if ok else "#8B1A1A"
                tk.Label(hr, text=f"  {'✓  OK' if ok else '⚠  REVISAR'}  ",
                         font=("Segoe UI",8,"bold"),
                         bg=bb, fg=WHITE, pady=2).pack(side="right")
                tk.Label(hc, text=nom, font=("Segoe UI",11,"bold"),
                         bg=col, fg=WHITE, anchor="w").pack(fill="x", pady=(4,0))

                # Cuerpo
                body = tk.Frame(c, bg=CARD, padx=16, pady=12)
                body.pack(fill="both", expand=True)

                # Valor grande + meta
                vr = tk.Frame(body, bg=CARD); vr.pack(fill="x", pady=(0,6))
                tk.Label(vr, text=val, font=("Segoe UI",22,"bold"),
                         bg=CARD, fg=col).pack(side="left")
                tk.Label(vr, text=f"  {meta}", font=("Segoe UI",8),
                         bg=CARD, fg=TEXT_LIGHT).pack(side="left", anchor="s", pady=(0,3))

                # Descripción
                tk.Label(body, text=desc, font=("Segoe UI",8),
                         bg=CARD, fg=TEXT2, anchor="w",
                         wraplength=420, justify="left").pack(fill="x", pady=(0,6))

                # Fórmula
                tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(0,6))
                fb = tk.Frame(body, bg="#F5F0EB",
                              highlightthickness=1, highlightbackground=BORDER)
                fb.pack(fill="x")
                tk.Label(fb, text=form, font=("Consolas",9,"bold"),
                         bg="#F5F0EB", fg=col, padx=10, pady=5, anchor="w").pack(fill="x")
                tk.Label(fb, text=vars_, font=("Segoe UI",8),
                         bg="#F5F0EB", fg=TEXT2, padx=10, pady=3, anchor="w").pack(fill="x")
                tk.Label(body, text=f"Cálculo:  {calc}", font=("Segoe UI",8),
                         bg=CARD, fg=TEXT_LIGHT, padx=2, anchor="w").pack(fill="x", pady=(5,0))

        # Gráfico comparativo final: barras por categoría
        if HAS_MPL:
            cr = tk.Frame(inn, bg=BG); cr.pack(fill="x", padx=pad, pady=(0,pad))
            ccc = _card(cr); ccc.pack(fill="both", expand=True)
            tk.Frame(ccc, bg=GOLD, height=4).pack(fill="x")
            hrow = tk.Frame(ccc, bg=CARD, padx=16, pady=10); hrow.pack(fill="x")
            tk.Label(hrow, text="Comparativo Ventas por Categoría  —  KPI TCL",
                     font=("Segoe UI",11,"bold"), bg=CARD, fg=TEXT).pack(side="left")
            tk.Label(hrow, text=f"Categoría líder: {k['top_cat']}  ({k['tcl']}%)",
                     font=("Segoe UI",9), bg=CARD, fg=TEXT2).pack(side="right")
            cat = k["cat_data"]
            fc  = Figure(figsize=(10, 2.4), facecolor=CARD, dpi=96)
            fc.subplots_adjust(left=0.04, right=0.98, top=0.88, bottom=0.18)
            ac  = fc.add_subplot(111)
            if not cat.empty:
                xp  = range(len(cat))
                cls = [CC[i%len(CC)] for i in range(len(cat))]
                bs  = ac.bar(xp, cat.values, color=cls, width=0.55)
                ac.set_xticks(list(xp))
                ac.set_xticklabels(cat.index.tolist(), fontsize=8, color=TEXT)
                ac.yaxis.set_major_formatter(
                    mticker.FuncFormatter(lambda v,_: f"${v/1000:.0f}k"))
                ac.tick_params(axis="y", labelsize=7, colors=TEXT2)
                for b, v in zip(bs, cat.values):
                    ac.text(b.get_x()+b.get_width()/2,
                            b.get_height()+max(cat.values)*0.01,
                            f"${v/1000:.1f}k", ha="center", fontsize=7, color=TEXT2)
            ac.set_facecolor(CARD)
            for sp in ac.spines.values(): sp.set_visible(False)
            ac.yaxis.grid(True, color=BORDER, linewidth=0.6, alpha=0.8)
            ac.set_axisbelow(True)
            cvc = FigureCanvasTkAgg(fc, master=ccc); cvc.draw()
            cvc.get_tk_widget().pack(fill="x", padx=8, pady=(0,12))

    # ══════════════════════════════════════════════════════════════════════════
    # PÁGINA: DATOS
    # ══════════════════════════════════════════════════════════════════════════
    def _page_datos(self):
        tb = tk.Frame(self.page_frame, bg=BG, pady=12); tb.pack(fill="x", padx=20)
        for label, cmd, color in [
            ("🗄️  Base de Datos", self._importar_bd,   ACCENT),
            ("📊  Excel",          self._importar_excel, ACCENT),
            ("🔗  URL / CSV",      self._importar_url,   BLUE),
            ("💾  Guardar Mongo",  self._guardar_mongo,  GREEN),
        ]:
            _btn(tb, label, cmd, bg=color, size=9, px=12, py=7).pack(side="left", padx=(0,8))

        sf = tk.Frame(tb, bg=BG); sf.pack(side="right")
        tk.Label(sf, text="Buscar:", font=("Segoe UI",9), fg=TEXT2, bg=BG
                 ).pack(side="left", padx=(0,6))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._filtrar_tabla)
        tk.Entry(sf, textvariable=self.search_var, bg=WHITE, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=("Segoe UI",10),
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT, width=24).pack(side="left", ipady=5)

        self.lbl_data_info = tk.Label(
            self.page_frame,
            text="Sin datos cargados — usa uno de los botones para importar",
            font=("Segoe UI",9), fg=TEXT2, bg=BG)
        self.lbl_data_info.pack(anchor="w", padx=22, pady=(0,6))

        tf = tk.Frame(self.page_frame, bg=WHITE,
                      highlightthickness=1, highlightbackground=BORDER)
        tf.pack(fill="both", expand=True, padx=20, pady=(0,14))
        self.tree = ttk.Treeview(tf, style="App.Treeview",
                                 show="headings", selectmode="browse")
        vsb = ttk.Scrollbar(tf, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tf.rowconfigure(0, weight=1); tf.columnconfigure(0, weight=1)
        if self.df is not None and not self.df.empty:
            self._llenar_tabla(self.df)

    # ══════════════════════════════════════════════════════════════════════════
    # PÁGINA: COMENTARIOS
    # ══════════════════════════════════════════════════════════════════════════
    def _page_comentarios(self):
        txts = []; califs_raw = []; extra_cols = {}
        if self.db.is_connected:
            try:
                df_c = self.db.read_table("Comentarios")
                if not df_c.empty:
                    # columna de texto (excluye _id)
                    col_c = next((c for c in df_c.columns
                                  if (any(k in c.lower() for k in
                                         ["comentario","texto","comment","resena","opinion"])
                                      and not c.lower().endswith("_id"))), None)
                    # columna de calificación
                    col_cal = next((c for c in df_c.columns
                                    if any(k in c.lower() for k in
                                           ["calificacion","calificación","rating",
                                            "puntuacion","score","stars"])), None)
                    # columnas extra de interés (plataforma, producto)
                    for campo in ["plataforma","producto_mencionado","fecha"]:
                        match = next((c for c in df_c.columns if campo in c.lower()), None)
                        if match:
                            extra_cols[campo] = match

                    if col_c:
                        txts = df_c[col_c].fillna("").astype(str).tolist()
                    if col_cal:
                        califs_raw = pd.to_numeric(
                            df_c[col_cal], errors="coerce").fillna(0).astype(int).tolist()
            except Exception:
                pass

        if not txts and not califs_raw:
            c = tk.Frame(self.page_frame, bg=BG); c.pack(expand=True, fill="both")
            inn = tk.Frame(c, bg=CARD, highlightthickness=1, highlightbackground=BORDER,
                           padx=60, pady=50)
            inn.place(relx=0.5, rely=0.5, anchor="center")
            tk.Label(inn, text="💬", font=("Segoe UI",48), bg=CARD).pack()
            tk.Label(inn, text="Sin colección de Comentarios",
                     font=("Segoe UI",14,"bold"), bg=CARD, fg=TEXT).pack(pady=(10,4))
            tk.Label(inn,
                     text="Crea una colección 'Comentarios' en MongoDB\n"
                          "con campos 'comentario' y/o 'calificacion'.",
                     font=("Segoe UI",10), bg=CARD, fg=TEXT2, justify="center").pack()
            return

        n = max(len(txts), len(califs_raw))
        base = datetime.now()
        rows = []
        for i in range(n):
            com  = txts[i] if i < len(txts) else ""
            cal  = califs_raw[i] if i < len(califs_raw) else None
            # sentimiento basado primero en calificación, luego en texto
            if cal is not None and cal > 0:
                sent = "Positivo" if cal >= 4 else ("Negativo" if cal <= 2 else "Neutro")
            else:
                sent = ("Positivo" if any(p in com.lower() for p in PALABRAS_POSITIVAS)
                        else ("Negativo" if any(p in com.lower() for p in PALABRAS_NEGATIVAS)
                              else "Neutro"))
            row = {"#": i+1, "Comentario": com}
            if cal is not None:
                row["Calificación"] = f"{cal}/5" if cal > 0 else ""
            row["Fecha"] = (base - timedelta(
                days=random.randint(1,90),
                hours=random.randint(8,21),
                minutes=random.randint(0,59))).strftime("%Y-%m-%d %H:%M")
            row["Sentimiento"] = sent
            rows.append(row)

        self._cargar_df(pd.DataFrame(rows), "Comentarios MongoDB")
        self._show_page("datos")

    # ══════════════════════════════════════════════════════════════════════════
    # PÁGINA: CLIMA
    # ══════════════════════════════════════════════════════════════════════════
    def _page_clima(self):
        outer = tk.Frame(self.page_frame, bg=BG, padx=20, pady=20)
        outer.pack(fill="both", expand=True)
        c = _card(outer); c.pack(fill="x")
        tk.Frame(c, bg="#2E86AB", height=4).pack(fill="x")
        body = tk.Frame(c, bg=CARD, padx=24, pady=20); body.pack(fill="x")
        tk.Label(body, text="Consulta de Clima en Tiempo Real",
                 font=("Segoe UI",13,"bold"), bg=CARD, fg=TEXT).pack(anchor="w")
        tk.Label(body,
                 text="El clima influye en la demanda de pan. "
                      "Días lluviosos o fríos aumentan ventas de pan dulce y café.",
                 font=("Segoe UI",9), bg=CARD, fg=TEXT2).pack(anchor="w", pady=(4,16))
        def fila(lbl, val="", ancho=28):
            r = tk.Frame(body, bg=CARD); r.pack(fill="x", pady=4)
            tk.Label(r, text=lbl, font=("Segoe UI",10),
                     fg=TEXT2, bg=CARD, width=10, anchor="w").pack(side="left")
            v = tk.StringVar(value=val)
            tk.Entry(r, textvariable=v, bg=BG, fg=TEXT, relief="flat",
                     font=("Segoe UI",10), highlightthickness=1,
                     highlightbackground=BORDER, highlightcolor=ACCENT,
                     width=ancho).pack(side="left", ipady=6)
            return v
        ciudad_var = fila("Ciudad:", "Oaxaca,MX")
        api_var    = fila("API Key:", "", ancho=36)
        tk.Label(body, text="Clave gratuita en openweathermap.org/api (puede tardar 2h)",
                 font=("Segoe UI",8), fg=TEXT_LIGHT, bg=CARD).pack(anchor="w", pady=(4,12))
        lbl_err = tk.Label(body, text="", font=("Segoe UI",9), fg=RED, bg=CARD)
        lbl_err.pack(anchor="w")
        def real():
            ciudad = ciudad_var.get().strip(); key = api_var.get().strip()
            if not ciudad: lbl_err.config(text="Escribe una ciudad."); return
            if not key:    lbl_err.config(text="Escribe tu API Key o usa Demo."); return
            lbl_err.config(text="Consultando...", fg=TEXT2); outer.update()
            try:
                def fetch(u):
                    with urllib.request.urlopen(u, timeout=8) as r: return json.loads(r.read())
                d = fetch(f"https://api.openweathermap.org/data/2.5/weather"
                          f"?q={urllib.parse.quote(ciudad)}&appid={key}&units=metric&lang=es")
                f = fetch(f"https://api.openweathermap.org/data/2.5/forecast"
                          f"?q={urllib.parse.quote(ciudad)}&appid={key}&units=metric&lang=es&cnt=40")
                rows = [{"Momento":"Ahora","Ciudad":d["name"],
                         "Temperatura C":round(d["main"]["temp"],1),
                         "Sensacion C":round(d["main"]["feels_like"],1),
                         "Humedad %":d["main"]["humidity"],
                         "Condicion":d["weather"][0]["description"].capitalize(),
                         "Lluvia mm":d.get("rain",{}).get("1h",0.0),
                         "Viento km/h":round(d["wind"]["speed"]*3.6,1),
                         "Presion hPa":d["main"]["pressure"]}]
                for it in f["list"]:
                    rows.append({"Momento":it["dt_txt"],"Ciudad":d["name"],
                                 "Temperatura C":round(it["main"]["temp"],1),
                                 "Sensacion C":round(it["main"]["feels_like"],1),
                                 "Humedad %":it["main"]["humidity"],
                                 "Condicion":it["weather"][0]["description"].capitalize(),
                                 "Lluvia mm":it.get("rain",{}).get("3h",0.0),
                                 "Viento km/h":round(it["wind"]["speed"]*3.6,1),
                                 "Presion hPa":it["main"]["pressure"]})
                self._cargar_df(pd.DataFrame(rows), f"Clima: {d['name']}")
                self._show_page("datos")
            except Exception as e:
                lbl_err.config(fg=RED,
                    text=("API Key inválida o no activada. Usa Demo."
                          if "401" in str(e) else f"Error: {e}"))
        def demo():
            ciudad = ciudad_var.get().strip() or "Oaxaca"
            self._cargar_df(_clima_demo(ciudad), f"Clima demo: {ciudad}")
            self._show_page("datos")
        br = tk.Frame(body, bg=CARD); br.pack(fill="x", pady=(8,0))
        _btn(br, "🌐  Consultar clima real", real,  bg="#2E86AB", px=16, py=8).pack(side="left", padx=(0,10))
        _btn(br, "🎲  Usar datos demo",      demo,  bg=TEXT2,     px=16, py=8).pack(side="left")

    # ══════════════════════════════════════════════════════════════════════════
    # ACCIONES DE DATOS
    # ══════════════════════════════════════════════════════════════════════════
    def _importar_bd(self):
        if not self.db.is_connected:
            try: self.db.connect()
            except Exception as e:
                messagebox.showerror("Error MongoDB","No se pudo conectar.\n"+str(e)); return
        tablas = [t for t in self.db.list_tables() if t != "Dim_Clima"]
        if not tablas:
            messagebox.showerror("BD vacía",
                "MongoDB conectado pero sin colecciones.\nEjecuta 'inicializar_bd.bat'."); return
        self._dialogo_lista("Seleccionar colección", tablas,
            lambda t: (self._cargar_df(self.db.read_table(t), f"BD: {t}"),
                       self._show_page("datos")),
            info_fn=lambda t: f"{self.db.table_row_count(t):,} docs")

    def _importar_excel(self):
        path = filedialog.askopenfilename(
            title="Abrir Excel", filetypes=[("Excel","*.xlsx *.xls *.xlsm"),("All","*.*")])
        if not path: return
        try:
            sheets = pd.read_excel(path, sheet_name=None); nombres = list(sheets.keys())
            if len(nombres)==1:
                self._cargar_df(sheets[nombres[0]], f"Excel: {nombres[0]}")
                self._show_page("datos")
            else:
                self._dialogo_lista("Seleccionar hoja", nombres,
                    lambda n: (self._cargar_df(sheets[n], f"Excel: {n}"),
                               self._show_page("datos")))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir:\n{e}")

    def _importar_url(self):
        win = self._form("Importar desde URL", 500, 220)
        tk.Label(win, text="URL del archivo CSV:", font=("Segoe UI",11,"bold"),
                 fg=TEXT, bg=BG).pack(pady=(20,4), padx=24, anchor="w")
        tk.Label(win, text="Ejemplo: https://datos.gob.mx/archivo.csv",
                 font=("Segoe UI",9), fg=TEXT2, bg=BG).pack(padx=24, anchor="w")
        url_v = tk.StringVar()
        tk.Entry(win, textvariable=url_v, bg=WHITE, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=("Segoe UI",10),
                 highlightthickness=1, highlightbackground=BORDER
                 ).pack(fill="x", padx=24, pady=(10,4), ipady=6)
        lbl = tk.Label(win, text="", font=("Segoe UI",9), fg=RED, bg=BG); lbl.pack(padx=24, anchor="w")
        def cargar():
            url = url_v.get().strip()
            if not url: lbl.config(text="Escribe una URL."); return
            try:
                lbl.config(text="Descargando...", fg=TEXT2); win.update()
                df = pd.read_csv(url); win.destroy()
                self._cargar_df(df, f"URL: {url.split('/')[-1]}")
                self._show_page("datos")
            except Exception as e: lbl.config(text=f"Error: {e}", fg=RED)
        _btn(win,"Cargar datos",cargar,bg=BLUE,px=20,py=8).pack(fill="x",padx=24,pady=(8,16))

    def _guardar_mongo(self):
        if self.df is None or self.df.empty:
            messagebox.showinfo("Sin datos","Primero carga datos."); return
        if not self.db.is_connected:
            try: self.db.connect()
            except Exception as e: messagebox.showerror("Error",str(e)); return
        win = self._form("Guardar en MongoDB", 460, 350)
        tk.Label(win, text="Guardar en MongoDB", font=("Segoe UI",13,"bold"),
                 bg="#13AA52", fg=WHITE, pady=12).pack(fill="x")
        form = tk.Frame(win, bg=BG); form.pack(fill="x", padx=24, pady=16)
        def campo(lbl, val=""):
            tk.Label(form, text=lbl, font=("Segoe UI",10),
                     fg=TEXT2, bg=BG, anchor="w").pack(fill="x", pady=(6,2))
            v = tk.StringVar(value=val)
            tk.Entry(form, textvariable=v, bg=WHITE, fg=TEXT, relief="flat",
                     font=("Segoe UI",10), highlightthickness=1,
                     highlightbackground=BORDER).pack(fill="x", ipady=5)
            return v
        db_v  = campo("Base de datos:", "panaderia")
        col_v = campo("Colección:", "Nueva_Coleccion")
        tk.Label(form, text="Si ya existe:", font=("Segoe UI",10),
                 fg=TEXT2, bg=BG, anchor="w").pack(fill="x", pady=(6,2))
        modo_v = tk.StringVar(value="Reemplazar")
        ttk.Combobox(form, textvariable=modo_v, state="readonly",
                     values=["Reemplazar","Agregar"],
                     font=("Segoe UI",10)).pack(fill="x", ipady=3)
        tk.Label(win, text=f"Filas a guardar: {len(self.df):,}",
                 font=("Segoe UI",10,"bold"), fg="#13AA52", bg=BG).pack(anchor="w", padx=24)
        def guardar():
            db_n=db_v.get().strip(); col_n=col_v.get().strip()
            if not db_n or not col_n:
                messagebox.showwarning("Incompleto","Llena todos los campos."); return
            try:
                self.db.connect(db_name=db_n)
                n = self.db.import_dataframe(self.df, col_n,
                    if_exists="replace" if modo_v.get()=="Reemplazar" else "append")
                win.destroy()
                messagebox.showinfo("Guardado", f"{n:,} registros guardados en {db_n}/{col_n}")
            except Exception as e: messagebox.showerror("Error",str(e))
        _btn(win,"💾  Guardar",guardar,bg="#13AA52",px=20,py=9).pack(fill="x",padx=24,pady=(8,16))

    # ──────────────────────────────────────────────────────────────────────────
    def _form(self, titulo, w, h):
        win = tk.Toplevel(self); win.title(titulo); win.configure(bg=BG)
        win.geometry(f"{w}x{h}"); win.resizable(False,False); win.grab_set()
        return win

    def _dialogo_lista(self, titulo, items, on_select, info_fn=None):
        win = self._form(titulo, 400, 420)
        tk.Label(win, text=titulo, font=("Segoe UI",12,"bold"),
                 fg=WHITE, bg=HDR_BG, pady=14).pack(fill="x")
        tk.Label(win, text="Selecciona una opción:", font=("Segoe UI",10),
                 fg=TEXT2, bg=BG).pack(pady=(14,4), padx=20, anchor="w")
        lb_f = tk.Frame(win, bg=WHITE, highlightthickness=1, highlightbackground=BORDER)
        lb_f.pack(fill="both", expand=True, padx=20)
        lb = tk.Listbox(lb_f, bg=WHITE, fg=TEXT, selectbackground=ACCENT,
                        selectforeground=WHITE, font=("Segoe UI",11), relief="flat",
                        borderwidth=0, activestyle="none", highlightthickness=0, cursor="hand2")
        vsb2 = ttk.Scrollbar(lb_f, command=lb.yview)
        lb.configure(yscrollcommand=vsb2.set)
        vsb2.pack(side="right", fill="y"); lb.pack(fill="both", expand=True)
        for it in items:
            lb.insert("end", f"  {it}{'  ('+info_fn(it)+')' if info_fn else ''}")
        lb.selection_set(0)
        def cargar():
            sel = lb.curselection()
            if not sel: return
            item = items[sel[0]]; win.destroy()
            try: on_select(item)
            except Exception as e: messagebox.showerror("Error",str(e))
        lb.bind("<Double-Button-1>", lambda e: cargar())
        _btn(win,"  Cargar  ",cargar,bg=ACCENT,px=20,py=9).pack(fill="x",padx=20,pady=(8,16))

    # ──────────────────────────────────────────────────────────────────────────
    def _limpiar_df(self, df):
        df = df.copy()
        df.drop_duplicates(inplace=True); df.dropna(how="all", inplace=True)
        df.reset_index(drop=True, inplace=True)
        ct = df.select_dtypes(include="object").columns
        df[ct] = df[ct].fillna("Sin datos")
        cn = df.select_dtypes(include="number").columns
        df[cn] = df[cn].fillna(0)
        for col in ct: df[col] = df[col].astype(str).str.strip()
        return df

    def _cargar_df(self, df, fuente=""):
        self.df = self._limpiar_df(df); self._df_fuente = fuente

    def _llenar_tabla(self, df):
        self.tree.delete(*self.tree.get_children())
        cols = list(df.columns.astype(str)); self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=c, command=lambda _c=c: self._ordenar(_c,False))
            self.tree.column(c, width=max(90,min(240,len(c)*11+24)), minwidth=60, anchor="w")
        for i,(_, row) in enumerate(df.iterrows()):
            self.tree.insert("","end", tags=("alt" if i%2 else "",),
                             values=[str(v) if pd.notna(v) else "" for v in row])
        self.tree.tag_configure("alt", background=ROW_ALT)
        self.lbl_data_info.config(
            text=f"{len(df):,} filas  ·  {len(cols)} columnas  ·  Fuente: {self._df_fuente}")

    def _filtrar_tabla(self, *_):
        if self.df is None: return
        q = self.search_var.get().lower()
        df = self.df if not q else self.df[
            self.df.apply(lambda c: c.astype(str).str.lower()
                          .str.contains(q,na=False)).any(axis=1)]
        self._llenar_tabla(df)

    def _ordenar(self, col, reverse):
        if self.df is None: return
        try:
            self.df.sort_values(col, ascending=not reverse, inplace=True, ignore_index=True)
            self._llenar_tabla(self.df)
            self.tree.heading(col, command=lambda: self._ordenar(col, not reverse))
        except Exception: pass

    def _autoconnect(self):
        try:
            self.db.connect()
            if self.db.is_panaderia_ready():
                n = self.db.table_row_count("Ventas")
                self.lbl_conn.config(
                    text=f"🟢  MongoDB conectado\n    {n:,} ventas cargadas", fg="#70E090")
            else:
                self.lbl_conn.config(
                    text="🟡  MongoDB conectado\n    Sin datos — ejecuta\n    inicializar_bd.bat",
                    fg="#E0C070")
        except Exception as e:
            self.lbl_conn.config(
                text=f"🔴  MongoDB no disponible\n    {str(e)[:60]}", fg="#E07070")


if __name__ == "__main__":
    app = App()
    app.mainloop()
