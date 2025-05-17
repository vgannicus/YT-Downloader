import subprocess
import os
from tkinter import Tk, Label, Entry, Button, Checkbutton, BooleanVar, filedialog, messagebox, Toplevel, Frame, Menu
import threading

# **** NOTA: Define aquí la ruta a tu ejecutable de yt-dlp ****
RUTA_YTDLP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yt-dlp")
if not os.path.exists(RUTA_YTDLP):
    RUTA_YTDLP += ".exe"  # Intenta con la extensión .exe en Windows

# **** NOTA: Si necesitas funcionalidades que requieran ffmpeg, define su ruta aquí ****
RUTA_FFMPEG = "ffmpeg"  # Asume que ffmpeg está en el PATH del sistema, puedes cambiarlo si no lo está

def descargar_en_hilo(url, carpeta_descarga, formatos, progreso_ventana):
    """Ejecuta la descarga de yt-dlp en un hilo separado."""
    descarga_exitosa = True
    for formato in formatos:
        comando = [RUTA_YTDLP, url, "-o", os.path.join(carpeta_descarga, f"%(title)s.{formato}")]

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
        except subprocess.CalledProcessError as e:
            messagebox.showerror(f"Error al descargar {formato}", e.stderr)
            descarga_exitosa = False
            break  # Detener si hay un error
        except FileNotFoundError:
            messagebox.showerror("Error", f"No se encontró yt-dlp en la ruta especificada en el código: {RUTA_YTDLP}")
            descarga_exitosa = False
            break  # Detener si no se encuentra yt-dlp

    progreso_ventana.destroy()  # Cerrar la ventana de progreso
    descargar_button.config(state='normal')  # Habilitar el botón de nuevo
    if descarga_exitosa:
        insert_placeholder_url() # Limpiar y restablecer el placeholder de la URL

def iniciar_descarga():
    """Recopila la información de la GUI y inicia la descarga en un hilo con ventana de progreso, con validaciones."""
    url_valor = url_entry.get()
    carpeta_descarga_valor = carpeta_descarga_entry.get()
    descargar_mp4 = descargar_mp4_var.get()
    descargar_mp3 = descargar_mp3_var.get()

    if not os.path.exists(RUTA_YTDLP):
        messagebox.showerror("Error", f"No se encontró yt-dlp en la ruta definida en el código: {RUTA_YTDLP}.\n"
                                        "Asegúrate de que el archivo exista en esa ubicación.")
        return

    if url_valor == "Ingrese URL de YouTube" or not url_valor:
        messagebox.showerror("Error", "Por favor, ingresa la URL del video de YouTube.")
        return

    # Validar si la URL es de YouTube (esta validación podría necesitar ajuste si el placeholder está presente)
    if "youtube.com" not in url_valor and "youtu.be" not in url_valor:
        messagebox.showerror("Error", "La URL ingresada no parece ser de YouTube.")
        return

    # Validar la longitud de la URL
    if len(url_valor) > 43 and url_valor != "Ingrese URL de YouTube":
        messagebox.showerror("Error", "La URL no puede tener más de 43 caracteres.")
        url_entry.delete(0, 'end')  # Limpiar el campo de URL
        insert_placeholder_url() # Reinsertar el placeholder
        return

    if not carpeta_descarga_valor:
        messagebox.showerror("Error", "Por favor, selecciona una carpeta de descarga.")
        return

    formatos_seleccionados = []
    if descargar_mp4:
        formatos_seleccionados.append("mp4")
    if descargar_mp3:
        formatos_seleccionados.append("mp3")

    if not formatos_seleccionados:
        messagebox.showerror("Error", "Por favor, selecciona al menos un formato de descarga (MP4 o MP3).")
        return

    # Deshabilitar el botón de descarga para evitar múltiples ejecuciones
    descargar_button.config(state='disabled')

    # Crear una ventana de "En progreso..."
    progreso_ventana = Toplevel(ventana)
    progreso_ventana.title("Descarga en progreso")
    Label(progreso_ventana, text="Descargando... Por favor, espera.").pack(padx=20, pady=20)
    progreso_ventana.grab_set()  # Hacer que esta ventana sea modal (bloquea la ventana principal)
    ventana.withdraw() # Ocultar la ventana principal

    # Crear y iniciar el hilo de descarga
    hilo_descarga = threading.Thread(target=descargar_en_hilo, args=(url_valor, carpeta_descarga_valor, formatos_seleccionados, progreso_ventana))
    hilo_descarga.start()

    # Hacer que la ventana de progreso sea la principal hasta que se cierre
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
    if not url_entry.get():
        insert_placeholder_url()

def insert_placeholder_url():
    """Inserta el texto de placeholder en el campo de URL."""
    url_entry.delete(0, 'end') # Primero limpiar cualquier texto que pudiera haber
    url_entry.insert(0, "Ingrese URL de YouTube")
    url_entry.config(fg='grey') # Cambiar el color del texto a gris para indicar placeholder

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

# Checkbuttons para seleccionar los formatos de descarga
formato_label = Label(ventana, text="Formatos de descarga:")
formato_label.grid(row=2, column=0, padx=5, pady=5, sticky='w')

descargar_mp4_var = BooleanVar()
mp4_checkbutton = Checkbutton(ventana, text="MP4 (Video)", variable=descargar_mp4_var)
mp4_checkbutton.grid(row=2, column=1, padx=5, pady=5, sticky='w')

descargar_mp3_var = BooleanVar()
mp3_checkbutton = Checkbutton(ventana, text="MP3 (Audio)", variable=descargar_mp3_var)
mp3_checkbutton.grid(row=3, column=1, padx=5, pady=5, sticky='w')

# Botón de descarga (ahora llama a iniciar_descarga)
descargar_button = Button(ventana, text="Descargar", command=iniciar_descarga)
descargar_button.grid(row=4, column=0, columnspan=3, padx=5, pady=10, sticky='ew')

# Configuración de las columnas para que se expandan bien
ventana.grid_columnconfigure(1, weight=1)
ventana.grid_columnconfigure(2, weight=0) # El botón "Seleccionar" no necesita expandirse

ventana.mainloop()