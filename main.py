import boto3
#import plotly.express as px
from datetime import datetime
import pandas as pd
from io import BytesIO
import streamlit as st
import pytz

session = boto3.client('s3',
    aws_access_key_id = st.secrets["aws"]["aws_access_key_id"],
    aws_secret_access_key = st.secrets["aws"]["aws_secret_access_key"],
     region_name='us-east-2'
)

def remove_shutdown_instruction(agent_number):
    # Primero obtenemos el archivo:
    bucket_name = 's3-pernexium-report-2'
    key_folder = 'raw/didi/didi_agent/'
    fecha = datetime.now()
    fecha_actual = fecha.strftime("%Y-%m-%d")
    
    key_final_prospectos = f'{key_folder}{fecha_actual}/shutdown_agent_{agent_number}.csv'
    
    file_content = "apagar"
    
    # Subir el archivo a S3
    response = session.delete_object(Bucket=bucket_name, Key=key_final_prospectos)
    
    return f"El agente {agent_number} no se apagará"


def send_shutdown_instruction(agent_number):
    # Primero obtenemos el archivo:
    bucket_name = 's3-pernexium-report-2'
    key_folder = 'raw/didi/didi_agent/'
    
    zona_horaria_mexico = pytz.timezone('America/Mexico_City')
    # Obtener la fecha actual en la zona horaria de CDMX
    fecha = datetime.now(zona_horaria_mexico)
    fecha_actual = fecha.strftime("%Y-%m-%d")
    
    key_final_prospectos = f'{key_folder}{fecha_actual}/shutdown_agent_{agent_number}.csv'
    
    file_content = "apagar"
    
    # Subir el archivo a S3
    response = session.put_object(Bucket=bucket_name, Key=key_final_prospectos, Body=file_content)
    
    return f"Apagado agente {agent_number}" if response['ResponseMetadata']['HTTPStatusCode'] == 200 else "No se mandó la instrucción"

# Especifica el nombre del bucket y la clave del archivo .pkl en S3
def get_data(fecha_buscar):
    data_general = pd.DataFrame()
    bucket_name = 's3-pernexium-report-2'
    key_folder = f'raw/didi/didi_agent/{fecha_buscar}/'
    
    response = session.list_objects_v2(Bucket=bucket_name, Prefix=key_folder)
        
    if 'Contents' in response:
        # Itera sobre cada archivo en el folder
        for obj in response['Contents']:
            key = obj['Key']
            #print(f"Leyendo el archivo: {key}")
    
            # Obtén el objeto desde S3
            file_response = session.get_object(Bucket=bucket_name, Key=key)
            
            # Lee el contenido del archivo en bytes
            columnas_bytes = file_response['Body'].read()
    
            # Usa BytesIO para leer el contenido como un DataFrame de pandas
            df = pd.read_csv(BytesIO(columnas_bytes))
    
            # Realiza cualquier operación que necesites con el DataFrame
            data_general = pd.concat([data_general, df])
    else:
        print(f"No se encontraron archivos en el folder {key_folder} del bucket {bucket_name}.")
        return None, None

    data_general_raw = data_general.copy()
    data_general_raw["page"] = data_general_raw.current_page.apply(lambda x: int(x.split("/")[0]))
    data_general = data_general.sort_values(by = "last_update", ascending=False).drop_duplicates(subset = ["agent_number"], keep="first")
    data_general['progress'] = data_general.current_page.apply(lambda x: int(x.split("/")[0]) / int(x.split("/")[1]))

    data_general = data_general[['agent_number', 'last_update', 'last_status', 'current_page', 'progress', 'errors']]
    data_general = data_general.sort_values(by = 'agent_number')
    return data_general, data_general_raw

st.set_page_config(
    page_title="Pernexium Agentes Automáticos",
    page_icon="./img/logo_pernexium.png"  # Puedes usar una ruta local o una URL
)

st.sidebar.title("Menú de Navegación")
opcion = st.sidebar.selectbox(
    "Selecciona una opción:",
    ("Agentes DiDi", "Gestiones BanCoppel","Gestiones Monte",  "Gestiones DiDi")
)

# ==========================================================================================
if opcion == "Gestiones BanCoppel":

    st.header("Gestiones por hora BanCoppel")
    
    mexico_city_tz = pytz.timezone('America/Mexico_City')
    
    # Obtén la fecha y hora actual en la zona horaria de Ciudad de México
    hoy = datetime.now(mexico_city_tz).date()
    #st.write(hoy)
    
    # Selector de fechas con la fecha de hoy como valor predeterminado
    col1, col2 = st.columns([9, 1])
    with col1:
        fecha_seleccionada_ = st.date_input("Seleccione una fecha:", hoy).strftime("%Y-%m-%d")
    with col2:
        #st.write("#")
        st.button('🔄')

    mes = fecha_seleccionada_[:-3].replace("-","_")
    
    bucket_name = 's3-pernexium-report-2'
    file_key = f'master/bancoppel/gestiones/{mes}/{mes}_gestiones.xlsx'  # Reemplaza con el nombre exacto del archivo
    
    # Nombre del archivo descargado en el sistema local
    try:
        # Crear un buffer de memoria
        excel_buffer = BytesIO()
        
        # Descargar el archivo en el buƒffer
        session.download_fileobj(bucket_name, file_key, excel_buffer)
        
        # Mover el puntero al inicio del buffer
        excel_buffer.seek(0)
        
        # Leer el archivo Excel en memoria con Pandas
        data_gestiones = pd.read_excel(excel_buffer, sheet_name=None)  # `sheet_name=None` para cargar todas las hojas en un dict
        data_gestiones_por_hora = data_gestiones["Por hora"].query(f"fecha == '{fecha_seleccionada_}'")
        data_gestiones_por_dia = data_gestiones["Por dia"].query(f"fecha == '{fecha_seleccionada_}'")
        data_gestiones_resumen = data_gestiones["Resumen"].query(f"fecha == '{fecha_seleccionada_}'")
        
    
    except Exception as e:
        print(f"Error al leer el archivo: {e}")


    st.header("Por hora")
    st.write(data_gestiones_por_hora)

    st.header("Por dia")
    st.write(data_gestiones_por_dia)

    st.header("Resumen")
    st.write(data_gestiones_resumen)


# ==========================================================================================


elif opcion == "Gestiones Monte":

    st.header("Gestiones por hora Monte")
    
    mexico_city_tz = pytz.timezone('America/Mexico_City')
    
    # Obtén la fecha y hora actual en la zona horaria de Ciudad de México
    hoy = datetime.now(mexico_city_tz).date()
    #st.write(hoy)
    
    # Selector de fechas con la fecha de hoy como valor predeterminado
    col1, col2 = st.columns([9, 1])
    with col1:
        fecha_seleccionada_ = st.date_input("Seleccione una fecha:", hoy).strftime("%Y-%m-%d")
    with col2:
        #st.write("#")
        st.button('🔄')

    mes = fecha_seleccionada_[:-3].replace("-","_")
    
    bucket_name = 's3-pernexium-report-2'
    file_key = f'master/monte_financiera/gestiones/{mes}/{mes}_gestiones.xlsx'  # Reemplaza con el nombre exacto del archivo
    
    # Nombre del archivo descargado en el sistema local
    try:
        # Crear un buffer de memoria
        excel_buffer = BytesIO()
        
        # Descargar el archivo en el buƒffer
        session.download_fileobj(bucket_name, file_key, excel_buffer)
        
        # Mover el puntero al inicio del buffer
        excel_buffer.seek(0)
        
        # Leer el archivo Excel en memoria con Pandas
        data_gestiones = pd.read_excel(excel_buffer, sheet_name=None, engine='openpyxl', dtype=str)
 # `sheet_name=None` para cargar todas las hojas en un dict
        data_gestiones_por_hora = data_gestiones["Por hora"].query(f"fecha == '{fecha_seleccionada_}'")
        data_gestiones_por_dia = data_gestiones["Por dia"].query(f"fecha == '{fecha_seleccionada_}'")
        data_gestiones_resumen = data_gestiones["Resumen"].query(f"fecha == '{fecha_seleccionada_}'")
        
    
    except Exception as e:
        print(f"Error al leer el archivo: {e}")


    st.header("Por hora")
    st.write(data_gestiones_por_hora)

    st.header("Por dia")
    st.write(data_gestiones_por_dia)

    st.header("Resumen")
    st.write(data_gestiones_resumen)
    

# ==========================================================================================
elif opcion == "Gestiones DiDi":

    st.header("Gestiones por hora DiDi")
    
    mexico_city_tz = pytz.timezone('America/Mexico_City')
    
    # Obtén la fecha y hora actual en la zona horaria de Ciudad de México
    hoy = datetime.now(mexico_city_tz).date()
    #st.write(hoy)
    
    # Selector de fechas con la fecha de hoy como valor predeterminado
    col1, col2 = st.columns([9, 1])
    with col1:
        fecha_seleccionada_ = st.date_input("Seleccione una fecha:", hoy).strftime("%Y-%m-%d")
    with col2:
        #st.write("#")
        st.button('🔄')

    mes = fecha_seleccionada_[:-3].replace("-","_")
    
    bucket_name = 's3-pernexium-report-2'
    file_key = f'master/didi/gestiones/{mes}/{mes}_gestiones.xlsx'  # Reemplaza con el nombre exacto del archivo
    
    # Nombre del archivo descargado en el sistema local
    try:
        # Crear un buffer de memoria
        excel_buffer = BytesIO()
        
        # Descargar el archivo en el buƒffer
        session.download_fileobj(bucket_name, file_key, excel_buffer)
        
        # Mover el puntero al inicio del buffer
        excel_buffer.seek(0)
        
        # Leer el archivo Excel en memoria con Pandas
        data_gestiones = pd.read_excel(excel_buffer, sheet_name=None)  # `sheet_name=None` para cargar todas las hojas en un dict
        data_gestiones_por_hora = data_gestiones["Por hora"].query(f"fecha == '{fecha_seleccionada_}'")
        data_gestiones_por_dia = data_gestiones["Por dia"].query(f"fecha == '{fecha_seleccionada_}'")
        data_gestiones_resumen = data_gestiones["Resumen"].query(f"fecha == '{fecha_seleccionada_}'")
        
    
    except Exception as e:
        print(f"Error al leer el archivo: {e}")


    st.header("Por hora")
    st.write(data_gestiones_por_hora)

    st.header("Por dia")
    st.write(data_gestiones_por_dia)

    st.header("Resumen")
    st.write(data_gestiones_resumen)

# ==========================================================================================
if opcion == 'Agentes DiDi':
    st.header("Interfaz de control para agentes automáticos")
    
    mexico_city_tz = pytz.timezone('America/Mexico_City')
    
    # Obtén la fecha y hora actual en la zona horaria de Ciudad de México
    hoy = datetime.now(mexico_city_tz).date()
    #st.write(hoy)
    
    # Selector de fechas con la fecha de hoy como valor predeterminado
    col1, col2 = st.columns([9, 1])
    with col1:
        fecha_seleccionada = st.date_input("Seleccione una fecha:", hoy)
    with col2:
        #st.write("#")
        st.button('🔄')
    
    data, data_raw = get_data(fecha_seleccionada)
        
    if data is None:
        st.warning("No hay información para la fecha seleccionada")
    else:
        data_raw.last_update = pd.to_datetime(data_raw.last_update)
    
        total_gestionado = 20 * (data_raw.groupby("agent_number").page.max() - data_raw.groupby("agent_number").page.min()).sum()
        
        agentes_corriendo = data_raw.agent_number.nunique()
        
        gestiones_medias = int(total_gestionado/agentes_corriendo)
        
        tiempo_medio_por_gestion = sum([data_raw.query(f"agent_number == {an}").last_update.diff().mean().total_seconds() / 20 for an in range(1, agentes_corriendo+1)])/ agentes_corriendo
        
        gestiones_en_ocho_horas = (9*60*60) / tiempo_medio_por_gestion
    
        st.data_editor(data, disabled = True, 
                       column_config={
                        "progress": st.column_config.ProgressColumn(
                            "Progress",
                            help="Progreso",
                            #format="%f",
                            min_value=0,
                            max_value=1,
                        ),
                    },
                    hide_index=True,)
    
        col1, col2  = st.columns(2)
        col1.metric(label = "Total de Cuentas gestionadas en el día", value = str(total_gestionado))
        
        col2.metric(label = "Promedio de cuentas por agente en jornada", value = f"{gestiones_en_ocho_horas:.0f}", delta = f'{gestiones_en_ocho_horas - 275:.0f}')
        
        col1.metric(label = "Productividad vs agente humano", value = f"{gestiones_en_ocho_horas/275:.1f}")
    
        col1, col2  = st.columns(2)
        
        if col1.button("Apagar todos los bots"):
            [st.write(send_shutdown_instruction(agent)) for agent in range(1, agentes_corriendo + 1)];
    
        if col2.button("Reactivar todos los bots"):
            [st.write(remove_shutdown_instruction(agent)) for agent in range(1, agentes_corriendo + 1)];


