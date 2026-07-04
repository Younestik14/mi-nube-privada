import streamlit as st

# Lista de estudiantes pre-aprobados (puedes añadir más aquí)
lista_aprobados = ["1868628"]

def verificar_acceso(num_estudiante):
    return num_estudiante in lista_aprobados
