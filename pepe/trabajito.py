import asyncio
import json
from deepface import DeepFace
import cv2

model = DeepFace.find(db_path='Database', enforce_detection=False, model_name='Facenet512')

async def detect_and_send_results(websocket, path):
    cap = cv2.VideoCapture(0)  # 0 para la cámara predeterminada

    while True:
        state, frame = cap.read()
 
        if not state:
            break

        res = DeepFace.find(frame, db_path='Database', enforce_detection=False, model_name='Facenet512')

        if len(res[0]['identity']) > 0:
            name = res[0]['identity'][0].split('/')[1].split('\\')[1]
            result = {'name': name}



