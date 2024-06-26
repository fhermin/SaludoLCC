import customtkinter
from PIL import Image, ImageTk
import tkinter as tk
import datetime
import cv2
import time
import os
import threading
import firebase_admin
import re
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


capture_images = False  # Variable para controlar la captura de imágenes
capture_interval = 5  # Intervalo de tiempo entre capturas en segundos

customtkinter.set_appearance_mode("dark")

root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.destroy()


app = customtkinter.CTk()
app.title("Saludo LCC")
app.geometry(f"{screen_width}x{screen_height}")

# Cargar el clasificador de cascada de Haar
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Función para comparar imágenes usando histogramas de colores
def compare_images(img1, img2):
    hist1 = cv2.calcHist([img1], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([img2], [0], None, [256], [0, 256])
    return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

# Cargar las imágenes conocidas
known_faces = []
known_names = []

def load_known_faces():
    global known_faces, known_names
    database_dir = "Database"
    for user_folder in os.listdir(database_dir):
        user_path = os.path.join(database_dir, user_folder)
        if os.path.isdir(user_path):
            for img_name in os.listdir(user_path):
                img_path = os.path.join(user_path, img_name)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    known_faces.append(img)
                    known_names.append(user_folder)

load_known_faces()


def capture_images_thread():
    global capture_images
    stop_detection()

    images_taken = 0  # Contador de imágenes capturadas
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

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
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)
                
                # Encuentra la cara más grande detectada
                largest_face = None
                largest_area = 0
                for (x, y, w, h) in faces:
                    if w * h > largest_area:
                        largest_area = w * h
                        largest_face = (x, y, w, h)
                
                if largest_face is not None:
                    x, y, w, h = largest_face
                    # Ajusta el rectángulo para capturar la cara de manera más cercada
                    face = frame[max(0, y-30):y+h+30, max(0, x-30):x+w+30]
                    resized_face = cv2.resize(face, (256, 256))  # Cambia el tamaño a 256x256 píxeles
                    cv2.imwrite(image_path, resized_face)
                    print(f"Imagen guardada en {image_path}")
                    images_taken += 1  # Incrementa el contador de imágenes capturadas

    # Detener la captura después de tomar las 5 fotos
    capture_images = False
    countdown_label.configure(text="Captura finalizada")  # Actualiza el texto después de la captura
    
    # Recargar las imágenes conocidas
    load_known_faces()
    # Recarga el modelo
    active_detection()

    # Después de 2 segundos, llama a clear_screen para limpiar la pantalla
    app.after(4000, clear_screen)


 
def getDateNow():
    month = int(datetime.datetime.now().month)
    day = int(datetime.datetime.now().day)
    year = int(datetime.datetime.now().year)
    month_name = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    return f"{month_name[month-1]} {day}, {year}"

frame = customtkinter.CTkLabel(app, text="")
frame.grid(row=0, column=0, sticky="w", padx=50, pady=20)

def clear_screen():
    # Limpia la pantalla y vuelve a la interfaz inicial (si es necesario)
    panel.configure(image="")
    countdown_label.configure(text="")
    name_label.configure(text="Bienvenido ", font=('Arial BOLD', 18), anchor="w")
    name_label.place_forget()

def dynamiclabels():
    dateLabel = customtkinter.CTkLabel(app, text=getDateNow(), font=('Arial', 15), anchor="center", width=200)
    dateLabel.place(relx=0.94, rely=0.025, anchor="ne")

dynamiclabels()

def create_new_user():
    global name, capture_images, face_detected
    face_detected = True
    new_user_window = customtkinter.CTk()
    new_user_window.title("Nuevo Usuario")

    label = customtkinter.CTkLabel(new_user_window, text="Introduce tu número de ID:")
    label.pack(pady=10)

    entry = customtkinter.CTkEntry(new_user_window)
    entry.pack(pady=10)

    def create_user_folder():
        global name, capture_images

        numero_id = entry.get()
        nombre_estudiante = obtener_nombre_estudiante_por_id(numero_id)
        
        if nombre_estudiante:
            user_folder_path = os.path.join("Database", nombre_estudiante)
            if not os.path.exists(user_folder_path):
                os.makedirs(user_folder_path, exist_ok=True)
                print(f"Carpeta creada para {nombre_estudiante} en {user_folder_path}")

                # Inicia el hilo para capturar imágenes
                name = nombre_estudiante
                capture_images = True
                capture_thread = threading.Thread(target=capture_images_thread)
                capture_thread.start()

                new_user_window.destroy()
            else:
                mostrar_error_mensaje(f'El usuario "{nombre_estudiante}" ya existe')
        else:
            mostrar_error_mensaje("ID de estudiante no encontrado.")
    
    create_button = customtkinter.CTkButton(new_user_window, text="Crear Usuario", command=create_user_folder)
    create_button.pack(pady=10)
    face_detected = False
    new_user_window.resizable(False, False)
    new_user_window.mainloop()

def mostrar_error_mensaje(mensaje):
    error_window = customtkinter.CTk()
    error_window.title("Error")
    error_label = customtkinter.CTkLabel(error_window, text=mensaje)
    error_label.pack(pady=20)
    error_button = customtkinter.CTkButton(error_window, text="OK", command=error_window.destroy)
    error_button.pack(pady=10)
    error_window.resizable(False, False)
    error_window.mainloop()


def stop_capture():
    global capture_images
    capture_images = False

countdown_label = customtkinter.CTkLabel(app, text="", font=('Arial', 20), anchor="center")
countdown_label.place(relx=0.5, rely=0.1, anchor="center")

def phot():
    create_memory = customtkinter.CTkButton(app, font=('Arial', 12), anchor="center", width=100, text="Crear nuevo usuario", command=create_new_user)
    create_memory.place(relx=0.94, rely=0.4, anchor="ne")
    take_phot = customtkinter.CTkButton(app, font=('Arial', 12), anchor="center", width=100, text="Capturar nuevas fotos")
    take_phot.place(relx=0.95, rely=0.35, anchor="ne")

def detect_faces():
    global face_detected, time_face_detected, name ,stop

    state, frame = cap.read()

    if not state:
        app.after(10, detect_faces)
        return

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    if not stop :
        if not face_detected :
            if len(faces) > 0:
                (x, y, w, h) = faces[0]
                roi_gray = gray[y:y+h, x:x+w]

                best_match_score = 0
                best_match_name = None

                for known_face, known_name in zip(known_faces, known_names):
                    score = compare_images(roi_gray, known_face)
                    if score > best_match_score:
                        best_match_score = score
                        best_match_name = known_name

                if best_match_score > 0.75 : # Umbral de coincidencia
                    name = best_match_name
                    face_detected = True
                    time_face_detected = time.time()
                    name_label.configure(text=f"Bienvenido {name}")
                    name_label.place(relx=0.5, rely=0.85, anchor="center")  # Adjust rely value to control vertical position
                else:
                    face_detected = False
                    name_label.place_forget()
        else :
                current_time = time.time() 
                if current_time - time_face_detected >= wait_time: 
                    face_detected = False
                    name_label.place_forget()


    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        if face_detected and name:
            cv2.putText(frame, f"{name}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    img = ImageTk.PhotoImage(image=img)
    panel.img = img
    panel.configure(image=img)
    panel.grid(row=0, column=0, columnspan=2, pady=10, sticky="nsew")
    panel.place(relx=0.5, rely=0.5, anchor="center")  # Center the video panel

    app.after(10, detect_faces)

def stop_detection():
    global face_detected,stop
    face_detected = True
    stop = True
    name_label.configure(text="Detección detenida")

def active_detection():
    global face_detected,stop
    face_detected = False
    stop = False


stop_button = customtkinter.CTkButton(app, text="Detener Detección", command=stop_detection)
stop_button.place(relx=0.05, rely=0.05, anchor="nw")

active_button = customtkinter.CTkButton(app, text="Activar Detección", command=active_detection)
active_button.place(relx=0.2, rely=0.05, anchor="nw")
# Start face detection
cap = cv2.VideoCapture(0)
frame_count = 0
face_detected = False
time_face_detected = None
wait_time = 5  # segundos
stop = False

panel = customtkinter.CTkLabel(app, text="")
panel.grid(row=6, column=0, columnspan=2, pady=10, sticky="nsew")

name_label = customtkinter.CTkLabel(app, text="Bienvenido ", font=('Arial BOLD', 18), anchor="w")
name_label.place(relx=0.5, rely=0.85, anchor="center")

load_known_faces()
detect_faces()
phot()

app.resizable(False, False)
app.mainloop()
