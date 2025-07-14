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
    import openai.error
    prompt = f"Evaluación writing:\n{text}"
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
        )
        return response.choices[0].message.content
    except openai.OpenAIError as e:
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
                data = json.loads(resultado_json)
                
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

                st.success(f"✅ **Nota total: {round(total,2)} / 3**")
                
                st.subheader("📝 Feedback para el alumno")
                st.info(data["Feedback"])

            except json.JSONDecodeError:
                st.error("❌ Error: La respuesta de la IA no es un JSON válido.")
                st.text(resultado_json)
            except Exception as e:
                st.error(f"❌ Error inesperado: {e}")
