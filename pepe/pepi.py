import customtkinter
from PIL import Image, ImageTk

import datetime
from pyowm.owm import OWM

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

cap_width = int(screen_width * 0.8)  
cap_height = int(screen_height * 0.8)  

def capture_images_t():
    global capture_images,stop_faces_detected  # Add this line
    global face_detected, name
    
    stop_faces_detected = True
    images_taken = 0  # Contador de imágenes capturadas

    while capture_images and images_taken < 5:  # Cambia 5 al número deseado de imágenes
        time.sleep(3)  # Espera 3 segundos antes de cada captura

        for countdown in range(3, 0, -1):
            # Actualiza el contador de tiempo en la interfaz gráfica
            countdown_label.configure(text=f"{countdown}")
            time.sleep(1)

        countdown_label.configure(text="")  # Limpia el contador después de los 3 segundos

        # Captura una imagen y guárdala en la carpeta del usuario
        if face_detected:
            user_folder = os.path.join("Database", name)
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            image_filename = f"{timestamp}.jpg"
            image_path = os.path.join(user_folder, image_filename)

            ret, frame = cap.read()
            if ret:
                cv2.imwrite(image_path, frame)
                print(f"Imagen guardada en {image_path}")
                images_taken += 1  # Incrementa el contador de imágenes capturadas

    # Detener la captura después de tomar las 5 fotos
    capture_images = False
    countdown_label.configure(text="Captura finalizada")  # Actualiza el texto después de la captura

    # Después de 2 segundos, llama a clear_screen para limpiar la pantalla
    app.after(4000, clear_screen)




def getDateNow():
    month = int(datetime.datetime.now().month)
    day = int(datetime.datetime.now().day)
    year = int(datetime.datetime.now().year)
    month_name = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    return f"{month_name[month-1]} {day}, {year}"

weatherData = {
    'place': 'Hermosillo,MX',
    'status': 'default',
    'temp': 0,
    'heatIndex': None,
    'humidity': 0
}

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
    os.remove("pepe\Database\representations_facenet512.pkl")
    print("Actualizando el modelo con las nuevas fotos")
    DeepFace.find(frame, db_path='Database', enforce_detection=False, model_name='Facenet512')


def dynamiclabels():
    cityLabel=customtkinter.CTkLabel(frame,text=weatherData['place'],font=('Arial BOLD', 25),anchor="w",width=180)
    cityLabel.grid(row=0,column=0,sticky="w")
    dateLabel=customtkinter.CTkLabel(app,text=getDateNow(),font=('Arial', 15),anchor="center",width=200)
    dateLabel.place(relx=0.94, rely=0.025, anchor="ne")
    try:
        weatherImg=customtkinter.CTkImage(Image.open(f"weatherImages/{weatherData['status']}.png"),size=(120,120))
    except Exception as e:
        weatherImg=customtkinter.CTkImage(Image.open(f"weatherImages/default.png"),size=(120,120))
        print('image not found, default image will be selected.')
    weatherImgLabel = customtkinter.CTkLabel(app, text='', image=weatherImg, anchor="center")
    weatherImgLabel.place(relx=0.9001, rely=0.05, anchor="ne")
    weatherLabel=customtkinter.CTkLabel(frame,text=weatherData['status'],font=('Arial BOLD',15),anchor="center")
    weatherLabel.grid(row=2,column=0,columnspan=2,pady=[0,20],sticky="nsew")
    tempLabel=customtkinter.CTkLabel(frame,text=f"Temperatura: {weatherData['temp']}°(C) ",font=('Arial',12),anchor="w")
    tempLabel.grid(row=3,column=0,padx=2,pady=0,sticky="w")
    humLabel=customtkinter.CTkLabel(frame,text=f"Humedad: {weatherData['humidity']}",font=('Arial',12),anchor="w")
    humLabel.grid(row=4,column=0,padx=2,pady=0,sticky="w")
    heatLabel=customtkinter.CTkLabel(frame,text=f"Indice de calor: {weatherData['heatIndex']}",font=('Arial',12),anchor="w")
    heatLabel.grid(row=5,column=0,padx=2,pady=0,sticky="w")

dynamiclabels()

def getweather(place):
    owm=OWM(owmKey,configDict)
    mgr=owm.weather_manager()
    observation=mgr.weather_at_place(place)
    w=observation.weather
    weatherData['status']=w.detailed_status
    weatherData['temp']=w.temperature('celsius')['temp_max']
    weatherData['heatIndex']=w.heat_index
    weatherData['humidity']=w.humidity
    dynamiclabels()
    print(weatherData)

def updateWeather():
    weatherData['place']=str(placesCombo.get())
    getweather(weatherData['place'])

getweather(weatherData['place'])


def create_new_user():
    global name, capture_images, face_detected
    face_detected = True
    new_user_window = customtkinter.CTk()
    new_user_window.title("Nuevo Usuario")

    label = customtkinter.CTkLabel(new_user_window, text="Introduce tu nombre:")
    label.pack(pady=10)

    entry = customtkinter.CTkEntry(new_user_window)
    entry.pack(pady=10)

    def create_user_folder():
        global name, capture_images

        name = entry.get()
        if name:
            user_folder = os.path.join("Database", name)
            os.makedirs(user_folder, exist_ok=True)
            print(f"Carpeta creada para {name} en {user_folder}")

            # Captura imágenes sin hilos
            capture_images_t()

            new_user_window.destroy()

    create_button = customtkinter.CTkButton(new_user_window, text="Crear Usuario", command=create_user_folder)
    create_button.pack(pady=10)
    face_detected = False
    new_user_window.resizable(False, False)
    new_user_window.mainloop()

def stop_capture():
    global capture_images
    capture_images = False

countdown_label = customtkinter.CTkLabel(app, text="", font=('Arial', 20), anchor="center")
countdown_label.place(relx=0.5, rely=0.1, anchor="center")

def update_video_panel():
    global stop_faces_detected
    state, frame = cap.read()

    if not state or not stop_faces_detected:
        cap.release()
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


def phot():
    create_memory = customtkinter.CTkButton(app, font=('Arial', 12), anchor="center", width=100, text="Crear nuevo usuario", command=create_new_user)
    create_memory.place(relx=0.94, rely=0.4, anchor="ne")
    take_phot = customtkinter.CTkButton(app,font=('Arial',12),anchor="center",width=100,text="Capturar nuevas fotos")
    take_phot.place(relx=0.95, rely=0.35, anchor="ne")

def detect_faces():
    global face_detected, time_face_detected,stop_faces_detected,cap
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
                    name_label.place(relx=0.5, rely=0.85, anchor="center")  # Adjust rely value to control vertical position
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

def restart_camera():
    global cap, cap_width, cap_height
    cap.release()
    cap = cv2.VideoCapture(0)
    cap.set(3, cap_width)  # Set the width
    cap.set(4, cap_height)  # Set the height



def stop_face_detection():
    global stop_faces_detected,cap
    stop_faces_detected = True  # Toggle the variable
    
    
stop_faces_button = customtkinter.CTkButton(app, font=('Arial', 12), anchor="center", width=100, text="Detener Detección", command=stop_face_detection)
stop_faces_button.place(relx=0.95, rely=0.45, anchor="ne")

# Inicia la detección de rostros
cap = cv2.VideoCapture(0)
cap.set(3, cap_width)  # Set the width
cap.set(4, cap_height)  # Set the height
frame_count = 0
face_detected = False
time_face_detected = None
wait_time = 5  # segundos

def start_face_detection():
    global stop_faces_detected,cap
    cap.release()
    cap = cv2.VideoCapture(0)
    cap.set(3, cap_width)  # Set the width
    cap.set(4, cap_height)  # Set the height
    stop_faces_detected = False
    detect_faces()

# Crea un nuevo botón para activar la detección de caras
start_faces_button = customtkinter.CTkButton(app, font=('Arial', 12), anchor="center", width=100, text="Iniciar Detección", command=start_face_detection)
start_faces_button.place(relx=0.95, rely=0.25, anchor="ne")

panel = customtkinter.CTkLabel(app, text="")
panel.grid(row=6, column=0, columnspan=2, pady=10, sticky="nsew")

name_label = customtkinter.CTkLabel(app, text="Bienvenido ",font=('Arial BOLD',18),anchor="w")
name_label.place(relx=0.5, rely=0.85, anchor="center") 

detect_faces()
phot()



app.after(False, False)
app.mainloop()

#Y el corazon tucun tucun 
#ahi va