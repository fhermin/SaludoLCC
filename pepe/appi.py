import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
import time
import os
import pandas as pd
from deepface import DeepFace
import firebase_admin
import re
from firebase_admin import credentials, firestore

try:
    cred = credentials.Certificate("Credenciales\lcc-hub-firebase-adminsdk-bz3gx-fd6ed6c479.json")
    firebase_admin.initialize_app(cred)
    print("Firebase initialized successfully.")
except Exception as e:
    print("Error initializing Firebase:", e)

# Obtener referencia a la colección "students"
db = firestore.client()
students_ref = db.collection("students")

# Definir una clase para transformar el video
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
        return transformar_video(frame)
    
# Ruta de la carpeta principal
DATABASE_FOLDER = "Database"

def obtener_nombre_estudiante_por_id(numero_ingresado):
    # Obtener todos los documentos en la colección "students"
    students_docs = students_ref.get()

    # Iterar sobre los documentos y comparar con el número ingresado
    for doc in students_docs:
        if doc.id == str(numero_ingresado):
            student_data = doc.to_dict()  # Convertir el documento a un diccionario
            name = student_data.get("name")
            # Eliminar caracteres no deseados usando expresiones regulares
            cleaned_name = re.sub(r'[^a-zA-Z\s]', '', name)
            return cleaned_name.strip()  # Devolver el nombre del estudiante limpio sin espacios al principio ni al final

    # Si no se encuentra ninguna coincidencia, devolver None
    return None
    
IMG_WIDTH = 150
IMG_HEIGHT = 150

def capturar_fotogramas_y_crear_carpeta(nombre_carpeta):
    # Detener el FaceDetector
    face_detector.stop_faces_detected = True

    ruta_carpeta = os.path.join(DATABASE_FOLDER, nombre_carpeta)
    try:
        os.mkdir(ruta_carpeta)
        st.success(f'Se creó la carpeta "{nombre_carpeta}"')

        # Capturar cinco fotos en intervalos de tres segundos
        for i in range(5):
            time.sleep(3)  # Esperar 3 segundos
            foto_path = os.path.join(ruta_carpeta, f"foto_{i+1}.jpg")  # Ruta para guardar la foto
            capture = cv2.VideoCapture(0)  # Inicializar la captura de la cámara
            ret, frame = capture.read()  # Leer un fotograma de la cámara

            if ret:
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml').detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                if len(faces) > 0:
                    # Tomar solo la primera cara detectada
                    x, y, w, h = faces[0]
                    # Recortar la región de interés (ROI) que contiene el rostro
                    face_roi = frame[y:y+h, x:x+w]
                    # Redimensionar la imagen al tamaño estándar
                    resized_face = cv2.resize(face_roi, (IMG_WIDTH, IMG_HEIGHT))
                    cv2.imwrite(foto_path, resized_face)  # Guardar la foto recortada y redimensionada en la carpeta
                    st.success(f"Foto {i+1} capturada y guardada correctamente en {foto_path}")
                else:
                    st.error("No se detectaron rostros. Inténtelo de nuevo.")

            else:
                st.error("Error al capturar la foto. Inténtelo de nuevo.")

            capture.release()  # Liberar la captura de la cámara

    except FileExistsError:
        st.error(f'El usuario "{nombre_carpeta}" ya existe')

    # Reanudar el FaceDetector
    face_detector.stop_faces_detected = False


# Definir una función para transformar el video y detectar caras
def transformar_video(frame):
    img = frame.to_ndarray(format="bgr24")
    
    if not face_detector.stop_faces_detected:
        gray_frame = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml').detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) > 0 and (time.time() - face_detector.time_face_detected) >= face_detector.wait_time:
            res = DeepFace.find(img, db_path='Database', enforce_detection=False, model_name='Facenet512')

            primer_diccionario = res[0]

            todos_mayor_que_cero = all(value.iloc[0] > 0 if isinstance(value, pd.Series) and not value.empty else False for key, value in primer_diccionario.items() if key != 'identity')

            if todos_mayor_que_cero:
                identity_series = res[0]['identity']

                if not identity_series.empty and len(identity_series) > 0:
                    photo_path = identity_series.iloc[0]
                    nombre_carpeta = os.path.basename(os.path.dirname(photo_path))
                    face_detector.name = nombre_carpeta
                    print(face_detector.name)
                    st.write(face_detector.name)
                    
                    # Agregar texto al fotograma de salida
                    cv2.putText(img, face_detector.name, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    face_detector.face_detected = True
                    face_detector.time_face_detected = time.time()

                    # Detener la detección de caras
                    face_detector.stop_faces_detected = True

                    # Iniciar temporizador para el nombre
                    face_detector.last_message_time = time.time()
                else:
                    face_detector.face_detected = False

    elif (time.time() - face_detector.time_face_detected) >= face_detector.wait_time:
        # Reanudar la detección de caras
        face_detector.stop_faces_detected = False

    # Actualizar el nombre en la interfaz de usuario
    if time.time() - face_detector.last_message_time < face_detector.display_time:
        st.write(face_detector.name)
        
    return img
# Actualizar la función crear_carpeta en tu código



# Cargar el estilo desde el archivo CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Llamar a la función local_css con el nombre del archivo CSS
local_css("styles.css")


# Iniciar la transmisión de la cámara en vivo y aplicar la transformación para detectar caras
face_detector = FaceDetector()
webrtc_streamer(key="example", video_transformer_factory=lambda: face_detector)
nombre_nueva_carpeta = st.text_input("Ingrese su numero de expediente")
# Agregar un botón para capturar fotogramas y crear la carpeta
if st.button("Crear Nuevo usuario"):
    if nombre_nueva_carpeta.strip() != "":
        # Verificar si el nombre es una secuencia numérica de 9 dígitos
        if re.match(r"^\d{9}$", nombre_nueva_carpeta.strip()):
            nombre_estudiante = obtener_nombre_estudiante_por_id(nombre_nueva_carpeta)
            capturar_fotogramas_y_crear_carpeta(nombre_estudiante)
        else:
            st.warning("El expediente no es correcto.")
    else:
        st.warning("Ingrese un expediente válido")



