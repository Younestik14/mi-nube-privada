"""Panel principal (dashboard) de la aplicacion: pestanas de Baja
Tension, Fotovoltaica, Industrial, Mediciones, Presupuesto, Esquema
unifilar, Memoria, Importar/Exportar, Ayuda y Asistente IA.

Reproduce exactamente la misma logica que el bloque de interfaz
original del archivo app.py monolitico; unicamente se ha reorganizado
en funciones mas pequenas y se apoya en los nuevos modulos de calculo,
exportacion y validacion.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd
import streamlit as st

from calculos.baja_tension import calcular_circuito_bt
from calculos.fotovoltaica import calcular_fv
from calculos.motores import calcular_motor
from calculos.presupuesto import Presupuesto
from core.historial import HistorialCambios
from core.memoria import MemoriaTecnica
from datos.constantes import (
    CDT_MAXIMA,
    COLUMNAS_BT,
    COLUMNAS_MEDICION_MANUAL,
    COLUMNAS_MOTORES,
    FACTORES_ARRANQUE_MOTOR,
    METODOS_INSTALACION,
    PRECIOS_DEFECTO,
    TIPOS_SUMINISTRO,
)
from datos.tablas import df_vacio
from ui.componentes import campo_texto_persistente, mostrar_caja_ayuda, numero_persistente
from utils.exportaciones import ExportadorProyecto
from utils.logging_config import obtener_logger

logger = obtener_logger(__name__)


def _tab_baja_tension(modulos: Dict[str, bool]) -> pd.DataFrame:
    """Pestana de circuitos interiores de Baja Tension."""
    st.subheader("Circuitos de Baja Tension")
    st.caption("Anade una fila por cada circuito interior (alumbrado, enchufes, electrodomesticos, etc.) y rellena sus datos.")
    df_bt_calc = df_vacio(COLUMNAS_BT)
    if not modulos.get("bt"):
        st.info("Activa el modulo 'Baja Tension' en la barra lateral para introducir circuitos.")
        return df_bt_calc

    df_editado = st.data_editor(
        st.session_state["df_bt"],
        num_rows="dynamic",
        use_container_width=True,
        key="editor_bt",
        column_config={
            "Fases": st.column_config.SelectboxColumn(options=["Monofasico", "Trifasico"], help="Numero de fases con las que se alimenta el circuito."),
            "Metodo instalacion": st.column_config.SelectboxColumn(options=list(METODOS_INSTALACION.keys()), help="Forma en que el cableado esta instalado (ver tabla ITC-BT-19 en la pestana Ayuda)."),
            "Aislamiento": st.column_config.SelectboxColumn(options=["PVC", "XLPE"], help="Material aislante del cable."),
            "Uso": st.column_config.SelectboxColumn(options=list(CDT_MAXIMA.keys()), help="Uso del circuito; determina la caida de tension maxima admisible."),
        },
    )
    HistorialCambios.detectar_cambios_df("df_bt", df_editado, "circuitos de Baja Tension")
    st.session_state["df_bt"] = df_editado

    with st.expander("Ver metodos de instalacion disponibles"):
        for k, v in METODOS_INSTALACION.items():
            st.markdown(f"**{k}**: {v}")

    if df_editado.empty:
        return df_bt_calc

    resultados = df_editado.apply(lambda f: pd.Series(calcular_circuito_bt(f)), axis=1)
    df_bt_calc = pd.concat([df_editado.reset_index(drop=True), resultados.reset_index(drop=True)], axis=1)
    st.markdown("#### Resultados de calculo")
    st.dataframe(df_bt_calc, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Circuitos totales", len(df_bt_calc))
    c2.metric("Cumplen", int((df_bt_calc["Cumple"] == "Si").sum()))
    c3.metric("A revisar", int((df_bt_calc["Cumple"] == "Revisar").sum()))

    try:
        import plotly.express as px
        conteo = df_bt_calc["Cumple"].value_counts().reset_index()
        conteo.columns = ["Estado", "Cantidad"]
        fig = px.pie(conteo, names="Estado", values="Cantidad", title="Estado de cumplimiento de circuitos",
                     color="Estado", color_discrete_map={"Si": "#2E7D32", "Revisar": "#C62828"})
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        logger.warning("No se ha podido generar el grafico de circuitos BT: %s", e)

    return df_bt_calc


def _tab_fotovoltaica(modulos: Dict[str, bool]):
    """Pestana de instalacion fotovoltaica."""
    st.subheader("Instalacion Fotovoltaica")
    if not modulos.get("fv"):
        st.info("Activa el modulo 'Fotovoltaica' en la barra lateral para realizar el dimensionado.")
        return None

    col1, col2 = st.columns(2)
    with col1:
        p_pico = numero_persistente("Potencia pico (kWp)", "fv_potencia_pico_kwp", 5.0, min_value=0.0, step=0.5,
                                     help_text="Potencia pico total de los paneles solares instalados, en kilovatios pico.")
        v_mppt = numero_persistente("Tension MPPT (V)", "fv_tension_mppt_v", 600.0, min_value=1.0, step=10.0,
                                     help_text="Tension de trabajo en el punto de maxima potencia de las cadenas de paneles.")
        n_paneles = numero_persistente("Numero de paneles", "fv_num_paneles", 12, min_value=1, step=1,
                                        help_text="Cantidad total de paneles fotovoltaicos de la instalacion.")
        long_dc = numero_persistente("Longitud tramo CC (m)", "fv_longitud_dc_m", 20.0, min_value=0.0, step=1.0,
                                      help_text="Longitud del cableado en corriente continua, desde los paneles hasta el inversor.")
    with col2:
        p_inv = numero_persistente("Potencia inversor (kW)", "fv_potencia_inversor_kw", 5.0, min_value=0.0, step=0.5,
                                    help_text="Potencia nominal del inversor fotovoltaico.")
        v_ac = numero_persistente("Tension CA (V)", "fv_tension_ac_v", 400.0, min_value=1.0, step=10.0,
                                   help_text="Tension de la red electrica en corriente alterna (habitualmente 230V monofasica o 400V trifasica).")
        long_ac = numero_persistente("Longitud tramo CA (m)", "fv_longitud_ac_m", 15.0, min_value=0.0, step=1.0,
                                      help_text="Longitud del cableado en corriente alterna, desde el inversor hasta el cuadro de conexion.")

    st.session_state["fv_datos"] = {
        "potencia_pico_kwp": p_pico, "tension_mppt_v": v_mppt, "num_paneles": n_paneles,
        "longitud_dc_m": long_dc, "longitud_ac_m": long_ac, "potencia_inversor_kw": p_inv,
        "tension_ac_v": v_ac,
    }

    resultado_fv = calcular_fv(p_pico, v_mppt, n_paneles, long_dc, long_ac, p_inv, v_ac)
    df_fv_calc = pd.DataFrame([resultado_fv])
    st.markdown("#### Resultados de calculo")
    cols = st.columns(4)
    cols[0].metric("Intensidad DC", f"{resultado_fv['Intensidad DC (A)']} A")
    cols[1].metric("Seccion DC", f"{resultado_fv['Seccion DC (mm2)']} mm2")
    cols[2].metric("Intensidad AC", f"{resultado_fv['Intensidad AC (A)']} A")
    cols[3].metric("Seccion AC", f"{resultado_fv['Seccion AC (mm2)']} mm2")
    st.dataframe(df_fv_calc, use_container_width=True)
    return df_fv_calc


def _tab_industrial(modulos: Dict[str, bool]) -> pd.DataFrame:
    """Pestana de motores e instalacion industrial."""
    st.subheader("Motores e instalacion industrial")
    df_motores_calc = df_vacio(COLUMNAS_MOTORES)
    if not modulos.get("industrial"):
        st.info("Activa el modulo 'Industrial / Motores' en la barra lateral.")
        return df_motores_calc

    df_editado_m = st.data_editor(
        st.session_state["df_motores"],
        num_rows="dynamic",
        use_container_width=True,
        key="editor_motores",
        column_config={
            "Fases": st.column_config.SelectboxColumn(options=["Monofasico", "Trifasico"]),
            "Metodo arranque": st.column_config.SelectboxColumn(options=list(FACTORES_ARRANQUE_MOTOR.keys()), help="Sistema de arranque del motor; influye en la intensidad de calculo."),
            "Metodo instalacion": st.column_config.SelectboxColumn(options=list(METODOS_INSTALACION.keys())),
        },
    )
    HistorialCambios.detectar_cambios_df("df_motores", df_editado_m, "motores")
    st.session_state["df_motores"] = df_editado_m

    if not df_editado_m.empty:
        resultados_m = df_editado_m.apply(lambda f: pd.Series(calcular_motor(f)), axis=1)
        df_motores_calc = pd.concat([df_editado_m.reset_index(drop=True), resultados_m.reset_index(drop=True)], axis=1)
        st.markdown("#### Resultados de calculo")
        st.dataframe(df_motores_calc, use_container_width=True)

    return df_motores_calc


def _tab_mediciones(df_bt_calc: pd.DataFrame, df_motores_calc: pd.DataFrame, modulos: Dict[str, bool]) -> pd.DataFrame:
    """Pestana de mediciones (automaticas y manuales)."""
    st.subheader("Mediciones")
    st.caption("Cantidades de materiales calculadas automaticamente a partir de los circuitos y motores introducidos.")
    df_auto = Presupuesto.generar_mediciones_auto(df_bt_calc if modulos.get("bt") else None, df_motores_calc if modulos.get("industrial") else None)
    st.markdown("#### Mediciones generadas automaticamente")
    st.dataframe(df_auto, use_container_width=True)

    st.markdown("#### Mediciones manuales adicionales")
    df_manual_editado = st.data_editor(
        st.session_state["df_mediciones_manual"], num_rows="dynamic", use_container_width=True, key="editor_mediciones",
    )
    HistorialCambios.detectar_cambios_df("df_mediciones_manual", df_manual_editado, "mediciones manuales")
    st.session_state["df_mediciones_manual"] = df_manual_editado

    if not df_manual_editado.empty:
        df_mediciones_total = pd.concat([df_auto, df_manual_editado], ignore_index=True)
    else:
        df_mediciones_total = df_auto
    return df_mediciones_total


def _tab_presupuesto(df_mediciones_total: pd.DataFrame):
    """Pestana de presupuesto (PEM, gastos generales, beneficio industrial, IVA)."""
    st.subheader("Presupuesto")
    df_presupuesto, resumen = Presupuesto.calcular_presupuesto(df_mediciones_total)
    st.dataframe(df_presupuesto, use_container_width=True)

    if resumen:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("PEM", f"{resumen['PEM']:,.2f} EUR", help="Presupuesto de Ejecucion Material: suma de todas las mediciones por su precio unitario.")
        c2.metric("Base licitacion", f"{resumen['Base de licitacion']:,.2f} EUR", help="PEM + Gastos Generales + Beneficio Industrial.")
        c3.metric("IVA", f"{resumen['IVA']:,.2f} EUR")
        c4.metric("TOTAL", f"{resumen['TOTAL']:,.2f} EUR")

        try:
            import plotly.express as px
            if not df_presupuesto.empty:
                resumen_capitulo = df_presupuesto.groupby("Capitulo")["Importe (EUR)"].sum().reset_index()
                fig = px.bar(resumen_capitulo, x="Capitulo", y="Importe (EUR)", title="Importe por capitulo", color="Capitulo")
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.warning("No se ha podido generar el grafico de presupuesto: %s", e)

    with st.expander("Editar precios por defecto"):
        for k in list(PRECIOS_DEFECTO.keys()):
            clave_precio = f"precio_{k}"
            valor_actual = numero_persistente(k, clave_precio, float(PRECIOS_DEFECTO[k]))
            PRECIOS_DEFECTO[k] = valor_actual

    return df_presupuesto, resumen


def _tab_esquema_unifilar(df_bt_calc: pd.DataFrame) -> None:
    """Pestana informativa del esquema unifilar (la descarga esta en Importar/Exportar)."""
    st.subheader("Esquema unifilar")
    st.caption(
        "Configurador tipo CIEBT: selecciona el tipo de suministro en la barra lateral y genera "
        "el esquema unifilar con la cadena de acometida, proteccion, medida y derivaciones a cada "
        "circuito interior, listo para exportar en formato DXF."
    )
    info_sum = TIPOS_SUMINISTRO[st.session_state["tipo_suministro"]]
    st.markdown(f"**Tipo de suministro seleccionado:** {st.session_state['tipo_suministro']}")
    st.markdown(info_sum["descripcion"])
    st.markdown("**Elementos que se incluiran en el esquema:**")
    for el in info_sum["elementos"]:
        st.markdown(f"- {el}")
    if not df_bt_calc.empty:
        st.markdown(f"Se incluiran **{len(df_bt_calc)}** circuitos interiores derivados del embarrado del cuadro general.")
    else:
        st.warning("No hay circuitos de Baja Tension definidos todavia; el esquema se generara solo con la parte de suministro.")


def _tab_memoria(dp: Dict[str, Any]) -> str:
    """Pestana de Memoria Tecnica de Diseno (MTD)."""
    st.subheader("Memoria Tecnica de Diseno (MTD)")
    dp["objeto"] = campo_texto_persistente(
        "1. Objeto de la memoria", "campo_objeto", dp.get("objeto", ""), area=True,
        help_text="Explica brevemente para que sirve esta memoria (ej: legalizar una instalacion electrica en vivienda unifamiliar).",
    )
    dp["normativa"] = campo_texto_persistente(
        "3. Reglamentacion y disposiciones aplicadas", "campo_normativa", dp.get("normativa", ""), area=True,
        help_text="Lista la normativa aplicable (REBT, ITC-BT, normas UNE, ordenanzas municipales, etc.). Si lo dejas vacio se usara un texto por defecto.",
    )
    dp["descripcion"] = campo_texto_persistente(
        "4. Descripcion general de la instalacion (potencia, uso, caracteristicas)", "campo_descripcion", dp.get("descripcion", ""), area=True,
        help_text="Describe la potencia total prevista, el uso del inmueble y las caracteristicas generales de la instalacion.",
    )

    texto_memoria = MemoriaTecnica.generar_texto({
        "datos_proyecto": dp, "tipo_suministro": st.session_state["tipo_suministro"],
    })
    st.markdown("#### Vista previa")
    st.text_area("Contenido de la memoria", value=texto_memoria, height=350, disabled=True)
    return texto_memoria


def _tab_importar_exportar(
    dp: Dict[str, Any],
    df_bt_calc: pd.DataFrame,
    df_fv_calc,
    df_motores_calc: pd.DataFrame,
    df_mediciones_total: pd.DataFrame,
    resumen: Dict[str, float],
    texto_memoria: str,
) -> None:
    """Pestana de importacion masiva de datos y exportacion de resultados."""
    st.subheader("Importar datos desde archivo")
    st.markdown("Descarga las plantillas, rellenalas y vuelve a subirlas para importar circuitos, motores o mediciones de forma masiva.")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.download_button("Plantilla circuitos BT (.csv)", data=df_vacio(COLUMNAS_BT).to_csv(index=False), file_name="plantilla_circuitos_bt.csv", mime="text/csv")
    with col_b:
        st.download_button("Plantilla motores (.csv)", data=df_vacio(COLUMNAS_MOTORES).to_csv(index=False), file_name="plantilla_motores.csv", mime="text/csv")
    with col_c:
        st.download_button("Plantilla mediciones (.csv)", data=df_vacio(COLUMNAS_MEDICION_MANUAL).to_csv(index=False), file_name="plantilla_mediciones.csv", mime="text/csv")

    tipo_importacion = st.selectbox("Que deseas importar", ["Circuitos de Baja Tension", "Motores", "Mediciones manuales"])
    archivo_datos = st.file_uploader("Selecciona un archivo .csv o .xlsx", type=["csv", "xlsx"], key="cargador_datos")
    if archivo_datos is not None:
        try:
            if archivo_datos.name.endswith(".csv"):
                df_importado = pd.read_csv(archivo_datos)
            else:
                df_importado = pd.read_excel(archivo_datos)
            if tipo_importacion == "Circuitos de Baja Tension":
                st.session_state["df_bt"] = df_importado
            elif tipo_importacion == "Motores":
                st.session_state["df_motores"] = df_importado
            else:
                st.session_state["df_mediciones_manual"] = df_importado
            HistorialCambios.registrar("Importacion de archivo", f"{tipo_importacion} desde {archivo_datos.name}")
            st.success(f"Datos de '{tipo_importacion}' importados correctamente. Revisa la pestana correspondiente.")
        except Exception as e:
            logger.error("Error al importar archivo de datos: %s", e)
            st.error(f"No se ha podido importar el archivo: {e}")

    st.divider()
    st.subheader("Exportar resultados")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        buffer_excel = ExportadorProyecto.exportar_excel(df_bt_calc, df_motores_calc, df_mediciones_total, resumen)
        st.download_button("Excel (mediciones/presupuesto)", data=buffer_excel, file_name="calculo_electrico.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with col2:
        try:
            dxf_bytes = ExportadorProyecto.generar_esquema_unifilar_dxf({"datos_proyecto": dp, "tipo_suministro": st.session_state["tipo_suministro"]}, df_bt_calc)
            st.download_button("Esquema unifilar (.dxf)", data=dxf_bytes, file_name="esquema_unifilar.dxf", mime="application/dxf")
            st.caption("Formato DXF abierto; se puede abrir y guardar como .dwg desde AutoCAD.")
        except Exception as e:
            logger.error("Error al generar el DXF: %s", e)
            st.error(f"No se ha podido generar el DXF: {e}")

    with col3:
        try:
            buffer_pdf = ExportadorProyecto.exportar_memoria_pdf(
                {"datos_proyecto": dp, "tipo_suministro": st.session_state["tipo_suministro"]},
                texto_memoria, df_bt_calc, df_fv_calc, df_motores_calc,
                df_mediciones_total, resumen,
            )
            st.download_button("Memoria (.pdf)", data=buffer_pdf, file_name="memoria_tecnica.pdf", mime="application/pdf")
        except Exception as e:
            logger.error("Error al generar el PDF: %s", e)
            st.error(f"No se ha podido generar el PDF: {e}")

    with col4:
        try:
            buffer_word = ExportadorProyecto.exportar_memoria_word(texto_memoria)
            st.download_button("Memoria (.docx)", data=buffer_word, file_name="memoria_tecnica.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except Exception as e:
            logger.error("Error al generar el Word: %s", e)
            st.error(f"No se ha podido generar el Word: {e}")


def _tab_ayuda() -> None:
    """Pestana de ayuda con guia rapida de uso paso a paso."""
    st.subheader("Guia rapida de uso")
    mostrar_caja_ayuda(
        "Aqui tienes una explicacion sencilla, paso a paso, de cada parte de la "
        "aplicacion. Si tienes dudas sobre un campo concreto, pasa el raton por encima de su etiqueta: "
        "muchos campos tienen un pequeno icono de interrogacion con una explicacion."
    )

    with st.expander("1. Datos del proyecto y tipo de suministro (barra lateral)", expanded=True):
        st.markdown(
            "Rellena el titular, el emplazamiento y la fecha del proyecto. Despues elige el **tipo de "
            "suministro**: esto le dice a la aplicacion como se alimenta tu instalacion (con caja general "
            "de proteccion para un unico usuario, con centralizacion de contadores en un edificio, con "
            "transformador propio en Media Tension, o con generacion propia/autoconsumo). Esta eleccion "
            "cambia automaticamente los elementos que se dibujan despues en el esquema unifilar."
        )

    with st.expander("2. Modulos activos"):
        st.markdown(
            "Marca las casillas de los bloques que necesites: Baja Tension (circuitos interiores), "
            "Fotovoltaica (paneles solares) e Industrial/Motores. Solo apareceran los datos de los "
            "modulos que actives, para que la pantalla no se sature de campos que no vas a usar."
        )

    with st.expander("3. Pestana Baja Tension"):
        st.markdown(
            "Pulsa el boton '+' de la tabla para anadir un circuito nuevo (por ejemplo, alumbrado de "
            "salon o enchufes de cocina). Rellena la potencia, la tension, el metodo de instalacion y "
            "el uso. La aplicacion calculara automaticamente la intensidad, la seccion del cable, la "
            "proteccion necesaria y la caida de tension, indicando si el circuito 'Cumple' o hay que "
            "'Revisar' los datos introducidos."
        )

    with st.expander("4. Pestana Fotovoltaica"):
        st.markdown(
            "Introduce la potencia pico de los paneles, la tension de trabajo, el numero de paneles y "
            "las longitudes de cable en corriente continua (paneles-inversor) y corriente alterna "
            "(inversor-cuadro). La aplicacion calcula las secciones y protecciones recomendadas para "
            "ambos tramos."
        )

    with st.expander("5. Pestana Industrial / Motores"):
        st.markdown(
            "Anade una fila por cada motor, indicando su potencia, rendimiento, factor de potencia y "
            "metodo de arranque (directo, estrella-triangulo, arrancador suave o variador). El metodo "
            "de arranque influye en la intensidad de calculo y, por tanto, en la seccion del cable."
        )

    with st.expander("6. Mediciones y Presupuesto"):
        st.markdown(
            "En 'Mediciones' se generan automaticamente las cantidades de cable, tubo y protecciones "
            "necesarias segun los circuitos y motores introducidos; tambien puedes anadir lineas "
            "manuales. En 'Presupuesto' se calcula el importe total (PEM, gastos generales, beneficio "
            "industrial e IVA); puedes ajustar los precios por defecto en el desplegable correspondiente."
        )

    with st.expander("7. Esquema unifilar"):
        st.markdown(
            "Esta pestana muestra que elementos se incluiran en el esquema segun el tipo de suministro "
            "elegido. Para descargar el dibujo, ve a la pestana 'Importar/Exportar' y pulsa el boton de "
            "'Esquema unifilar (.dxf)'. El archivo DXF se puede abrir directamente con AutoCAD u otros "
            "programas CAD, y guardarlo desde alli como .dwg si lo necesitas."
        )

    with st.expander("8. Memoria"):
        st.markdown(
            "Rellena el objeto, la normativa aplicada y una breve descripcion de la instalacion. La "
            "aplicacion genera automaticamente el resto de apartados (titular, tipo de suministro, "
            "calculos justificativos y anexos) siguiendo la estructura habitual de una Memoria Tecnica "
            "de Diseno (MTD) profesional."
        )

    with st.expander("9. Importar / Exportar"):
        st.markdown(
            "Puedes descargar plantillas en Excel/CSV, rellenarlas fuera de la aplicacion y volver a "
            "subirlas para cargar muchos circuitos, motores o mediciones de golpe. Tambien puedes "
            "exportar los resultados en Excel, el esquema unifilar en DXF, y la memoria completa en "
            "PDF o Word."
        )

    with st.expander("10. Preguntas frecuentes"):
        st.markdown(
            "**Por que un circuito aparece como 'Revisar'?** Porque la seccion calculada no cumple la "
            "caida de tension maxima o no hay intensidad admisible definida para ese metodo de "
            "instalacion; prueba a aumentar la seccion, reducir la longitud o cambiar el metodo.\n\n"
            "**Los valores son oficiales?** Son valores de referencia tomados de las tablas habituales "
            "del REBT/ITC-BT-19. Antes de presentar un proyecto o boletin oficial, verifica siempre los "
            "datos con la edicion vigente del reglamento y con un tecnico competente."
        )


def _tab_asistente_ia() -> None:
    """Pestana del asistente de IA (orientativo, requiere clave de API propia)."""
    st.subheader("Asistente IA para dimensionado")
    mostrar_caja_ayuda(
        "Este asistente puede darte orientacion adicional sobre como dimensionar "
        "tu instalacion, pero <b>no sustituye el calculo normativo de la aplicacion ni la revision de un "
        "tecnico competente</b>. Las respuestas son orientativas."
    )

    clave_api = None
    try:
        clave_api = st.secrets.get("OPENAI_API_KEY", None)
    except Exception:
        clave_api = None

    if not clave_api:
        st.warning(
            "No hay ninguna clave de API configurada todavia, asi que el asistente no puede conectarse. "
            "Para activarlo, tienes que anadir tu propia clave (por ejemplo de OpenAI) en los 'Secrets' "
            "de tu aplicacion de Streamlit:"
        )
        st.markdown(
            "- En Streamlit Community Cloud: abre tu app, entra en 'Settings', luego 'Secrets' y anade "
            "una linea con el texto OPENAI_API_KEY seguido de un signo igual y tu clave entre comillas; "
            "guarda los cambios.\n"
            "- En local: crea un archivo secrets.toml dentro de una carpeta llamada .streamlit en tu "
            "proyecto, con esa misma linea.\n\n"
            "Por seguridad, esa clave la debes generar y pegar tu mismo: esta aplicacion nunca almacena "
            "ni pide tu clave a traves del chat."
        )
        return

    if "campo_pregunta_ia" not in st.session_state:
        st.session_state["campo_pregunta_ia"] = ""
    st.text_area(
        "Describe tu instalacion o tu duda",
        key="campo_pregunta_ia",
        height=120,
        help="Ejemplo: Tengo una vivienda de 90 m2 con cocina de induccion de 7kW, que seccion necesito para ese circuito?",
    )
    incluir_contexto = st.checkbox(
        "Incluir automaticamente los datos ya introducidos en el proyecto (tipo de suministro, numero de circuitos, etc.)",
        value=True,
    )

    if not st.button("Preguntar al asistente"):
        return

    pregunta = st.session_state["campo_pregunta_ia"].strip()
    if not pregunta:
        st.error("Escribe primero tu pregunta o una breve descripcion de la instalacion.")
        return

    contexto = ""
    if incluir_contexto:
        contexto = (
            f"Tipo de suministro: {st.session_state.get('tipo_suministro')}. "
            f"Circuitos de Baja Tension definidos: {len(st.session_state.get('df_bt', []))}. "
            f"Motores definidos: {len(st.session_state.get('df_motores', []))}. "
            f"Modulos activos: {st.session_state.get('modulos')}."
        )
    try:
        import requests
        respuesta = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {clave_api}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": (
                        "Eres un asistente de apoyo para el predimensionado de instalaciones "
                        "electricas de baja tension conforme al REBT/ITC-BT espanol. Da "
                        "respuestas claras, breves y orientativas, recordando siempre que deben "
                        "verificarse por un tecnico competente antes de ejecutar o legalizar la "
                        "instalacion."
                    )},
                    {"role": "user", "content": f"{contexto}\n\nPregunta: {pregunta}"},
                ],
                "temperature": 0.3,
            },
            timeout=30,
        )
        if respuesta.status_code == 200:
            texto_respuesta = respuesta.json()["choices"][0]["message"]["content"]
            st.markdown("#### Respuesta del asistente")
            st.write(texto_respuesta)
            HistorialCambios.registrar("Consulta al asistente IA", pregunta[:80])
        else:
            logger.error("El servicio de IA devolvio un error HTTP %s", respuesta.status_code)
            st.error(f"El servicio de IA ha devuelto un error ({respuesta.status_code}). Revisa tu clave de API.")
    except Exception as e:
        logger.error("No se ha podido contactar con el servicio de IA: %s", e)
        st.error(f"No se ha podido contactar con el servicio de IA: {e}")


def render_dashboard(modulos: Dict[str, bool], dp: Dict[str, Any]) -> None:
    """Renderiza el panel principal completo (las 10 pestanas de la aplicacion).

    Args:
        modulos: Diccionario de modulos activos (bt, fv, industrial).
        dp: Diccionario de datos generales del proyecto (titular, emplazamiento, etc.).
    """
    (tab_bt, tab_fv, tab_ind, tab_med, tab_pres, tab_esq,
     tab_mem, tab_io, tab_ayuda, tab_ia) = st.tabs([
        "Baja Tension", "Fotovoltaica", "Industrial",
        "Mediciones", "Presupuesto", "Esquema unifilar",
        "Memoria", "Importar/Exportar", "Ayuda", "Asistente IA",
    ])

    with tab_bt:
        df_bt_calc = _tab_baja_tension(modulos)

    with tab_fv:
        df_fv_calc = _tab_fotovoltaica(modulos)

    with tab_ind:
        df_motores_calc = _tab_industrial(modulos)

    with tab_med:
        df_mediciones_total = _tab_mediciones(df_bt_calc, df_motores_calc, modulos)

    with tab_pres:
        _df_presupuesto, resumen = _tab_presupuesto(df_mediciones_total)

    with tab_esq:
        _tab_esquema_unifilar(df_bt_calc)

    with tab_mem:
        texto_memoria = _tab_memoria(dp)

    with tab_io:
        _tab_importar_exportar(dp, df_bt_calc, df_fv_calc, df_motores_calc, df_mediciones_total, resumen, texto_memoria)

    with tab_ayuda:
        _tab_ayuda()

    with tab_ia:
        _tab_asistente_ia()
