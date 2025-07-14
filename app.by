import streamlit as st
import json

try:
    import openai
    import openai.error
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

Evalúa el texto siguiente y asigna una nota **(0, 0.25 o 0.5)** para cada criterio según los errores detectados. Sé riguroso: baja la nota cuando haya errores significativos o repetidos.
Luego, genera un feedback constructivo para que el alumno mejore.

Texto: '''{text}'''

Devuelve la respuesta en este formato JSON:
{{
  "Adecuacion_Cumplimiento": valor_numérico,
  "Adecuacion_Variedad": valor_numérico,
  "Adecuacion_Cohesion": valor_numérico,
  "Expresion_Gramatica": valor_numérico,
  "Expresion_Vocabulario": valor_numérico,
  "Expresion_Ortografia": valor_numérico,
  "Justificaciones": {{
    "Cumplimiento": texto,
    "Variedad": texto,
    "Cohesion": texto,
    "Gramatica": texto,
    "Vocabulario": texto,
    "Ortografia": texto
  }},
  "Feedback": texto
}}
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un evaluador de writings."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except openai.error.OpenAIError as e:
        return f"ERROR en la llamada a OpenAI: {e}"

if st.button("✅ Corregir"):
    if texto_alumno.strip() == "":
        st.warning("⚠️ Por favor, introduce un texto para corregir.")
    else:
        resultado_json = evaluar_rubrica_con_gpt(texto_alumno)
        
        if resultado_json.startswith("ERROR"):
            st.error(resultado_json)
        else:
            st.text("Respuesta IA bruta:")
            st.text(resultado_json)  # Mostrar para depurar
            
            try:
                start = resultado_json.find("{")
                end = resultado_json.rfind("}") + 1
                json_str = resultado_json[start:end]
                data = json.loads(json_str)
                
                st.subheader("📊 Resultado de la rúbrica")
                criterios = {
                    "Cumplimiento de la tarea": data["Adecuacion_Cumplimiento"],
                    "Variedad y organización": data["Adecuacion_Variedad"],
                    "Cohesión y coherencia": data["Adecuacion_Cohesion"],
                    "Gramática": data["Expresion_Gramatica"],
                    "Vocabulario": data["Expresion_Vocabulario"],
                    "Ortografía y puntuación": data["Expresion_Ortografia"]
                }

                total = sum(criterios.values())

                for criterio, nota in criterios.items():
                    st.write(f"**{criterio}: {nota} / 0.5**")
                    st.progress(min(nota / 0.5, 1.0))
                    st.caption(data["Justificaciones"].get(criterio.split()[0], ""))

                st.success(f"✅ **Nota total: {round(total, 2)} / 3**")
                
                st.subheader("📝 Feedback para el alumno")
                st.info(data["Feedback"])

            except json.JSONDecodeError:
                st.error("❌ Error: La respuesta de la IA no es un JSON válido.")
                st.text(resultado_json)
            except Exception as e:
                st.error(f"❌ Error inesperado: {e}")
