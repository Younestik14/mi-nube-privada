import sys
import os

# Esto le dice a Python: "busca en la carpeta superior donde están los demás archivos"
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import init_db, registrar_usuario
