import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json
from datetime import datetime
import os

# Configuración de página
st.set_page_config(page_title="Rastreador Clash Royale", page_icon="🏆", layout="wide")

# Archivo para almacenar datos
DATA_FILE = "clash_royale_data.json"

# Inicializar session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

def load_data():
    """Cargar datos guardados del archivo JSON"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"players": {}, "history": []}

def save_data(data):
    """Guardar datos en archivo JSON"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def fetch_player_data(player_tag, api_key):
    """Obtener datos del jugador de la API de Clash Royale"""
    # Limpiar el tag
    clean_tag = player_tag.replace('#', '').strip()
    
    url = f"https://api.clashroyale.com/v1/players/%23{clean_tag}"
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")

# Título
st.title("🏆 Rastreador de Estadísticas Clash Royale")
st.markdown("¡Rastrea el progreso de trofeos de tus amigos a lo largo del tiempo!")

# Barra lateral para la API key
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input("Clave API", type="password", value=st.session_state.api_key)
    st.session_state.api_key = api_key
    
    st.markdown("---")
    st.markdown("### 📖 Cómo usar:")
    st.markdown("""
    1. Obtén tu clave API de [RoyaleAPI](https://developer.clashroyale.com)
    2. Ingresa los tags de jugadores abajo
    3. Añade jugadores para rastrear
    4. ¡Actualiza las estadísticas regularmente para ver el progreso!
    """)
    
    if st.button("🗑️ Borrar Todos los Datos"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.success("¡Datos borrados!")
        st.rerun()

# Cargar datos existentes
data = load_data()

# Sección añadir jugador
st.header("➕ Añadir Jugador")
col1, col2 = st.columns([3, 1])
with col1:
    player_tag = st.text_input("Tag del Jugador (ej., #ABC123 o ABC123)", key="player_tag_input")
with col2:
    st.write("")  # Espaciado
    st.write("")  # Espaciado
    add_button = st.button("Añadir Jugador", type="primary")

if add_button:
    if not api_key:
        st.error("¡Por favor ingresa tu clave API en la barra lateral!")
    elif not player_tag:
        st.error("¡Por favor ingresa un tag de jugador!")
    else:
        try:
            with st.spinner("Obteniendo datos del jugador..."):
                player_data = fetch_player_data(player_tag, api_key)
                
                player_tag_clean = player_data['tag']
                
                # Añadir al diccionario de jugadores si no existe
                if player_tag_clean not in data['players']:
                    data['players'][player_tag_clean] = {
                        'name': player_data['name'],
                        'tag': player_tag_clean
                    }
                
                # Añadir estadísticas actuales al historial
                data['history'].append({
                    'timestamp': datetime.now().isoformat(),
                    'tag': player_tag_clean,
                    'name': player_data['name'],
                    'trophies': player_data['trophies'],
                    'level': player_data['expLevel'],
                    'wins': player_data['wins'],
                    'losses': player_data['losses']
                })
                
                save_data(data)
                st.success(f"¡Añadido {player_data['name']} ({player_tag_clean})!")
                st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Sección actualizar todos los jugadores
if data['players']:
    st.header("🔄 Actualizar Estadísticas")
    if st.button("Actualizar Todos los Jugadores"):
        if not api_key:
            st.error("¡Por favor ingresa tu clave API en la barra lateral!")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_players = len(data['players'])
            for idx, (tag, player_info) in enumerate(data['players'].items()):
                try:
                    status_text.text(f"Actualizando {player_info['name']}...")
                    player_data = fetch_player_data(tag, api_key)
                    
                    # Añadir al historial
                    data['history'].append({
                        'timestamp': datetime.now().isoformat(),
                        'tag': player_data['tag'],
                        'name': player_data['name'],
                        'trophies': player_data['trophies'],
                        'level': player_data['expLevel'],
                        'wins': player_data['wins'],
                        'losses': player_data['losses']
                    })
                    
                    progress_bar.progress((idx + 1) / total_players)
                except Exception as e:
                    st.warning(f"Fallo al actualizar {player_info['name']}: {str(e)}")
            
            save_data(data)
            status_text.text("✅ ¡Todos los jugadores actualizados!")
            st.rerun()

# Mostrar jugadores actuales
if data['players']:
    st.header("👥 Jugadores Rastreados")
    
    # Obtener estadísticas más recientes de cada jugador
    latest_stats = {}
    for entry in reversed(data['history']):
        if entry['tag'] not in latest_stats:
            latest_stats[entry['tag']] = entry
    
    cols = st.columns(min(len(data['players']), 4))
    for idx, (tag, player_info) in enumerate(data['players'].items()):
        with cols[idx % 4]:
            stats = latest_stats.get(tag, {})
            st.metric(
                label=f"🏆 {player_info['name']}",
                value=f"{stats.get('trophies', 'N/A')} 🏆",
                delta=None
            )
            st.caption(f"Tag: {tag}")
            if stats:
                st.caption(f"Nivel {stats.get('level', 'N/A')} • {stats.get('wins', 0)}V/{stats.get('losses', 0)}D")
            
            if st.button(f"Eliminar", key=f"remove_{tag}"):
                del data['players'][tag]
                # Eliminar del historial también
                data['history'] = [h for h in data['history'] if h['tag'] != tag]
                save_data(data)
                st.rerun()

# Mostrar gráfica
if data['history']:
    st.header("📈 Progreso de Trofeos")
    
    # Convertir historial a DataFrame
    df = pd.DataFrame(data['history'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Crear gráfica de líneas
    fig = px.line(
        df, 
        x='timestamp', 
        y='trophies', 
        color='name',
        title='Progreso de Trofeos a lo Largo del Tiempo',
        labels={'timestamp': 'Fecha y Hora', 'trophies': 'Trofeos', 'name': 'Jugador'},
        markers=True
    )
    
    fig.update_layout(
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=900  # Graph is now much taller for better visibility
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar tabla de datos
    with st.expander("📊 Ver Datos en Crudo"):
        display_df = df[['timestamp', 'name', 'trophies', 'level', 'wins', 'losses']].copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        display_df.columns = ['Fecha y Hora', 'Jugador', 'Trofeos', 'Nivel', 'Victorias', 'Derrotas']
        st.dataframe(display_df, use_container_width=True)
else:
    st.info("👆 ¡Añade jugadores y actualiza sus estadísticas para ver la gráfica!")

# Pie de página
st.markdown("---")
st.caption("Hecho con ❤️ para rastrear estadísticas de Clash Royale con amigos")