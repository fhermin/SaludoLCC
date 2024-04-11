import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
import time
import os
import pandas as pd
from deepface import DeepFace

# Definir una clase para transformar el video
class FaceDetector(VideoTransformerBase):
    wait_time = 5  # Tiempo de espera en segundos
    display_time = 3  # Tiempo de visualización del nombre en segundos

    def _init_(self):
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
                        print(self.name)
                        st.write(self.name)
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

# Función principal
def main():
    st.title("Detector de Caras en Tiempo Real")

    # Iniciar la transmisión de la cámara en vivo y aplicar la transformación para detectar caras
    webrtc_streamer(key="example", video_transformer_factory=FaceDetector)

if _name_ == "_main_":
    main()
