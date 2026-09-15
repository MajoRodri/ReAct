import streamlit as st
import httpx

API_URL = "http://localhost:8000"

URGENCY_CONFIG = {
    "baja":     {"color": "#22c55e", "bg": "#f0fdf4", "border": "#86efac", "label": "BAJA",     "icon": "●"},
    "media":    {"color": "#f59e0b", "bg": "#fffbeb", "border": "#fcd34d", "label": "MEDIA",    "icon": "●"},
    "alta":     {"color": "#f97316", "bg": "#fff7ed", "border": "#fdba74", "label": "ALTA",     "icon": "●"},
    "crítica":  {"color": "#ef4444", "bg": "#fef2f2", "border": "#fca5a5", "label": "CRÍTICA",  "icon": "▲"},
}

CATEGORY_ICONS = {
    "acoso":            ("🎯", "Acoso"),
    "violencia_fisica": ("⚡", "Violencia Física"),
    "agresion_verbal":  ("💬", "Agresión Verbal"),
    "exclusion_social": ("🚫", "Exclusión Social"),
    "sustancias":       ("⚗️",  "Sustancias"),
    "autolesion":       ("🆘", "Autolesión"),
    "otro":             ("📋", "Otro"),
}

DEPARTMENT_ICONS = {
    "tutoria":            ("👤", "Tutoría"),
    "orientacion":        ("🧠", "Orientación"),
    "direccion":          ("🏛️",  "Dirección"),
    "servicios_externos": ("🚨", "Servicios Externos"),
}

CSS = """
<style>
    /* fondo general */
    .stApp { background-color: #f8fafc; }

    /* oculta el menú de hamburguesa y el footer de streamlit */
    #MainMenu, footer { visibility: hidden; }

    /* header superior */
    .app-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
        border-radius: 16px;
        padding: 28px 36px;
        margin-bottom: 28px;
        color: white;
    }
    .app-header h1 { color: white; font-size: 2rem; margin: 0; font-weight: 700; }
    .app-header p  { color: #bfdbfe; margin: 6px 0 0; font-size: 0.95rem; }

    /* tarjeta de resultado */
    .result-card {
        border-radius: 14px;
        padding: 24px;
        margin: 16px 0;
        border-left: 6px solid;
    }
    .badge-urgency {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
    }
    .metric-box {
        background: white;
        border-radius: 10px;
        padding: 14px 18px;
        text-align: center;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-box .metric-icon { font-size: 1.5rem; }
    .metric-box .metric-label { font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; margin: 4px 0 2px; }
    .metric-box .metric-value { font-size: 1rem; font-weight: 600; color: #1e293b; }

    /* resumen */
    .summary-box {
        background: white;
        border-radius: 10px;
        padding: 16px 20px;
        border: 1px solid #e2e8f0;
        margin: 14px 0;
        font-style: italic;
        color: #374151;
    }

    /* razonamiento */
    .reasoning-box {
        background: #f1f5f9;
        border-radius: 10px;
        padding: 16px 20px;
        font-size: 0.9rem;
        color: #475569;
        line-height: 1.7;
        border-left: 3px solid #94a3b8;
        margin-top: 8px;
    }

    /* telemetría */
    .telemetry-row {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin-top: 14px;
    }
    .telemetry-chip {
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-radius: 999px;
        padding: 4px 12px;
        font-size: 0.78rem;
        color: #64748b;
        font-family: monospace;
    }

    /* botones de validación */
    .validation-section {
        background: white;
        border-radius: 14px;
        padding: 20px 24px;
        border: 1px solid #e2e8f0;
        margin-top: 20px;
    }
    .validation-section h4 { margin: 0 0 6px; color: #1e293b; }
    .validation-section p  { margin: 0 0 16px; color: #64748b; font-size: 0.9rem; }

    /* sidebar */
    [data-testid="stSidebar"] { background: #1e293b; }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] .stRadio label { color: #cbd5e1 !important; }
    [data-testid="stSidebar"] hr { border-color: #334155; }

    /* tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 500;
    }
</style>
"""


def call_api(endpoint: str, payload: dict):
    try:
        r = httpx.post(f"{API_URL}/{endpoint}", json=payload, timeout=120.0)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        st.error("⚠️ No hay conexión con el backend. Asegúrate de que está corriendo en el puerto 8000.")
        return None
    except Exception as e:
        st.error(f"Error inesperado: {e}")
        return None


def render_result_card(result: dict, title: str = ""):
    urgency   = result.get("urgency_level", "baja")
    cfg       = URGENCY_CONFIG.get(urgency, URGENCY_CONFIG["baja"])
    cat_key   = result.get("category", "otro")
    dept_key  = result.get("department", "tutoria")
    cat_icon,  cat_label  = CATEGORY_ICONS.get(cat_key,  ("📋", cat_key))
    dept_icon, dept_label = DEPARTMENT_ICONS.get(dept_key, ("👤", dept_key))

    card_html = f"""
    <div class="result-card" style="background:{cfg['bg']}; border-color:{cfg['color']};">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px;">
            <span style="font-weight:700; font-size:1.05rem; color:#1e293b;">{title}</span>
            <span class="badge-urgency" style="background:{cfg['color']}; color:white;">
                {cfg['icon']} {cfg['label']}
            </span>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; margin-bottom:16px;">
            <div class="metric-box">
                <div class="metric-icon">{cat_icon}</div>
                <div class="metric-label">Categoría</div>
                <div class="metric-value">{cat_label}</div>
            </div>
            <div class="metric-box">
                <div class="metric-icon" style="color:{cfg['color']};">●</div>
                <div class="metric-label">Urgencia</div>
                <div class="metric-value" style="color:{cfg['color']};">{urgency.capitalize()}</div>
            </div>
            <div class="metric-box">
                <div class="metric-icon">{dept_icon}</div>
                <div class="metric-label">Derivar a</div>
                <div class="metric-value">{dept_label}</div>
            </div>
        </div>
        <div class="summary-box">"{result.get('summary', '')}"</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    with st.expander("🧠 Razonamiento del modelo (Chain-of-Thought)"):
        st.markdown(
            f'<div class="reasoning-box">{result.get("reasoning", "")}</div>',
            unsafe_allow_html=True,
        )

    tokens   = result.get("tokens_used")
    cost     = result.get("estimated_cost_usd")
    latency  = result.get("latency_ms", 0)
    model    = result.get("model", "")
    provider = result.get("provider", "")

    chips = [
        f"⚙️ {provider} / {model}",
        f"⏱ {latency:.0f} ms",
    ]
    if tokens:
        chips.append(f"🔢 {tokens} tokens")
    if cost and cost > 0:
        chips.append(f"💲 ${cost:.5f} USD")

    chips_html = "".join(f'<span class="telemetry-chip">{c}</span>' for c in chips)
    st.markdown(f'<div class="telemetry-row">{chips_html}</div>', unsafe_allow_html=True)


def sidebar():
    with st.sidebar:
        st.markdown("## ⚙️ Configuración")
        st.markdown("---")
        provider = st.radio(
            "Proveedor de IA",
            options=["ollama", "groq"],
            format_func=lambda x: "🖥️  Ollama — Local" if x == "ollama" else "☁️  Groq — Nube",
        )
        st.markdown("---")
        st.markdown("**Estado del sistema**")
        try:
            r = httpx.get(f"{API_URL}/health", timeout=3)
            if r.status_code == 200:
                st.success("Backend activo")
            else:
                st.error("Backend con errores")
        except Exception:
            st.error("Backend no disponible")

        st.markdown("---")
        st.caption("Motor de Triaje Escolar v0.1")
    return provider


def page_triage(provider: str):
    st.markdown("### 📝 Reporte de Incidencia")
    st.caption("Introduce el texto del reporte y el sistema lo clasificará automáticamente.")

    report_text = st.text_area(
        label="Texto del reporte",
        height=160,
        placeholder="Ej: Un alumno ha estado siendo ignorado por sus compañeros durante semanas. Hoy ha llegado llorando y no quiere entrar a clase...",
        label_visibility="collapsed",
    )

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        analyze = st.button("🔍 Analizar", type="primary", use_container_width=True, disabled=not report_text.strip())
    with col_info:
        provider_label = "🖥️ Ollama (local)" if provider == "ollama" else "☁️ Groq (nube)"
        st.markdown(f"<div style='padding:8px 0; color:#64748b; font-size:0.9rem;'>Usando {provider_label}</div>", unsafe_allow_html=True)

    if analyze:
        with st.spinner("Analizando incidencia..."):
            data = call_api("triage", {"report_text": report_text, "provider": provider})

        if data and data.get("success"):
            st.markdown("---")
            render_result_card(data["data"], "Resultado del Triaje")

            st.markdown("""
            <div class="validation-section">
                <h4>👩‍💼 Validación humana</h4>
                <p>Revisa la clasificación y confirma antes de registrar la incidencia.</p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar y derivar", use_container_width=True, type="primary"):
                    st.success("Incidencia registrada y derivada correctamente.")
            with col2:
                if st.button("✏️ Marcar para revisión manual", use_container_width=True):
                    st.warning("Incidencia marcada para revisión del equipo directivo.")

        elif data:
            st.error(f"El modelo devolvió un error: {data.get('error')}")


def page_compare():
    st.markdown("### ⚖️ Comparativa de Modelos")
    st.caption("El mismo reporte se envía a Ollama y Groq simultáneamente para comparar resultados.")

    report_text = st.text_area(
        label="Texto del reporte",
        height=160,
        placeholder="Ej: Un grupo de alumnos lleva semanas ignorando a un compañero...",
        key="compare_input",
        label_visibility="collapsed",
    )

    if st.button("⚖️ Comparar modelos", type="primary", use_container_width=False, disabled=not report_text.strip()):
        with st.spinner("Consultando Ollama y Groq en paralelo..."):
            data = call_api("compare", {"report_text": report_text})

        if not data:
            return

        col_left, col_right = st.columns(2)
        with col_left:
            if data.get("ollama_result"):
                render_result_card(data["ollama_result"], "🖥️ Ollama — Local")
            else:
                st.error(f"Ollama falló: {data.get('ollama_error', 'Error desconocido')}")

        with col_right:
            if data.get("groq_result"):
                render_result_card(data["groq_result"], "☁️ Groq — Nube")
            else:
                st.error(f"Groq falló: {data.get('groq_error', 'Error desconocido')}")

        o = data.get("ollama_result")
        g = data.get("groq_result")
        if o and g:
            st.markdown("---")
            st.markdown("### 📊 Resumen comparativo")
            _, cat_o = CATEGORY_ICONS.get(o["category"],  ("", o["category"]))
            _, cat_g = CATEGORY_ICONS.get(g["category"],  ("", g["category"]))
            _, dep_o = DEPARTMENT_ICONS.get(o["department"], ("", o["department"]))
            _, dep_g = DEPARTMENT_ICONS.get(g["department"], ("", g["department"]))

            col_h, col_o, col_g = st.columns([2, 1, 1])
            rows = [
                ("Categoría",      cat_o,                          cat_g),
                ("Urgencia",       o["urgency_level"].capitalize(), g["urgency_level"].capitalize()),
                ("Departamento",   dep_o,                          dep_g),
                ("Latencia (ms)",  f"{o['latency_ms']:.0f}",       f"{g['latency_ms']:.0f}"),
                ("Tokens",         str(o.get("tokens_used") or "—"), str(g.get("tokens_used") or "—")),
            ]
            col_h.markdown("**Campo**")
            col_o.markdown("**Ollama**")
            col_g.markdown("**Groq**")
            for label, val_o, val_g in rows:
                col_h.markdown(label)
                col_o.markdown(f"`{val_o}`")
                col_g.markdown(f"`{val_g}`")
                col_h.markdown(""); col_o.markdown(""); col_g.markdown("")


def main():
    st.set_page_config(
        page_title="Motor de Triaje Escolar",
        page_icon="🏫",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="app-header">
        <h1>🏫 Motor de Triaje Escolar</h1>
        <p>Sistema inteligente de clasificación de incidencias de convivencia — Human-in-the-Loop</p>
    </div>
    """, unsafe_allow_html=True)

    provider = sidebar()

    tab1, tab2 = st.tabs(["📋 Analizar Incidencia", "⚖️ Comparar Modelos"])
    with tab1:
        page_triage(provider)
    with tab2:
        page_compare()


if __name__ == "__main__":
    main()
