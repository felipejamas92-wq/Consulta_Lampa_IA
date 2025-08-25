import streamlit as st
import os
import requests
import PyPDF2
import docx
import subprocess

# ==== CONFIGURACIÓN ====
CARPETA_DOCS = "documentos"
os.makedirs(CARPETA_DOCS, exist_ok=True)

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
HEADERS = {"Authorization": f"Bearer {st.secrets['HF_API_TOKEN']}"}

# ==== FUNCIONES DE ARCHIVOS ====
def leer_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def leer_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

def leer_pdf(file_path):
    reader = PyPDF2.PdfReader(file_path)
    return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

def cargar_archivo(file_path):
    if file_path.endswith(".txt"):
        return leer_txt(file_path)
    elif file_path.endswith(".pdf"):
        return leer_pdf(file_path)
    elif file_path.endswith(".doc") or file_path.endswith(".docx"):
        return leer_docx(file_path)
    else:
        return ""

# ==== FUNCIÓN HUGGING FACE ====
def consultar_modelo(contexto, pregunta):
    prompt = f"Responde en base al siguiente texto:\n\n{contexto}\n\nPregunta: {pregunta}\n\nRespuesta:"
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 300}}
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    return response.json()

# ==== FUNCIÓN PARA AUTO COMMIT & PUSH ====
def git_commit_push(mensaje="Archivo subido automáticamente"):
    try:
        subprocess.run(["git", "add", CARPETA_DOCS], check=True)
        subprocess.run(["git", "commit", "-m", mensaje], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        st.success("✅ Archivo guardado en GitHub automáticamente")
    except subprocess.CalledProcessError:
        st.error("❌ Error al subir a GitHub. Verifica configuración de Git y permisos.")

# ==== INTERFAZ ====
st.title("📚 Consulta IA Lampa")

rol = st.sidebar.radio("Selecciona rol:", ["Usuario", "Administrador"])

# --- Administrador ---
if rol == "Administrador":
    password = st.sidebar.text_input("🔑 Clave de administrador", type="password")
    if password == "mi_clave_segura":  # Cambia por tu clave real
        st.sidebar.success("✅ Acceso como Administrador")

        uploaded_file = st.file_uploader("Sube archivos (.txt, .pdf, .docx)", type=["txt","pdf","doc","docx"])
        if uploaded_file:
            file_path = os.path.join(CARPETA_DOCS, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Archivo '{uploaded_file.name}' guardado localmente en '{CARPETA_DOCS}'")

            # Auto commit & push a GitHub
            git_commit_push(f"Archivo '{uploaded_file.name}' subido desde la app")

    else:
        st.sidebar.error("❌ Clave incorrecta")

# --- Usuario ---
st.header("📄 Consultar documentos")

archivos = [os.path.join(CARPETA_DOCS, f) for f in os.listdir(CARPETA_DOCS)]
if not archivos:
    st.warning("⚠️ No hay documentos. Espera que el Administrador suba archivos.")
else:
    textos = [cargar_archivo(f) for f in archivos]
    contexto_total = "\n".join(textos)

    pregunta = st.text_input("❓ Escribe tu pregunta sobre los documentos:")
    if pregunta:
        respuesta = consultar_modelo(contexto_total, pregunta)
        st.subheader("🧠 Respuesta:")
        st.write(respuesta)
