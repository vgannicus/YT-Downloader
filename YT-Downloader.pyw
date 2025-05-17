import subprocess
import os
from tkinter import Tk, Label, Entry, Button, Radiobutton, StringVar, filedialog, messagebox, Toplevel, Menu
import threading
import re

# **** NOTA: Define aquí la ruta a tu ejecutable de yt-dlp ****
RUTA_YTDLP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yt-dlp")
if not os.path.exists(RUTA_YTDLP):
    RUTA_YTDLP += ".exe"  # Intenta con la extensión .exe en Windows

# **** NOTA: Si necesitas funcionalidades que requieran ffmpeg, define su ruta aquí ****
RUTA_FFMPEG = "ffmpeg"  # Asume que ffmpeg está en el PATH del sistema, puedes cambiarlo si no lo está

def archivo_existe(carpeta, nombre_base, extension):
    """Verifica si un archivo con un nombre base y extensión ya existe en la carpeta."""
    nombre_archivo = f"{nombre_base}.{extension}"
    ruta_completa = os.path.join(carpeta, nombre_archivo)
    return os.path.exists(ruta_completa)

def obtener_nombre_base(url):
    """Obtiene el nombre base del video desde yt-dlp sin descargarlo."""
    comando = [RUTA_YTDLP, "--get-filename", "-o", "%(title)s", url]
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        return resultado.stdout.strip()
    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        messagebox.showerror("Error", f"No se encontró yt-dlp en la ruta especificada: {RUTA_YTDLP}")
        return None

def ejecutar_descarga(url, carpeta_descarga, formato, progreso_ventana):
    """Ejecuta la descarga de yt-dlp para el formato seleccionado."""
    nombre_base = obtener_nombre_base(url)
    if not nombre_base:
        messagebox.showerror("Error", "No se pudo obtener el nombre del video.")
        return False

    extension = "mp4" if formato == "mp4" else "mp3"
    if archivo_existe(carpeta_descarga, nombre_base, extension):
        messagebox.showinfo("Descarga omitida", f"Ya existe un archivo con el nombre '{nombre_base}.{extension}' en la carpeta de descarga.")
        return True  # Se considera "exitoso" porque no hubo error, solo se omitió

    comando = [RUTA_YTDLP, url, "-o", os.path.join(carpeta_descarga, f"{nombre_base}.%(ext)s")]
    if formato == "mp3":
        comando.extend(["-x", "--audio-format", "mp3"])

    print(f"Ejecutando para {formato}: {' '.join(comando)}")

    try:
        # Ocultar la ventana de la consola de yt-dlp en Windows
        startupinfo_ytdlp = None
        if os.name == 'nt':
            startupinfo_ytdlp = subprocess.STARTUPINFO()
            startupinfo_ytdlp.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo_ytdlp.wShowWindow = subprocess.SW_HIDE

        resultado = subprocess.run(comando, capture_output=True, text=True, check=True, startupinfo=startupinfo_ytdlp)
        print(f"Descarga de {formato} completada exitosamente.")
        print(resultado.stdout)
        return True
    except subprocess.CalledProcessError as e:
        messagebox.showerror(f"Error al descargar {formato}", e.stderr)
        return False
    except FileNotFoundError:
        messagebox.showerror("Error", f"No se encontró yt-dlp en la ruta especificada en el código: {RUTA_YTDLP}")
        return False

def descargar_en_hilo(url, carpeta_descarga, formato_seleccionado, progreso_ventana):
    """Ejecuta la descarga de yt-dlp en un hilo separado para el formato seleccionado."""
    descarga_exitosa = ejecutar_descarga(url, carpeta_descarga, formato_seleccionado, progreso_ventana)

    progreso_ventana.destroy()  # Cerrar la ventana de progreso
    descargar_button.config(state='normal')  # Habilitar el botón de nuevo
    if descarga_exitosa:
        insert_placeholder_url() # Limpiar y restablecer el placeholder de la URL

def validar_url_youtube(url):
    """Valida si la URL proporcionada parece ser de YouTube."""
    patron_youtube = re.compile(r'(https?://)?(www\.)?(youtube|youtu\.be)\.(com)?/?.*(?:watch\?v=)?([\w-]{11})')
    return bool(patron_youtube.match(url))

def iniciar_descarga():
    """Recopila la información de la GUI, valida la entrada y comienza la descarga en un hilo con ventana de progreso."""
    url_valor = url_entry.get().strip()
    carpeta_descarga_valor = carpeta_descarga_entry.get().strip()
    formato_seleccionado = formato_var.get()

    if not os.path.exists(RUTA_YTDLP):
        messagebox.showerror("Error", f"No se encontró yt-dlp en la ruta definida:\n{RUTA_YTDLP}.\n"
                                        "Asegúrate de que el archivo exista en esa ubicación.")
        return

    if url_valor == "Ingrese URL de YouTube" or not url_valor:
        messagebox.showerror("Error", "Por favor, ingresa la URL del video de YouTube.")
        return

    if not validar_url_youtube(url_valor):
        messagebox.showerror("Error", "La URL ingresada no parece ser una URL válida de YouTube.")
        return

    if not carpeta_descarga_valor:
        messagebox.showerror("Error", "Por favor, selecciona una carpeta de descarga.")
        return

    if not formato_seleccionado:
        messagebox.showerror("Error", "Por favor, selecciona un formato de descarga (MP4 o MP3).")
        return

    # Deshabilitar el botón de descarga para evitar múltiples ejecuciones
    descargar_button.config(state='disabled')

    # Crear una ventana de "En progreso..."
    progreso_ventana = Toplevel(ventana)
    progreso_ventana.title("Descarga en progreso")
    Label(progreso_ventana, text="Verificando y descargando... Por favor, espera.").pack(padx=20, pady=20)
    progreso_ventana.grab_set()  # Hacer que esta ventana sea modal
    ventana.withdraw() # Ocultar la ventana principal

    # Crear e iniciar el hilo de descarga
    hilo_descarga = threading.Thread(target=descargar_en_hilo, args=(url_valor, carpeta_descarga_valor, formato_seleccionado, progreso_ventana))
    hilo_descarga.start()

    # Esperar a que el hilo de descarga termine y luego mostrar la ventana principal
    ventana.wait_window(progreso_ventana)
    ventana.deiconify() # Mostrar la ventana principal de nuevo

def seleccionar_carpeta():
    """Abre un diálogo para seleccionar la carpeta de descarga y actualiza el campo de entrada."""
    carpeta = filedialog.askdirectory(title="Selecciona la carpeta de descarga")
    if carpeta:
        carpeta_descarga_entry.delete(0, 'end')
        carpeta_descarga_entry.insert(0, carpeta)

def focus_in_url(event):
    """Borra el placeholder de la URL al recibir el foco."""
    if url_entry.get() == "Ingrese URL de YouTube":
        url_entry.delete(0, 'end')
        url_entry.config(fg='black') # Cambiar el color del texto a negro

def focus_out_url(event):
    """Reinserta el placeholder de la URL al perder el foco si el campo está vacío."""
    if not url_entry.get().strip():
        insert_placeholder_url()

def insert_placeholder_url():
    """Inserta el texto de placeholder en el campo de URL."""
    url_entry.delete(0, 'end') # Primero limpiar cualquier texto
    url_entry.insert(0, "Ingrese URL de YouTube")
    url_entry.config(fg='grey') # Cambiar el color del texto a gris para placeholder

def mostrar_menu_contextual_url(event):
    """Muestra el menú contextual para el campo de URL."""
    menu_url.post(event.x_root, event.y_root)

def pegar_url():
    """Pega el contenido del portapapeles en el campo de URL."""
    try:
        texto = ventana.clipboard_get()
        url_entry.insert('insert', texto)
    except Exception as e:
        messagebox.showerror("Error al pegar", f"No se pudo acceder al portapapeles: {e}")

def cortar_url():
    """Corta el texto seleccionado del campo de URL y lo copia al portapapeles."""
    try:
        seleccion = url_entry.selection_get()
        ventana.clipboard_clear()
        ventana.clipboard_append(seleccion)
        url_entry.delete(url_entry.selection_start(), url_entry.selection_end())
    except:
        pass # No hay selección

# Configuración de la ventana principal
ventana = Tk()
ventana.title("Descargar desde YouTube (yt-dlp)")
ventana.resizable(False, False) # Impedir el redimensionamiento de la ventana

# Crear el menú contextual para el campo de URL
menu_url = Menu(ventana, tearoff=0)
menu_url.add_command(label="Cortar", command=cortar_url) # Agregar la opción Cortar
menu_url.add_command(label="Pegar", command=pegar_url)

# Etiqueta y entrada para la URL del video
url_label = Label(ventana, text="URL del video:")
url_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
url_entry = Entry(ventana, width=50)
url_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
insert_placeholder_url() # Insertar el placeholder inicial
url_entry.bind("<FocusIn>", focus_in_url)
url_entry.bind("<FocusOut>", focus_out_url)
url_entry.bind("<Button-3>", mostrar_menu_contextual_url) # Asociar el clic derecho al menú

# Sección para la carpeta de descarga directamente en el grid
carpeta_descarga_label = Label(ventana, text="Carpeta de descarga:")
carpeta_descarga_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')
carpeta_descarga_entry = Entry(ventana, width=40)
carpeta_descarga_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
seleccionar_carpeta_button = Button(ventana, text="Seleccionar", command=seleccionar_carpeta)
seleccionar_carpeta_button.grid(row=1, column=2, padx=5, pady=5, sticky='ew')

# Radiobuttons para seleccionar el formato de descarga
formato_label = Label(ventana, text="Formato de descarga:")
formato_label.grid(row=2, column=0, padx=5, pady=5, sticky='w')

formato_var = StringVar(value="") # Variable para almacenar el formato seleccionado

mp4_radiobutton = Radiobutton(ventana, text="MP4 (Video)", variable=formato_var, value="mp4")
mp4_radiobutton.grid(row=2, column=1, padx=5, pady=5, sticky='w')

mp3_radiobutton = Radiobutton(ventana, text="MP3 (Audio)", variable=formato_var, value="mp3")
mp3_radiobutton.grid(row=3, column=1, padx=5, pady=5, sticky='w')

# Botón de descarga (ahora llama a iniciar_descarga)
descargar_button = Button(ventana, text="Descargar", command=iniciar_descarga)
descargar_button.grid(row=4, column=0, columnspan=3, padx=5, pady=10, sticky='ew')

# Configuración de las columnas para que se expandan bien
ventana.grid_columnconfigure(1, weight=1)
ventana.grid_columnconfigure(2, weight=0) # El botón "Seleccionar" no necesita expandirse

ventana.mainloop()