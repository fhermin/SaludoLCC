import os
import cv2
import tkinter as tk
from tkinter import filedialog
from deepface import DeepFace
import time
from PIL import Image, ImageTk

def take_photo():
    _, frame = cap.read()
    cv2.imshow("Captured Image", frame)
    cv2.imwrite("temp_image.jpg", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def add_new_image():
    take_photo()
    if os.path.exists("temp_image.jpg"):
        folder_name = filedialog.askstring("Nueva carpeta", "Ingrese el nombre de la carpeta:")
        if folder_name:
            destination_folder = os.path.join('Database', folder_name)
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)
            
            image = cv2.imread("temp_image.jpg")
            cv2.imwrite(os.path.join(destination_folder, f"new_image_{len(os.listdir(destination_folder))}.jpg"), image)
            print("Imagen añadida a la carpeta:", destination_folder)
            os.remove("temp_image.jpg")  # Elimina la imagen temporal

def detect_faces():
    global face_detected, time_face_detected

    state, frame = cap.read()

    if not state:
        root.after(10, detect_faces)
        return

    if not face_detected:
        res = DeepFace.find(frame, db_path='Database', enforce_detection=False, model_name='Facenet512')
        print("Debug - res:", res)

        if res and len(res) > 0 and 'identity' in res[0]:
            identity_series = res[0]['identity']
            
            if not identity_series.empty and len(identity_series) > 0:
                name_path = os.path.basename(identity_series.iloc[0])
                name = name_path.split('\\')[0]
                print(name)
                cv2.putText(frame, name, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                face_detected = True
                time_face_detected = time.time()
                name_label.config(text=f"Bienvenido {name}")
                name_label.pack()
            else:
                face_detected = False
                name_label.place_forget()

    else:
        current_time = time.time()
        if current_time - time_face_detected >= wait_time:
            face_detected = False
            name_label.pack_forget()

    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    img = ImageTk.PhotoImage(image=img)
    panel.img = img
    panel.config(image=img)
    root.after(10, detect_faces)


root = tk.Tk()
root.title("Detección de Rostros")

cap = cv2.VideoCapture(0)

frame_count = 0
face_detected = False
time_face_detected = None
wait_time = 5  # segundos

panel = tk.Label(root)
panel.pack(padx=10, pady=10)

name_label = tk.Label(root, text="Bienvenido ")

add_image_button = tk.Button(root, text="Tomar y Agregar Foto", command=add_new_image)
add_image_button.pack(padx=10, pady=10)

detect_faces()

def close_app():
    cap.release()
    cv2.destroyAllWindows()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close_app)
root.mainloop()
