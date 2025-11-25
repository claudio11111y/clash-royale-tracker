import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json
from datetime import datetime, timedelta
import os

# Configuración de página
st.set_page_config(page_title="Rastreador Clash Royale", page_icon="🏆", layout="wide")

# Archivo para almacenar datos
DATA_FILE = "clash_royale_data.json"

# Inicializar session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'last_update' not in st.session_state:
    st.session_state.last_update = None

def load_data():
    """Cargar datos guardados del archivo JSON"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"players": {}, "history": [], "last_auto_update": None, "api_key": ""}

def save_data(data):
    """Guardar datos en archivo JSON"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_api_key(data):
    """Obtener la API key, ya sea de session_state o de los datos guardados"""
    if st.session_state.api_key and verify_api_key(st.session_state.api_key):
        return st.session_state.api_key
    elif 'api_key' in data and verify_api_key(data.get('api_key', '')):
        return data['api_key']
    return None

def verify_api_key(api_key):
    """Verificar que la API key sea válida"""
    return api_key and len(api_key) > 50

def fetch_player_data(player_tag, api_key):
    """Obtener datos del jugador de la API de Clash Royale"""
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

def auto_update_players(data, api_key):
    """Actualizar automáticamente todos los jugadores"""
    if not data['players']:
        return data
    
    success_count = 0
    fail_count = 0
    
    for tag, player_info in data['players'].items():
        try:
            player_data = fetch_player_data(tag, api_key)
            
            data['history'].append({
                'timestamp': datetime.now().isoformat(),
                'tag': player_data['tag'],
                'name': player_data['name'],
                'trophies': player_data['trophies'],
                'level': player_data['expLevel'],
                'wins': player_data['wins'],
                'losses': player_data['losses']
            })
            success_count += 1
        except Exception:
            fail_count += 1
    
    data['last_auto_update'] = datetime.now().isoformat()
    save_data(data)
    return data, success_count, fail_count

# Cargar datos existentes
data = load_data()

# AUTO-UPDATE LOGIC: Verificar si han pasado 30 minutos desde la última actualización
# Cargar datos frescos para verificar el timestamp
data = load_data()

# Obtener API key (ya sea del usuario actual o la guardada)
working_api_key = get_api_key(data)

if data['players'] and working_api_key:
    last_update = data.get('last_auto_update')
    should_update = False
    
    if last_update is None:
        should_update = True
    else:
        try:
            last_update_time = datetime.fromisoformat(last_update)
            time_diff = datetime.now() - last_update_time
            if time_diff >= timedelta(minutes=30):
                should_update = True
        except:
            should_update = True
    
    if should_update:
        with st.spinner("🔄 Actualizando datos automáticamente..."):
            data, success, fail = auto_update_players(data, working_api_key)
            if success > 0:
                st.toast(f"✅ Auto-actualización completada: {success} jugadores actualizados", icon="✅")
            # Recargar datos después de actualizar
            data = load_data()

# Título
st.title("🏆 Estatisticas Clash Royale")
st.markdown("")

# Barra lateral para la API key
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input("Input", type="password", value=st.session_state.api_key)
    st.session_state.api_key = api_key
    
    has_valid_api = verify_api_key(api_key)
    
    if has_valid_api:
        st.success("✅ API Key válida - Puedes modificar datos")
        
        # Guardar API key en el archivo de datos para que todos puedan usar
        if data.get('api_key') != api_key:
            data['api_key'] = api_key
            save_data(data)
        
        # Mostrar información de última actualización
        if data.get('last_auto_update'):
            last_update_time = datetime.fromisoformat(data['last_auto_update'])
            time_since = datetime.now() - last_update_time
            minutes_since = int(time_since.total_seconds() / 60)
            
            st.info(f"⏱️ Última actualización: hace {minutes_since} minutos")
            
            if minutes_since < 30:
                remaining = 30 - minutes_since
                st.caption(f"Próxima actualización en ~{remaining} minutos")
    else:
        # Verificar si hay API key guardada en los datos
        stored_api_key = get_api_key(data)
        if stored_api_key:
            st.success("✅ API Key configurada - Todos pueden actualizar")
        else:
            st.info("Si quieres que se anada/quitar/cambiar algo pregunta al que hizo la pagina (yo)")
    
    if has_valid_api:
        st.markdown("---")
        if st.button("🗑️ Borrar Todos los Datos"):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.success("¡Datos borrados!")
            st.rerun()

has_valid_api = verify_api_key(st.session_state.api_key)

# Sección añadir jugador
if has_valid_api:
    st.header("➕ Añadir Jugador")
    col1, col2 = st.columns([3, 1])
    with col1:
        player_tag = st.text_input("Tag del Jugador (ej., #ABC123 o ABC123)", key="player_tag_input")
    with col2:
        st.write("")
        st.write("")
        add_button = st.button("Añadir Jugador", type="primary")

    if add_button:
        if not player_tag:
            st.error("¡Por favor ingresa un tag de jugador!")
        else:
            try:
                with st.spinner("Obteniendo datos del jugador..."):
                    player_data = fetch_player_data(player_tag, api_key)
                    
                    player_tag_clean = player_data['tag']
                    
                    if player_tag_clean not in data['players']:
                        data['players'][player_tag_clean] = {
                            'name': player_data['name'],
                            'tag': player_tag_clean
                        }
                    
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

# Sección actualizar todos los jugadores manualmente - DISPONIBLE PARA TODOS
if data['players']:
    st.header("🔄 Actualizar Estadísticas")
    
    # Obtener API key (ya sea del usuario actual o la guardada)
    working_api_key = get_api_key(data)
    
    # Mostrar información diferente según si tiene API key o no
    if has_valid_api:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("💡 Los datos se actualizan automáticamente cada 30 minutos cuando alguien visita la página")
        with col2:
            update_button = st.button("Actualizar Ahora", type="secondary")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            if working_api_key:
                st.info("💡 Puedes actualizar manualmente los datos en cualquier momento")
            else:
                st.warning("⚠️ No hay API key configurada. Pide al administrador que configure una.")
        with col2:
            update_button = st.button("Actualizar Ahora", type="primary", disabled=(not working_api_key))
    
    if update_button and working_api_key:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_players = len(data['players'])
        for idx, (tag, player_info) in enumerate(data['players'].items()):
            try:
                status_text.text(f"Actualizando {player_info['name']}...")
                player_data = fetch_player_data(tag, working_api_key)
                
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
        
        data['last_auto_update'] = datetime.now().isoformat()
        save_data(data)
        status_text.text("✅ ¡Todos los jugadores actualizados!")
        st.rerun()

# Mostrar jugadores actuales
if data['players']:
    st.header("👥 Jugadores Rastreados")
    
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
            
            if has_valid_api:
                if st.button(f"Eliminar", key=f"remove_{tag}"):
                    del data['players'][tag]
                    data['history'] = [h for h in data['history'] if h['tag'] != tag]
                    save_data(data)
                    st.rerun()

# Mostrar gráfica
if data['history']:
    st.header("📈 Progreso de Trofeos")
    
    df = pd.DataFrame(data['history'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
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
        height=900
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📊 RAW DATA"):
        display_df = df[['timestamp', 'name', 'trophies', 'level', 'wins', 'losses']].copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        display_df.columns = ['Fecha y Hora', 'Jugador', 'Trofeos', 'Nivel', 'Victorias', 'Derrotas']
        st.dataframe(display_df, use_container_width=True)
elif not has_valid_api:
    st.info("📊 No hay datos disponibles todavía. Alguien con API key necesita añadir jugadores.")

# Pie de página
st.markdown("---")
st.caption("Hecho por CB")
