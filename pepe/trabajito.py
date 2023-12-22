import asyncio
import websockets
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
            await websocket.send(json.dumps(result))

start_server = websockets.serve(detect_and_send_results, "localhost", 1900)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
