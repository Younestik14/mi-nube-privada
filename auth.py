import gspread
import streamlit as st

# Conexión rápida a Google Sheets (asegúrate de compartir el sheet con 'cualquiera puede editar')
def get_gsheet():
    # Nota: para proyectos más grandes, usa credenciales JSON. 
    # Para algo rápido, gspread puede abrir sheets públicos.
    gc = gspread.service_account(filename="credenciales.json") # Necesitarás subir un archivo JSON de Google Cloud
    return gc.open_by_key("https://docs.google.com/spreadsheets/d/1jGXK9O8iqP6L4AU7GEuFITTh63A3e61WKM4UxoZSUOw/edit?usp=sharing").sheet1

# Pero para evitarte complicaciones de configuración JSON ahora mismo:
# USA ESTA LÓGICA SIMPLE:
def registrar_usuario_en_sheet(nombre, num):
    # Aquí iría la lógica de escritura. 
    # Si te parece muy técnico, ¿prefieres que usemos "st.secrets" o una solución aún más simple?
