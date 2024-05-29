import streamlit as st
import cv2
import time
import os
import datetime
import numpy as np
import re
from deepface import DeepFace
import tensorflow as tf
import firebase_admin
from firebase_admin import credentials, firestore

# Inicializar Firebase si no está ya inicializado
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("Credenciales/lcc-hub-firebase-adminsdk-bz3gx-fd6ed6c479.json")
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
else:
    print("Firebase already initialized.")

# Obtener referencia a la colección "students"
db = firestore.client()
students_ref = db.collection("students")

# Función para obtener el nombre del estudiante por ID
def obtener_nombre_estudiante_por_id(numero_ingresado):
    try:
        students_docs = students_ref.get()
        for doc in students_docs:
            if doc.id == str(numero_ingresado):
                student_data = doc.to_dict()
                name = student_data.get("name")
                cleaned_name = re.sub(r'[^a-zA-Z\s]', '', name)
                return cleaned_name.strip()
    except Exception as e:
        st.write(f"Error fetching student name: {e}")
    return None

# Función para capturar fotogramas y crear carpeta
def capturar_fotogramas_y_crear_carpeta(nombre_carpeta):
    ruta_carpeta = os.path.join("Database", nombre_carpeta)
    try:
        os.mkdir(ruta_carpeta)
        st.success(f'Se creó la carpeta "{nombre_carpeta}"')
    except FileExistsError:
        mostrar_error_mensaje(f'El usuario "{nombre_carpeta}" ya existe')
    except Exception as e:
        mostrar_error_mensaje(f"Error creating folder: {e}")

# Cargar el modelo de liveness
model = tf.keras.models.load_model('liveness.model')

# Variables globales
stop_faces_detected = False
pause_duration = 5  # Definimos la variable pause_duration
cap = None  # Definimos la variable cap para manejar la cámara

# Función para capturar imágenes
def capture_images_t(name):
    global cap
    global stop_faces_detected

    # Limpiar mensajes y vistas anteriores
    capture_message.empty()
    live_view.empty()

    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        mostrar_error_mensaje("La cámara no está abierta.")
        return

    images_taken = 0
    user_folder = os.path.join("Database", name)
    os.makedirs(user_folder, exist_ok=True)

    capture_message.write("Iniciando captura de imágenes...")

    while images_taken < 5:
        ret, frame = cap.read()
        if not ret:
            mostrar_error_mensaje("Error al capturar la imagen de la cámara.")
            break

        live_view.image(frame, channels="BGR")

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml').detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) > 0:
            x, y, w, h = faces[0]
            face_area = frame[y:y+h, x:x+w]

            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            image_filename = f"{timestamp}.jpg"
            image_path = os.path.join(user_folder, image_filename)

            cv2.imwrite(image_path, face_area)
            images_taken += 1

            time.sleep(3)

    capture_message.empty()
    capture_message.write("Captura finalizada")
    time.sleep(3)
    capture_message.empty()
    live_view.empty()  # Limpiar el marcador de posición de la vista en vivo
    stop_faces_detected = True
    if cap and cap.isOpened():
        cap.release()
        cap = None  # Asegurarse de que la cámara se libere
    time.sleep(0.1)
    st.session_state["detect_faces_running"] = False    

    update_model(frame)

# Función para actualizar el modelo con nuevas fotos
def update_model(frame):
    global stop_faces_detected
    global cap
    try:
        os.remove("Database/representations_facenet512.pkl")
    except FileNotFoundError:
        pass
    DeepFace.find(frame, db_path='Database', enforce_detection=False, model_name='Facenet512')
    stop_faces_detected = False
    if cap and cap.isOpened():
        cap.release()
        cap = None 
    time.sleep(0.1)
    st.session_state["detect_faces_running"] = True
    detect_faces()

# Función para detectar rostros
def detect_faces():
    global stop_faces_detected, frame, last_detection_time, cap

    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        mostrar_error_mensaje("No se pudo abrir la cámara.")
        return

    frame_window = st.empty()
    welcome_message = st.empty()  # Espacio reservado para el mensaje de bienvenida
    last_detection_time = time.time() - pause_duration  # Inicializa para no tener una pausa inicial

    while True:
        if stop_faces_detected:
            if cap and cap.isOpened():
                cap.release()
                cap = None  # Asegurarse de que la cámara se libere
            time.sleep(0.1)
            frame_window.empty()  # Limpiar el marcador de posición de la cámara
            welcome_message.empty()  # Limpiar el mensaje de bienvenida
            continue

        ret, frame = cap.read()
        if not ret:
            mostrar_error_mensaje("Error al capturar la imagen de la cámara.")
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml').detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        current_time = time.time()

        if len(faces) > 0 and (current_time - last_detection_time >= pause_duration):
            res = DeepFace.find(frame, db_path='Database', enforce_detection=False, model_name='Facenet512')
            identity_series = res[0]['identity']

            if not identity_series.empty and len(identity_series) > 0:
                photo_path = identity_series.iloc[0]
                name = os.path.basename(os.path.dirname(photo_path))
                last_detection_time = current_time
                welcome_message.markdown(f"**Bienvenido {name}**")

                # Dibuja un rectángulo alrededor del rostro
                x, y, w, h = faces[0]
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        frame_window.image(frame, channels="BGR")

        time.sleep(0.1)  # Ajusta este valor para controlar la velocidad de actualización

def mostrar_error_mensaje(mensaje, duracion=2):
    error_placeholder = st.error(mensaje)
    time.sleep(duracion)
    error_placeholder.empty()

# Función principal para la transmisión en vivo
def main():
    global stop_faces_detected, cap
    global capture_message, live_view

    # Incluir el CSS personalizado
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    st.title("DETECCIÓN FACIAL LCC")
    st.write("Esta es la aplicación de detección facial para LCC")

    # Inicializar marcadores de posición
    capture_message = st.empty()
    live_view = st.empty()

    # Mostrar la cámara en un espacio reservado
    frame_placeholder = st.empty()

    # Espacio para la imagen de la cámara
    frame_window = frame_placeholder.image([])

    # Colocar los controles debajo de la cámara
    st.markdown('<div class="controls-container">', unsafe_allow_html=True)
    numero_id = st.text_input("Introduce tu ID de estudiante:", key="id_input", help="Introduce tu número de identificación")
    new_user_button = st.button("Buscar y Crear Usuario", key="new_user_btn")

    if new_user_button and numero_id:
        stop_faces_detected = True  # Pausa la detección de rostros
        if cap and cap.isOpened():
            cap.release()
            cap = None  # Asegurarse de que la cámara se libere
        time.sleep(1)  # Pausa antes de buscar en la base de datos y capturar imágenes
        nombre_estudiante = obtener_nombre_estudiante_por_id(numero_id)
        if nombre_estudiante:
            user_folder_path = os.path.join("Database", nombre_estudiante)
            if not os.path.exists(user_folder_path):
                capturar_fotogramas_y_crear_carpeta(nombre_estudiante)
                capture_images_t(nombre_estudiante)
            else:
                mostrar_error_mensaje(f'El usuario "{nombre_estudiante}" ya existe')
        else:
            mostrar_error_mensaje("ID de estudiante no encontrado.")
        stop_faces_detected = False  # Reanuda la detección de rostros

    # Iniciar la detección automáticamente
    if "detect_faces_running" not in st.session_state:
        st.session_state["detect_faces_running"] = True

    if st.session_state["detect_faces_running"]:
        detect_faces()

    # Asegurarse de liberar la cámara cuando se cierra la aplicación
    if cap and cap.isOpened():
        cap.release()
        cap = None
    
if __name__ == "__main__":
    main()
