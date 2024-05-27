import customtkinter
from PIL import Image, ImageTk

import datetime
from pyowm.owm import OWM
import tkinter as tk  
from pyowm.utils.config import get_default_config
import pandas as pd
import cv2
from deepface import DeepFace
import time
import os
import numpy as np
import tensorflow as tf


capture_images = False  # Variable para controlar la captura de imágenes
capture_interval = 5  # Intervalo de tiempo entre capturas en segundos
stop_faces_detected = False 
rt =False
last_interaction_time = time.time()



model = 'liveness.model'
model = tf.keras.models.load_model(model)

configDict = get_default_config()
configDict['language'] = 'es'
owmKey = '203bce55953436d69e8b111e0105679c'

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

app = customtkinter.CTk()
screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()
app.title("Saludo LCC")
app.geometry(f"{screen_width}x{screen_height}")
app.attributes("-fullscreen", True)

cap_width = int(screen_width * 2)  
cap_height = int(screen_height * 2 )  

def capture_images_t(images_taken=0):
    global capture_images, name
    if images_taken >= 5:  # Salir si se han capturado las 5 fotos
        # Detener la captura después de tomar las 5 fotos
        capture_images = False
        countdown_label.configure(text="Captura finalizada")  # Actualiza el texto después de la captura

        # Después de 2 segundos, llama a clear_screen para limpiar la pantalla
        stop_face_detection()
        app.after(4000, clear_screen)
        start_face_detection()
        return

    for countdown in range(3, 0, -1):
        # Actualiza el contador de tiempo en la interfaz gráfica
        countdown_label.configure(text=f"{countdown}")
        app.update()
        time.sleep(1)

    countdown_label.configure(text="")  # Limpia el contador después de los 3 segundos

    # Captura una imagen y guárdala en el área del rostro detectado
    ret, frame = cap.read()
    if ret:
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml').detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if len(faces) > 0:
            x, y, w, h = faces[0]  # Obtiene las coordenadas del primer rostro detectado
            face_area = frame[y:y+h, x:x+w]  # Recorta el área del rostro
            
            # Guarda la imagen del rostro en la carpeta del usuario
            user_folder = os.path.join("Database", name)
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            image_filename = f"{timestamp}.jpg"
            image_path = os.path.join(user_folder, image_filename)

            cv2.imwrite(image_path, face_area)
            print(f"Imagen guardada en {image_path}")
            images_taken += 1  # Incrementa el contador de imágenes capturadas

        # Espera 3 segundos antes de tomar la próxima foto
        time.sleep(3)

    # Llama a capture_images_t() nuevamente después de 10 milisegundos
    app.after(10, capture_images_t, images_taken)



frame=customtkinter.CTkLabel(app,text="")
frame.grid(row=0,column=0,sticky="w",padx=50,pady=20)


def clear_screen():
    # Limpia la pantalla y vuelve a la interfaz inicial (si es necesario)
    panel.configure(image="")
    countdown_label.configure(text="")
    name_label.configure(text="Bienvenido ", font=('Arial BOLD', 18), anchor="w")
    name_label.place_forget()

    # Llama a la función para actualizar el modelo con las nuevas fotos
    update_model()

def update_model():
    # Lógica para actualizar el modelo con las nuevas fotos
    # Puedes utilizar la función de DeepFace correspondiente aquí
    os.remove("Database/representations_facenet512.pkl")
    print("Actualizando el modelo con las nuevas fotos")
    DeepFace.find(frame, db_path='Database', enforce_detection=False, model_name='Facenet512')
    return


import tkinter.ttk as ttk
def save_date(date, user_folder):
    date_file_path = os.path.join(user_folder, "fecha_nacimiento.txt")
    print(f"Fecha a guardar: {date}")
    print(f"Ruta del archivo: {date_file_path}")
    with open(date_file_path, "w") as file:
        file.write(date)
    print(f"Fecha de nacimiento guardada en {date_file_path}")

def save_date_and_close(date, user_folder, window):
    if date:
        save_date(date, user_folder)
        window.destroy()  # Cierra la ventana después de guardar la fecha
        capture_images_t()

def radiobutton_event(window, name, entry):
    global date_entry  # Hacer la variable date_entry global
    # Hacer la ventana más grande
    window.geometry("300x400")
    print("holaaaaaaa")
    # Crear un campo de entrada para la fecha de nacimiento
    date_label = customtkinter.CTkLabel(window, text="Ingresa tu fecha de nacimiento (dd/mm):")
    date_label.pack(pady=10)
    date_entry = customtkinter.CTkEntry(window)
    date_entry.pack(pady=10)

    # Botón para guardar la fecha de nacimiento
    save_button = customtkinter.CTkButton(window, text="Guardar", command=lambda: save_date_and_close(date_entry.get(), f"Database/{name}", window))
    save_button.pack(pady=10)

def create_new_user():
    global capture_images
    new_user_window = customtkinter.CTk()
    new_user_window.title("Nuevo Usuario")
    new_user_window.geometry("300x250")  
    stop_face_detection()

    label = customtkinter.CTkLabel(new_user_window, text="Introduce tu nombre:")
    label.pack(pady=10)

    entry = customtkinter.CTkEntry(new_user_window)
    entry.pack(pady=10)

    # Función para crear el usuario y guardar la fecha de nacimiento si se selecciona
    def create_user_folder():
        global name, capture_images

        name = entry.get()
        print(f"Nombre: {name}")
        if name:
            user_folder = os.path.join("Database", name)
            os.makedirs(user_folder, exist_ok=True)
            print(f"Carpeta creada para {name} en {user_folder}")

            # Captura imágenes sin hilos

            if var.get() == 1:  # Si elige "Sí"
                print("Se seleccionó 'Sí'")
                # Ejecutar el evento de radiobutton
                radiobutton_event(new_user_window, name, entry)
            else:
                capture_images_t()
                new_user_window.destroy()  # Cierra la ventana principal si no se selecciona "Sí"

    # Agrega botones de radio para seleccionar Sí o No
    var = tk.IntVar()  # Utiliza IntVar del módulo tkinter estándar
    yes_radio = customtkinter.CTkRadioButton(new_user_window, text="Sí", variable=var, value=1)
    no_radio = customtkinter.CTkRadioButton(new_user_window, text="No", variable=var, value=0)
    yes_radio.pack()
    no_radio.pack()

    create_button = customtkinter.CTkButton(new_user_window, text="Crear Usuario", command=create_user_folder)
    create_button.pack(pady=10)

    new_user_window.resizable(False, False)
    new_user_window.mainloop()

    # Cierra la ventana principal
    new_user_window.destroy()


def stop_capture():
    global capture_images
    capture_images = False

countdown_label = customtkinter.CTkLabel(app, text="", font=('Arial', 20), anchor="center")
countdown_label.place(relx=0.5, rely=0.1, anchor="center")

def update_video_panel():
    global cap,stop_faces_detected
    state, frame = cap.read()

    if not state or not(stop_faces_detected):
        return

    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    img = ImageTk.PhotoImage(image=img)
    panel.img = img
    panel.configure(image=img)
    panel.grid(row=0, column=0, columnspan=2, pady=10, sticky="nsew")
    panel.place(relx=0.5, rely=0.5, anchor="center")  # Centra el panel de video
    
    app.update_idletasks() 

    app.after(10, update_video_panel)
    

def detect_faces():
    global face_detected, time_face_detected,stop_faces_detected
    state, frame = cap.read()
    
    
    if not state or stop_faces_detected:
          # Libera los recursos de la cámara
        update_video_panel()
        name_label.place_forget()  
        return

    if not face_detected and not stop_faces_detected:

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml').detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        print("Debug - faces shape:", faces)

        if len(faces) > 0:
            print("Entro")
            res = DeepFace.find(frame, db_path='Database', enforce_detection=False, model_name='Facenet512')
            print("Debug - res:", res)
            print("Debug - asa:", res[0]['target_x'])

            # Extraer el primer diccionario de la lista
            primer_diccionario = res[0]

            # Verificar si todos los valores en el primer diccionario son mayores que cero
            todos_mayor_que_cero = all(value.iloc[0] > 0 if isinstance(value, pd.Series) and not value.empty else False for key, value in primer_diccionario.items() if key != 'identity')
            
            if todos_mayor_que_cero:
                identity_series = res[0]['identity']
                print("Pipo :",identity_series)
                if not identity_series.empty and len(identity_series) > 0:
                    photo_path = identity_series.iloc[0]
                    nombre_carpeta = os.path.basename(os.path.dirname(photo_path))
                    name = nombre_carpeta
                    print(name)
                    cv2.putText(frame, name, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    face_detected = True
                    time_face_detected = time.time()
                    name_label.configure(text=f"Bienvenido {name}")
                    name_label.place(relx=0.5, rely=0.80, anchor="center")  # Adjust rely value to control vertical position
                else:
                    face_detected = False
                    name_label.place_forget()

    else:
        print("entro1l")
        current_time = time.time()
        if not stop_faces_detected:  
            if current_time - time_face_detected >= wait_time:
             face_detected = False
             name_label.place_forget()


    update_gui(frame)
    
    
    app.after(10, detect_faces)




def update_gui(frame):
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    img = ImageTk.PhotoImage(image=img)
    panel.img = img
    panel.configure(image=img)
    panel.grid(row=0, column=0, columnspan=2, pady=10, sticky="nsew")
    panel.place(relx=0.5, rely=0.5, anchor="center")  # Centro del panel de vide


def stop_face_detection():
    global stop_faces_detected
    stop_faces_detected = True  # Toggle the variable
    

# Inicia la detección de rostros
cap = cv2.VideoCapture(0)
cap.set(3, cap_width)  # Set the width
cap.set(4, cap_height)  # Set the height
frame_count = 0
face_detected = False
time_face_detected = None
wait_time = 5  # segundos

def start_face_detection():
    global stop_faces_detected,frame_count,face_detected,time_face_detected,wait_time,cap,cap_width,cap_height
    cap.release()
    cap = cv2.VideoCapture(0)
    cap.set(3, cap_width)  # Set the width
    cap.set(4, cap_height)  # Set the height
    stop_faces_detected = False
    
    detect_faces()


panel = customtkinter.CTkLabel(app, text="")
panel.grid(row=6, column=0, columnspan=2, pady=10, sticky="nsew")

name_label = customtkinter.CTkLabel(app, text="Bienvenido ",font=('Arial BOLD',24),anchor="w")
name_label.place(relx=0.5, rely=0.80, anchor="center") 

detect_faces()

# Define el tamaño y el tipo de fuente
button_font = customtkinter.CTkFont(family='Arial', size=24)

button_width = 90
button_height = 15

start_faces_button = customtkinter.CTkButton(app, font=button_font, anchor="center", width=button_width, height=button_height, text="INICIAR DETECCION", command=start_face_detection)
start_faces_button.place(relx=0.05, rely=0.3, anchor="w")

stop_faces_button = customtkinter.CTkButton(app, font=button_font, anchor="center", width=button_width, height=button_height, text="DETENER DETECCION", command=stop_face_detection)
stop_faces_button.place(relx=0.05, rely=0.4, anchor="w")

create_memory = customtkinter.CTkButton(app, font=button_font, anchor="center", width=button_width, height=button_height, text="NUEVO USUARIO", command=create_new_user)
create_memory.place(relx=0.05, rely=0.5, anchor="w")

from moviepy.editor import VideoFileClip
import tkinter.filedialog

def play_video():
  # Ruta al video predefinido
    default_video_path = "Quibo.mp4"

    # Crea una nueva ventana para reproducir el video
    video_window = customtkinter.CTk()
    video_window.title("Reproducción de Video")
    video_window.geometry("800x600")  # Ajusta el tamaño según sea necesario

    # Carga y reproduce el video predefinido en la nueva ventana
    video_clip = VideoFileClip(default_video_path)
    video_clip.preview(fps=60)
    video_clip.close()

    # Cierra la ventana emergente después de que el video termine
    video_window.destroy()

# Agrega el botón a tu interfaz gráfica
open_video_button = customtkinter.CTkButton(app, font=button_font, anchor="center", width=button_width, height=button_height, text="Abrir Video", command=play_video)
open_video_button.place(relx=0.05, rely=0.7, anchor="w")



app.after(False, False)
app.mainloop()


#Y el corazon tucun tucun 
#ahi va