"""
auth.py
Este archivo contiene la lista maestra de estudiantes autorizados.
Para dar acceso a alguien, simplemente añade su ID a la lista 'lista_aprobados'.
"""

# Lista maestra de estudiantes autorizados. 
# Solo los números que estén aquí podrán iniciar sesión.
lista_aprobados = [
    "1868628", "123456"
    # Añade aquí los nuevos IDs aceptados, por ejemplo:
    # "12345", 
    # "67890"
]

def verificar_acceso(num_estudiante):
    """
    Comprueba si el número de estudiante está en la lista de aprobados.
    Retorna True si tiene acceso, False en caso contrario.
    """
    # strip() elimina espacios accidentales al inicio o final del ID
    # str() asegura que estamos comparando siempre como texto
    return str(num_estudiante).strip() in lista_aprobados
