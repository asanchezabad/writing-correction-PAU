import streamlit as st
import json
import io
from docx import Document
from docx.shared import Pt, Inches
from fpdf import FPDF
from PIL import Image

try:
    import openai
    st.write("OpenAI version:", getattr(openai, "__version__", "Desconocida"))
except ModuleNotFoundError:
    st.error("❌ La librería 'openai' no está instalada. Añádela en requirements.txt con:\n\nopenai\n")
    st.stop()

openai.api_key = st.secrets.get("OPENAI_API_KEY", "")
if not openai.api_key:
    st.error("❌ No se ha configurado la clave API de OpenAI. Añádela en Secrets como OPENAI_API_KEY.")
    st.stop()

st.set_page_config(page_title="Writing correction B1-B2", page_icon="✍️")
st.title("✍️ Writing correction - Bachillerato")
texto_alumno = st.text_area("📄 Pega aquí el writing del alumno:", height=200)

def evaluar_rubrica_con_gpt(texto_alumno):
    prompt = f"""
Eres un profesor de inglés. Evalúa el siguiente writing para un nivel B1-B2 según esta rúbrica:

ADECUACIÓN (máximo 1.5 puntos)
- Cumplimiento de la tarea, registro y extensión (0.5)
- Variedad y organización de ideas (0.5)
- Cohesión y coherencia (0.5)

EXPRESIÓN (máximo 1.5 puntos)
- Gramática y estructuras (0.5)
- Vocabulario y riqueza léxica (0.5)
- Ortografía y puntuación (0.5)

Devolverás solo un JSON con los siguientes campos y ningún texto adicional:

{{
  "Adecuacion_Cumplimiento": 0.5,
  "Adecuacion_Variedad": 0.5,
  "Adecuacion_Cohesion": 0.5,
  "Expresion_Gramatica": 0.5,
  "Expresion_Vocabulario": 0.5,
  "Expresion_Ortografia": 0.5,
  "Justificaciones": {{
    "Cumplimiento": "detalles",
    "Variedad": "detalles",
    "Cohesion": "detalles",
    "Gramatica": "detalles",
    "Vocabulario": "detalles",
    "Ortografia": "detalles"
  }},
  "Errores_Detectados": "lista detallada",
  "Feedback": "texto detallado explicando cómo mejorar"
}}

Texto a evaluar:
'''{texto_alumno}'''
"""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=1200,
    )
    return response.choices[0].message.content

if st.button("✅ Corregir"):
    if texto_alumno.strip():
        resultado_json = evaluar_rubrica_con_gpt(texto_alumno)
        try:
            start = resultado_json.find('{')
            end = resultado_json.rfind('}') + 1
            json_str = resultado_json[start:end]
            data = json.loads(json_str)
            criterios = {
                "Cumplimiento de la tarea": data.get("Adecuacion_Cumplimiento", 0),
                "Variedad y organización": data.get("Adecuacion_Variedad", 0),
                "Cohesión y coherencia": data.get("Adecuacion_Cohesion", 0),
                "Gramática": data.get("Expresion_Gramatica", 0),
                "Vocabulario": data.get("Expresion_Vocabulario", 0),
                "Ortografía y puntuación": data.get("Expresion_Ortografia", 0)
            }
            st.session_state['criterios'] = criterios
            st.session_state['data'] = data
            st.session_state['corregido'] = True
        except json.JSONDecodeError:
            st.error("❌ La respuesta de la IA no es un JSON válido.")

if 'criterios' in st.session_state and 'data' in st.session_state:
    criterios = st.session_state['criterios']
    data = st.session_state['data']
    if st.button("📥 Descargar informe en Word"):
        doc = Document()
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Calibri'
        font.size = Pt(11)
        doc.add_heading("INFORME DE CORRECCIÓN - Writing", 0)
        try:
            doc.add_picture("logo_instituto.png", width=Inches(1.5))
        except:
            pass
        doc.add_heading("Writing original", level=1)
        doc.add_paragraph(texto_alumno)
        doc.add_heading("Resultado de la rúbrica", level=1)
        for k, v in criterios.items():
            doc.add_paragraph(f"{k}: {v}/0.5")
        doc.add_heading("Errores detectados", level=1)
        doc.add_paragraph(data.get("Errores_Detectados", "No disponible"))
        doc.add_heading("Feedback detallado", level=1)
        doc.add_paragraph(data.get("Feedback", "No disponible"))
        doc.add_heading("Writing reescrito para nota máxima (3/3)", level=1)
        doc.add_paragraph("[Espacio para sugerencia del profesor]")
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        st.download_button("Descargar informe (Word)", data=buffer, file_name="informe_writing.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    if st.button("📥 Descargar informe en PDF"):
        pdf = FPDF()
        pdf.add_page()
        try:
            pdf.image("logo_instituto.png", x=10, y=8, w=30)
        except:
            pass
        pdf.set_font("Arial", 'B', size=14)
        pdf.set_text_color(0, 0, 128)
        pdf.multi_cell(0, 10, "INFORME DE CORRECCIÓN - Writing\n\n")
        pdf.set_font("Arial", '', size=12)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 10, f"Writing original:\n{texto_alumno}\n\n")
        pdf.multi_cell(0, 10, "Resultado de la rúbrica:\n")
        for k, v in criterios.items():
            pdf.multi_cell(0, 10, f"{k}: {v}/0.5")
        pdf.multi_cell(0, 10, f"\nErrores detectados:\n{data.get('Errores_Detectados', 'No disponible')}\n")
        pdf.multi_cell(0, 10, f"\nFeedback detallado:\n{data.get('Feedback', 'No disponible')}\n")
        pdf.multi_cell(0, 10, "\nWriting reescrito para nota máxima (3/3):\n[Espacio para sugerencia del profesor]")
        buffer_pdf = io.BytesIO()
        pdf.output(buffer_pdf)
        buffer_pdf.seek(0)
        st.download_button("Descargar informe (PDF)", data=buffer_pdf, file_name="informe_writing.pdf", mime="application/pdf")
