import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

st.set_page_config(
    page_title="Mi App de Productos",
    page_icon="📦"  # También podés usar un emoji como ícono
)


st.title("📦 Proyección de Stock en base a Consumo y Vencimientos")

# --- Entradas ---
consumo_promedio = st.number_input("Consumo promedio mensual (unidades)", min_value=0.1, value=2.0)
margen_vto_meses = st.number_input("Margen de vencimiento requerido (meses)", min_value=1, value=3)
fecha_entrega_nueva = st.date_input("Fecha estimada de entrega del nuevo pedido", value=datetime.today())
vencimiento_nuevo_lote = st.date_input("Vencimiento del lote nuevo ofrecido por proveedor")

# --- Stock actual ---
st.subheader("Stock actual por lote")
stock_data = []

num_lotes = st.number_input("Cantidad de lotes actuales", min_value=1, value=2, step=1)

for i in range(num_lotes):
    st.markdown(f"**Lote {i+1}**")
    cantidad = st.number_input(f"Cantidad Lote {i+1}", min_value=0, step=1, key=f"cant_{i}")
    vencimiento = st.date_input(f"Vencimiento Lote {i+1}", key=f"vto_{i}")
    stock_data.append({"cantidad": cantidad, "vencimiento": vencimiento})

# --- Proyección ---
if st.button("Generar proyección"):
    hoy = datetime.today().date()
    mes = hoy.replace(day=1)
    proyeccion = []
    margen_meses = 3

    inventario = []
    for i, row in enumerate(stock_data):
        for _ in range(int(row["cantidad"])):
            inventario.append({
                "vencimiento": row["vencimiento"],
                "usada": False,
                "origen": f"Lote {i+1}"
            })

    lote_nuevo_agregado = False
    lote_nuevo_usado = False

    while True:
        consumo = int(consumo_promedio)
        unidades_usadas = []
        vencimientos_usados = []
        origenes_usados = []

        # Agregar nuevo lote si corresponde
        if not lote_nuevo_agregado and mes >= fecha_entrega_nueva:
            for _ in range(9999):  # simular lote amplio
                inventario.append({
                    "vencimiento": vencimiento_nuevo_lote,
                    "usada": False,
                    "origen": "Lote nuevo"
                })
            lote_nuevo_agregado = True

        disponibles = [u for u in inventario if not u["usada"] and u["vencimiento"] >= mes]
        disponibles.sort(key=lambda x: x["vencimiento"])

        for i in range(consumo):
            if i < len(disponibles):
                unidad = disponibles[i]
                unidad["usada"] = True
                unidades_usadas.append(unidad)
                vencimientos_usados.append(unidad["vencimiento"].strftime("%d/%m/%Y"))
                origenes_usados.append(unidad["origen"])
            else:
                break

                # Evaluar si se usó el nuevo lote
        se_uso_lote_nuevo = any(u["origen"] == "Lote nuevo" for u in unidades_usadas)
        if se_uso_lote_nuevo:
            lote_nuevo_usado = True

        # Evaluar si el vencimiento en origen sirve para este mes
        if lote_nuevo_usado and se_uso_lote_nuevo:
            fecha_minima_vto = (mes + relativedelta(months=margen_meses)).replace(day=1)
            if vencimiento_nuevo_lote >= fecha_minima_vto:
                cumple_vto_str = vencimiento_nuevo_lote.strftime("%d/%m/%Y")
                excluir_vto_origen = True
            else:
                cumple_vto_str = "❌ No"
                excluir_vto_origen = False
        else:
            cumple_vto_str = "-"
            excluir_vto_origen = False
        
        # Armar la lista de vencimientos sin repetir el de origen si aparece en la otra columna
        vencimientos_mostrados = []
        for unidad in unidades_usadas:
            vto_str = unidad["vencimiento"].strftime("%d/%m/%Y")
            if unidad["origen"] == "Lote nuevo" and (
                (cumple_vto_str == vto_str) or (cumple_vto_str == "❌ No")
            ):
                continue  # No mostrar en lista principal
            vencimientos_mostrados.append(vto_str)


        proyeccion.append({
            "Mes": mes.strftime("%B %Y"),
            "Unidades necesarias": consumo,
            "Unidades cubiertas": len(unidades_usadas),
            "Faltante": max(0, consumo - len(unidades_usadas)),
            "Vencimientos utilizados": ", ".join(vencimientos_mostrados) if vencimientos_mostrados else "-",
            "¿El vto. en origen sirve?": cumple_vto_str
        })


        if len(unidades_usadas) < consumo:
            break

        mes = mes + relativedelta(months=1)

    st.subheader("📊 Proyección")
    st.dataframe(pd.DataFrame(proyeccion))
