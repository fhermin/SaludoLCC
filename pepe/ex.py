import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
import time
import os
import pandas as pd
from deepface import DeepFace
import firebase_admin
from firebase_admin import credentials, firestore
import shutil

# Inicializar Firebase
cred = credentials.Certificate("Credenciales\lcc-hub-firebase-adminsdk-bz3gx-fd6ed6c479.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
students_ref = db.collection("students")

# Función para obtener el nombre del estudiante por ID
def obtener_nombre_estudiante_por_id(numero_ingresado):
    student_doc = students_ref.document(str(numero_ingresado)).get()
    if student_doc.exists:
        student_data = student_doc.to_dict()
        return student_data.get("name")
    else:
        return None

# Función para crear una carpeta dentro de "Database"
def crear_carpeta(nombre_carpeta):
    database_dir = "Database"
    carpeta_path = os.path.join(database_dir, nombre_carpeta)
    # Verificar si la carpeta ya existe
    if not os.path.exists(carpeta_path):
        # Si no existe, crear la carpeta dentro de "Database"
        os.makedirs(carpeta_path)
        st.success(f'Se ha creado la carpeta "{nombre_carpeta}" dentro de "Database"')
    else:
        st.warning(f'La carpeta "{nombre_carpeta}" ya existe dentro de "Database"')

# Clase para transformar el video
class FaceDetector(VideoTransformerBase):
    wait_time = 5  # Tiempo de espera en segundos
    display_time = 3  # Tiempo de visualización del nombre en segundos

    def __init__(self):
        self.last_detection_time = 0
        self.last_message_time = 0
        self.face_detected = False
        self.time_face_detected = 0
        self.stop_faces_detected = False
        self.name = ""

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        if not self.stop_faces_detected:
            gray_frame = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml').detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            if len(faces) > 0 and (time.time() - self.time_face_detected) >= self.wait_time:
                res = DeepFace.find(img, db_path='Database', enforce_detection=False, model_name='Facenet512')

                primer_diccionario = res[0]

                todos_mayor_que_cero = all(value.iloc[0] > 0 if isinstance(value, pd.Series) and not value.empty else False for key, value in primer_diccionario.items() if key != 'identity')

                if todos_mayor_que_cero:
                    identity_series = res[0]['identity']

                    if not identity_series.empty and len(identity_series) > 0:
                        photo_path = identity_series.iloc[0]
                        nombre_carpeta = os.path.basename(os.path.dirname(photo_path))
                        self.name = nombre_carpeta

                        # Obtener nombre del estudiante desde Firebase
                        student_name = obtener_nombre_estudiante_por_id(nombre_carpeta)
                        if student_name:
                            self.name = student_name

                        cv2.putText(img, self.name, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        self.face_detected = True
                        self.time_face_detected = time.time()

                        # Detener la detección de caras
                        self.stop_faces_detected = True

                        # Iniciar temporizador para el nombre
                        self.last_message_time = time.time()
                    else:
                        self.face_detected = False

        elif (time.time() - self.time_face_detected) >= self.wait_time:
            # Reanudar la detección de caras
            self.stop_faces_detected = False

        # Actualizar el nombre en la interfaz de usuario
        if time.time() - self.last_message_time < self.display_time:
            st.write(self.name)
            
        return img
    
page_bg = """
<style>
body {
    margin: 0px;
    font-family: "Source Sans Pro", sans-serif;
    font-weight: 400;
    line-height: 1.6;
    color: rgb(12, 249, 249);
    background-color: rgb(250, 250, 11);
    text-size-adjust: 100%;
    -webkit-tap-highlight-color: rgba(58, 40, 145, 0.8);
    -webkit-font-smoothing: auto;
}
</style>
<style>
.st-emotion-cache-13k62yr {
    position: absolute;
    background: rgb(233,226,218);
    color: rgb	(21, 12, 12);
    inset: 0px;
    color-scheme: light;
    overflow: hidden;
}
.st-emotion-cache-10trblm {
    position: relative;
    flex: 1 1 0%;
    margin-left: calc(4rem);
    color: rgb	(21, 12, 12);

}
.st-emotion-cache-1avcm0n {
    position: fixed;
    top: 0px;
    left: 0px;
    right: 0px;
    height: 2.875rem;
    background: rgb(251,131,81);
    background-image: url('fotito.png'); /* Ruta de la imagen */
    outline: none;
    z-index: 999990;
    display: block;
}
.st-emotion-cache-1avcm0n::after {
    content: "";
    display: block;
    width: 50px; /* Ancho de la imagen */
    height: 50px; /* Alto de la imagen */
    background-image: url('fotito.png'); /* Ruta de la imagen */
    background-size: cover;
    background-repeat: no-repeat;
    position: absolute;
    top: 5px; /* Posición vertical de la imagen desde arriba */
    right: 5px; /* Posición horizontal de la imagen desde la derecha */
    border-radius: 50%; /* Para hacer la imagen circular */
}
</style>
<h1 style='color: #333237;'>Detector de Caras en Tiempo Real</h1>
"""

# Establecer el color de fondo a blanco
theming = "fantastic"
st.markdown(page_bg,unsafe_allow_html=True)

# Crear una carpeta usando st.form
with st.form(key="create_folder_form"):
    numero_ingresado = st.text_input("Ingrese el número de estudiante:")
    submit_button = st.form_submit_button(label="Crear Carpeta")

    if submit_button and numero_ingresado:
        nombre_estudiante = obtener_nombre_estudiante_por_id(numero_ingresado)
        if nombre_estudiante:
            crear_carpeta(nombre_estudiante)
        else:
            st.warning(f"No se encontró ningún estudiante con el ID {numero_ingresado}")

# Iniciar la transmisión de la cámara en vivo y aplicar la transformación para detectar caras
webrtc_streamer(key="example", video_transformer_factory=FaceDetector)
