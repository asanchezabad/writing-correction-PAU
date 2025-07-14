import streamlit as st
import json

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

st.set_page_config(page_title="Corrección de Writings", page_icon="✍️")
st.title("✍️ Corrección de Writings con IA y Rúbrica dinámica")
texto_alumno = st.text_area("📄 Pega aquí el writing del alumno:", height=200)

def evaluar_rubrica_con_gpt(text):
    if not openai.api_key:
        return "❌ OpenAI API key no configurada."

    prompt = f"""
Eres un profesor que evalúa un writing en inglés con esta rúbrica (puntuaciones máximas indicadas):

ADECUACIÓN (máximo 1.5 puntos)
- Cumplimiento de la tarea, registro y extensión (0.5)
- Variedad y organización de ideas (0.5)
- Cohesión y coherencia (0.5)

EXPRESIÓN (máximo 1.5 puntos)
- Gramática y estructuras (0.5)
- Vocabulario y riqueza léxica (0.5)
- Ortografía y puntuación (0.5)

Evalúa el texto siguiente y asigna una nota **(0, 0.25 o 0.5)** para cada criterio según los errores detectados.
IMPORTANTE: No añadas explicaciones ni texto antes o después del JSON. Devuelve solo un objeto JSON válido, sin formato adicional.

Además, para cada criterio, incluye en "Justificaciones" los errores concretos que observas y en "Feedback" escribe un texto largo explicando cómo mejorar específicamente cada apartado.

Texto: '''{text}'''

{{
  "Adecuacion_Cumplimiento": valor_numérico,
  "Adecuacion_Variedad": valor_numérico,
  "Adecuacion_Cohesion": valor_numérico,
  "Expresion_Gramatica": valor_numérico,
  "Expresion_Vocabulario": valor_numérico,
  "Expresion_Ortografia": valor_numérico,
  "Justificaciones": {{
    "Cumplimiento": "errores detectados y explicación",
    "Variedad": "errores detectados y explicación",
    "Cohesion": "errores detectados y explicación",
    "Gramatica": "errores detectados y explicación",
    "Vocabulario": "errores detectados y explicación",
    "Ortografia": "errores detectados y explicación"
  }},
  "Errores_Detectados": "Lista completa de errores cometidos por el alumno con ejemplos específicos y correcciones sugeridas.",
  "Feedback": "Texto detallado explicando cómo mejorar en cada criterio."
}}
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except openai.OpenAIError as e:
        if "insufficient_quota" in str(e):
            return "❌ OpenAI API error: Cuota agotada o insuficiente. Revisa tu plan en https://platform.openai.com/account/billing"
        return f"❌ OpenAI API error: {e}"

if st.button("✅ Corregir"):
    if texto_alumno.strip() == "":
        st.warning("⚠️ Por favor, introduce un texto para corregir.")
    else:
        resultado_json = evaluar_rubrica_con_gpt(texto_alumno)
        if resultado_json.startswith("❌ OpenAI API error"):
            st.error(resultado_json)
        else:
            try:
                start = resultado_json.find('{')
                end = resultado_json.rfind('}') + 1
                json_str = resultado_json[start:end]
                data = json.loads(json_str)
                
                st.subheader("📊 Resultado de la rúbrica")
                criterios = {
                    "Cumplimiento de la tarea": data.get("Adecuacion_Cumplimiento", 0),
                    "Variedad y organización": data.get("Adecuacion_Variedad", 0),
                    "Cohesión y coherencia": data.get("Adecuacion_Cohesion", 0),
                    "Gramática": data.get("Expresion_Gramatica", 0),
                    "Vocabulario": data.get("Expresion_Vocabulario", 0),
                    "Ortografía y puntuación": data.get("Expresion_Ortografia", 0)
                }

                total = sum(criterios.values())

                for criterio, nota in criterios.items():
                    st.write(f"**{criterio}: {nota} / 0.5**")
                    st.progress(min(nota / 0.5, 1.0))
                    st.caption(data.get("Justificaciones", {}).get(criterio.split()[0], ""))

                st.success(f"✅ **Nota total: {round(total,2)} / 3**")
                
                    st.markdown("""
    <div style='background-color:#e6ffe6; padding:15px; border-radius:12px; border: 2px solid green; font-size:16px;'>
    📝 <strong style='color:darkgreen;'>Feedback para el alumno:</strong>
    </div>""", unsafe_allow_html=True)
    st.write(data.get("Feedback", "No disponible"))

            except json.JSONDecodeError:
                st.error("❌ Error: La respuesta de la IA no es un JSON válido.")
                st.text(resultado_json)
            except Exception as e:
                    st.error(f"❌ Error inesperado: {e}")
                    st.stop()
