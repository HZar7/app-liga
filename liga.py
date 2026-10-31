import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Gestor Liga Amigos", layout="wide")

# Conectar con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Equipos iniciales (Si creáis más, podéis añadirlos aquí)
EQUIPOS = ["Lote C.F", "Goteborg F.C", "Noterdant", "Goat F.C"]

# Cargar datos desde el Excel (sin caché para ver cambios al instante)
def cargar_hoja(nombre_hoja, columnas):
    try:
        df = conn.read(worksheet=nombre_hoja, ttl=0)
        df = df.dropna(how="all") # Limpia filas en blanco del excel
        return df
    except Exception as e:
        return pd.DataFrame(columns=columnas)

df_plantillas = cargar_hoja("Plantillas", ["Jugador", "Equipo", "Goles Reales"])
df_partidos = cargar_hoja("Partidos", ["Local", "Goles L", "Goles V", "Visitante"])
df_palmares = cargar_hoja("Palmares", ["Edicion", "Campeon", "Subcampeon"])

st.sidebar.title("Menú")
seccion = st.sidebar.radio("Secciones", ["Plantillas", "Goles en la Vida Real", "Torneos PES"])

# --- SECCIÓN: PLANTILLAS ---
if seccion == "Plantillas":
    st.header("Gestión de Plantillas")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Añadir Jugador")
        nuevo_jugador = st.text_input("Nombre del jugador real")
        equipo_destino = st.selectbox("Asignar a equipo", EQUIPOS)
        
        if st.button("Fichar"):
            if nuevo_jugador:
                nuevo_dato = pd.DataFrame([{"Jugador": nuevo_jugador, "Equipo": equipo_destino, "Goles Reales": 0}])
                df_actualizado = pd.concat([df_plantillas, nuevo_dato], ignore_index=True)
                # Guardar en Excel
                conn.update(worksheet="Plantillas", data=df_actualizado)
                st.success(f"{nuevo_jugador} fichado. Refrescando...")
                st.rerun()

    st.subheader("Plantillas Actuales")
    equipo_filtro = st.selectbox("Ver plantilla de:", EQUIPOS)
    if not df_plantillas.empty:
        plantilla = df_plantillas[df_plantillas["Equipo"] == equipo_filtro]
        st.dataframe(plantilla, use_container_width=True, hide_index=True)

# --- SECCIÓN: GOLES VIDA REAL ---
elif seccion == "Goles en la Vida Real":
    st.header("Estadísticas Reales")
    
    if not df_plantillas.empty:
        df_plantillas["Goles Reales"] = pd.to_numeric(df_plantillas["Goles Reales"], errors='coerce').fillna(0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Goles Totales por Equipo")
            goles_equipo = df_plantillas.groupby("Equipo")["Goles Reales"].sum().reset_index()
            st.dataframe(goles_equipo.sort_values(by="Goles Reales", ascending=False), use_container_width=True, hide_index=True)
            
        with col2:
            st.subheader("Pichichi Individual")
            st.dataframe(df_plantillas.sort_values(by="Goles Reales", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.warning("Aún no hay jugadores registrados.")

# --- SECCIÓN: TORNEOS PES ---
elif seccion == "Torneos PES":
    st.header("Gestor de Campeonatos PES")
    pestana_liguilla, pestana_finales, pestana_palmares = st.tabs(["Liguilla", "Fase Final", "Palmarés"])
    
    with pestana_liguilla:
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1: local = st.selectbox("Local", EQUIPOS, key="loc")
        with col2:
            goles_l = st.number_input("GL", 0, step=1)
            goles_v = st.number_input("GV", 0, step=1)
        with col3: visitante = st.selectbox("Visitante", EQUIPOS, key="vis")
            
        if st.button("Guardar Resultado"):
            if local != visitante:
                nuevo_partido = pd.DataFrame([{"Local": local, "Goles L": goles_l, "Goles V": goles_v, "Visitante": visitante}])
                df_actualizado = pd.concat([df_partidos, nuevo_partido], ignore_index=True)
                conn.update(worksheet="Partidos", data=df_actualizado)
                st.success("Partido registrado.")
                st.rerun()
            else:
                st.error("Un equipo no puede jugar contra sí mismo.")
                
        st.subheader("Resultados")
        st.dataframe(df_partidos, use_container_width=True, hide_index=True)

    with pestana_finales:
        edicion = st.text_input("Nombre de la edición (Ej: Torneo 2)")
        campeon = st.selectbox("Campeón", EQUIPOS, key="camp")
        subcampeon = st.selectbox("Subcampeón", EQUIPOS, key="subc")
        
        if st.button("Guardar en Palmarés"):
            if campeon != subcampeon and edicion:
                nuevo_titulo = pd.DataFrame([{"Edicion": edicion, "Campeon": campeon, "Subcampeon": subcampeon}])
                df_actualizado = pd.concat([df_palmares, nuevo_titulo], ignore_index=True)
                conn.update(worksheet="Palmares", data=df_actualizado)
                st.success("Palmarés actualizado.")
                st.rerun()

    with pestana_palmares:
        if not df_palmares.empty:
            st.dataframe(df_palmares, use_container_width=True, hide_index=True)