from flask import Flask, request, Response
from deepface import DeepFace
import cv2
import base64

app = Flask(__name__)

# Esta función configura la respuesta para permitir CORS
def response_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'  # Reemplaza con la URL de tu app React
    return response

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.after_request
def after_request(response):
    return response_headers(response)

cap = cv2.VideoCapture(0)  # Inicializa la cámara

def generate_frames():
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        else:
            # Procesa el frame con DeepFace
            result = DeepFace.find(frame, db_path='Database', enforce_detection=False, model_name='Facenet512')

            if len(result) > 0 and 'identity' in result[0]:
                identity = result[0]['identity']
            else:
                identity = "No face detected"

            # Codifica el frame en base64
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = base64.b64encode(buffer).decode('utf-8')

            yield (f'--frame\r\nContent-Type: image/jpeg\r\n\r\n{frame_bytes}\r\n')

if __name__ == '__main__':
    app.run(debug=True)
