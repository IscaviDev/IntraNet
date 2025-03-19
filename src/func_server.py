# ------------------------- GOOGLE DRIVE API -------------------------#


# import flet as ft
# import pandas as pd
# import ast
# from google.oauth2.service_account import Credentials
# from googleapiclient.discovery import build
# from googleapiclient.http import MediaIoBaseUpload
# from io import BytesIO  # Usamos BytesIO en lugar de StringIO

# # Autenticación con Google Drive
# SCOPES = ["https://www.googleapis.com/auth/drive"]
# creds = Credentials.from_service_account_file(
#     "./storage/credentials.json", scopes=SCOPES)
# # creds = Credentials.from_service_account_file(
# #     "credentials.json", scopes=SCOPES)
# drive_service = build("drive", "v3", credentials=creds)

# # ID del archivo CSV en Google Drive
# FILE_ID = "1PaKYHC8yIXIYQe2JJMXooWwzp3iJ7puC"


# def leer_csv():
#     """Lee el archivo CSV desde Google Drive"""
#     request = drive_service.files().get_media(fileId=FILE_ID)
#     csv_data = request.execute().decode("utf-8")
#     # Usamos BytesIO aquí para manejar los datos en bytes
#     df = pd.read_csv(BytesIO(csv_data.encode('utf-8')))
#     return df


# def escribir_csv(df):
#     """Sube el archivo CSV modificado a Google Drive"""
#     output = BytesIO()  # Usamos BytesIO para trabajar con datos en bytes
#     df.to_csv(output, index=False)
#     output.seek(0)

#     # Definir los metadatos del archivo (nombre)
#     file_metadata = {"name": "archivo_modificadov2.csv"}

#     # Crear el cuerpo del archivo para la carga usando MediaIoBaseUpload
#     media = MediaIoBaseUpload(output, mimetype="text/csv", resumable=True)

#     # Actualizar el archivo en Google Drive con los metadatos y el contenido
#     drive_service.files().update(fileId=FILE_ID, body=file_metadata,
#                                  media_body=media).execute()


# def upload_users(table):
#     columns = table.columns  # Nombres de las columnas del DataFrame
#     processed_rows = []  # Lista para almacenar las filas procesadas como diccionarios
#     unique_rows = []  # Lista para almacenar filas únicas sin duplicados
#     # Recorre cada fila del DataFrame y construye un diccionario para cada una
#     for index in table.index:
#         row_dict = {}  # Nuevo diccionario para cada fila
#         for column in columns:
#             value = table.at[index, column]
#             # Convierte strings con formato de lista en listas reales
#             if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
#                 try:
#                     value = ast.literal_eval(value)
#                 except (ValueError, SyntaxError):
#                     pass  # Si no se puede interpretar, dejar como está
#             elif isinstance(value, str) and value.startswith('{') and value.endswith('}'):
#                 try:
#                     value = ast.literal_eval(value)
#                 except (ValueError, SyntaxError):
#                     pass  # Si no se puede interpretar, dejar como está
#             row_dict[column] = value
#         # Añade el diccionario a la lista procesada
#         processed_rows.append(row_dict)
#     # Elimina duplicados basándose en el contenido de los diccionarios
#     for row in processed_rows:
#         if row not in unique_rows:
#             unique_rows.append(row)

#     return unique_rows


# def main(page: ft.Page):
#     page.title = "Editor CSV en Google Drive"

#     # Leer el CSV al inicio
#     df = leer_csv()

#     a = upload_users(df)
#     print(a)
#     # print("Datos del archivo CSV en Google Drive:")
#     # print(df)
#     # # for i in df["parent_id"]:
#     # #     print(i)
#     # print(df["parent_id"])
#     # lista_diccionarios = df.to_dict('records')
#     # # lista = ast.literal_eval(lista_diccionarios)
#     # print("\n\n\n", lista_diccionarios)

#     def agregar_dato(e):
#         """Añadir una nueva fila al CSV"""
#         nueva_fila = {"parent_id": "Test App", "alumn_id": "Ha funcionado"}
#         df.loc[len(df)] = nueva_fila
#         escribir_csv(df)
#         resultado.value = "CSV actualizado en Google Drive"
#         page.update()

#     boton = ft.ElevatedButton("Agregar fila al CSV", on_click=agregar_dato)
#     resultado = ft.Text("")

#     page.add(boton, resultado)


# ft.app(target=main)

# ---------------------------------------------- SABER ID ---------------------------------------------- #
from io import BytesIO  # Usamos BytesIO en lugar de StringIO
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import ast
import pandas as pd
import flet as ft
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Configuración de la API
SCOPES = ["https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(
    './storage/credentials.json', scopes=SCOPES)
service = build('drive', 'v3', credentials=creds)

# Nombre del archivo que quieres buscar
file_name = "Classes.csv"  # 🔹 Cambia esto por el nombre que buscas

# Realizar la búsqueda en Google Drive
query = f"name = '{file_name}'"
results = service.files().list(q=query, fields="files(id, name)").execute()
files = results.get('files', [])

# Mostrar resultados
if not files:
    print(f'❌ No se encontraron archivos con el nombre "{file_name}".')
else:
    for file in files:
        print(f"✅ Archivo encontrado: {file['name']} - ID: {file['id']}")


def obtener_permisos_carpeta(folder_id):
    """Lista los permisos de una carpeta en Google Drive"""
    try:
        permisos = service.permissions().list(fileId=folder_id).execute()

        print(f"📜 Permisos de la carpeta ({folder_id}):")
        for permiso in permisos.get('permissions', []):
            print(
                f"- Tipo: {permiso['type']}, Rol: {permiso['role']}, Email: {permiso.get('emailAddress', 'N/A')}")

    except Exception as e:
        print(
            f"❌ No se pueden obtener permisos de la carpeta ({folder_id}): {e}")


# 🔹 Ejemplo de uso
obtener_permisos_carpeta("1rwADwSr-_gFeEOhXjrqfAOY3HPeQMqHk")


def verificar_acceso_carpeta(folder_id):
    """Verifica si se tiene acceso a una carpeta en Google Drive"""
    try:
        # Intentar listar archivos dentro de la carpeta
        results = service.files().list(
            q=f"'{folder_id}' in parents",
            fields="files(id, name)",
            pageSize=1
        ).execute()

        files = results.get("files", [])
        if files:
            print(f"✅ Tienes acceso a la carpeta ({folder_id}).")
            return True
        else:
            print(
                f"⚠️ La carpeta ({folder_id}) está vacía o no tienes acceso.")
            return False

    except Exception as e:
        print(f"❌ No tienes acceso a la carpeta ({folder_id}): {e}")
        return False


# 🔹 Ejemplo de uso
verificar_acceso_carpeta("1rwADwSr-_gFeEOhXjrqfAOY3HPeQMqHk")


def compartir_carpeta_con_usuario(folder_id, user_email):
    """Otorga acceso a un usuario específico a una carpeta en Google Drive"""
    permiso = {
        'type': 'user',  # Usuario específico
        # Puede editar (cambiar a 'reader' si solo quieres que vea)
        'role': 'writer',
        'emailAddress': user_email
    }

    try:
        service.permissions().create(
            fileId=folder_id,
            body=permiso,
            sendNotificationEmail=True  # Enviará un correo notificando al usuario
        ).execute()
        print(f"✅ Se ha compartido la carpeta con {user_email}")
    except Exception as e:
        print(f"❌ Error al compartir la carpeta: {e}")


# 🔹 Ejemplo de uso
folder_id = "1rwADwSr-_gFeEOhXjrqfAOY3HPeQMqHk"
user_email = "taborservice@taborapptest.iam.gserviceaccount.com"
compartir_carpeta_con_usuario(folder_id, user_email)

# SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
creds = Credentials.from_service_account_file(
    "./storage/credentials.json", scopes=SCOPES)
service = build("drive", "v3", credentials=creds)

# Listar los archivos en Drive
results = service.files().list(
    pageSize=10, fields="files(id, name)").execute()

files = results.get('files', [])

if not files:
    print("No se encontraron archivos.")
else:
    for file in files:
        print(f"Archivo: {file['name']} - ID: {file['id']}")


def verificar_permisos_carpeta(folder_id):
    """Lista los permisos de la carpeta en Google Drive"""
    try:
        permisos = service.permissions().list(
            fileId=folder_id, fields="permissions").execute()
        print("📂 Permisos de la carpeta:")
        for p in permisos.get("permissions", []):
            print(f"➡ {p}")
    except Exception as e:
        print(f"❌ Error al verificar permisos: {e}")


# Reemplaza con tu folder_id
FOLDER_ID = "1rwADwSr-_gFeEOhXjrqfAOY3HPeQMqHk"
verificar_permisos_carpeta(FOLDER_ID)


def subir_archivo(file_path, file_name, folder_id):
    file_metadata = {
        "name": file_name,
        "parents": [folder_id]  # Especificamos la carpeta donde se subirá
    }
    media = MediaFileUpload(file_path, mimetype="application/pdf")

    try:
        archivo = service.files().create(
            body=file_metadata, media_body=media, fields="id").execute()
        print(f"✅ Archivo subido con éxito: {archivo['id']}")
    except Exception as e:
        print(f"❌ Error al subir el archivo: {e}")


# Reemplaza con el ID de la carpeta correcta
FOLDER_ID = "1rwADwSr-_gFeEOhXjrqfAOY3HPeQMqHk"
# subir_archivo(r"C:\Users\32icv\Desktop\SMX\SMX2\Espai d'habilitats\EH7\A5\INFORME_EH7_A5_Isaac_castillo_vidal.pdf",
#               "INFORME_EH7_A5_Isaac_castillo_vidal.pdf", FOLDER_ID)


# Configuración de la API
# SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
creds = Credentials.from_service_account_file(
    './storage/credentials.json', scopes=SCOPES)
service = build('drive', 'v3', credentials=creds)


def obtener_id_subcarpeta(carpeta_padre_id, nombre_subcarpeta):
    # Realizar la búsqueda de la subcarpeta dentro de la carpeta padre
    query = f"'{carpeta_padre_id}' in parents and name = '{nombre_subcarpeta}' and mimeType = 'application/vnd.google-apps.folder'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])

    if not folders:
        print(
            f"No se encontró la subcarpeta '{nombre_subcarpeta}' dentro de la carpeta con ID: {carpeta_padre_id}")
        return None
    else:
        # Si se encuentra, devolver el ID de la subcarpeta
        for folder in folders:
            print(
                f"Subcarpeta encontrada: {folder['name']} - ID: {folder['id']}")
            return folder['id']


# Ejemplo de uso
# Reemplaza con el ID de la carpeta que contiene la subcarpeta
carpeta_padre_id = "1kVHZJm-j-Vn_AVyUDHScfg3kHI2_EyX0"
nombre_subcarpeta = "Circulars"  # Nombre de la subcarpeta que buscas

# Obtener el ID de la subcarpeta
subcarpeta_id = obtener_id_subcarpeta(carpeta_padre_id, nombre_subcarpeta)

if subcarpeta_id:
    print(f"ID de la subcarpeta encontrada: {subcarpeta_id}")
else:
    print("No se encontró la subcarpeta.")
# import flet as ft
# import pandas as pd
# import ast
# from google.oauth2.service_account import Credentials
# from googleapiclient.discovery import build
# from googleapiclient.http import MediaFileUpload
# from io import BytesIO
# from googleapiclient.errors import HttpError

# # Autenticación con Google Drive
# SCOPES = ["https://www.googleapis.com/auth/drive"]
# creds = Credentials.from_service_account_file(
#     "./storage/credentials.json", scopes=SCOPES)
# drive_service = build("drive", "v3", credentials=creds)

# # ID del archivo CSV en Google Drive
# FILE_ID = "1PaKYHC8yIXIYQe2JJMXooWwzp3iJ7puC"


# def leer_csv():
#     """Lee el archivo CSV desde Google Drive"""
#     request = drive_service.files().get_media(fileId=FILE_ID)
#     csv_data = request.execute().decode("utf-8")
#     df = pd.read_csv(BytesIO(csv_data.encode('utf-8')))
#     return df


# def escribir_csv(df):
#     """Sube el archivo CSV modificado a Google Drive"""
#     output = BytesIO()  # Usamos BytesIO para trabajar con datos en bytes
#     df.to_csv(output, index=False)
#     output.seek(0)

#     # Definir los metadatos del archivo (nombre)
#     file_metadata = {"name": "archivo_modificadov2.csv"}

#     # Crear el cuerpo del archivo para la carga usando MediaIoBaseUpload
#     media = MediaFileUpload(output, mimetype="text/csv", resumable=True)

#     # Actualizar el archivo en Google Drive con los metadatos y el contenido
#     drive_service.files().update(fileId=FILE_ID, body=file_metadata,
#                                  media_body=media).execute()


# def compartir_archivo_con_enlace(file_id):
#     """Hacer el archivo accesible con el enlace"""
#     permiso = {
#         'type': 'anyone',  # Cualquier persona
#         'role': 'reader'   # Solo lectura
#     }

#     drive_service.permissions().create(
#         fileId=file_id,
#         body=permiso
#     ).execute()

#     print("Archivo ahora es accesible con el enlace")


# def upload_users(table):
#     columns = table.columns  # Nombres de las columnas del DataFrame
#     processed_rows = []  # Lista para almacenar las filas procesadas como diccionarios
#     unique_rows = []  # Lista para almacenar filas únicas sin duplicados
#     # Recorre cada fila del DataFrame y construye un diccionario para cada una
#     for index in table.index:
#         row_dict = {}  # Nuevo diccionario para cada fila
#         for column in columns:
#             value = table.at[index, column]
#             # Convierte strings con formato de lista en listas reales
#             if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
#                 try:
#                     value = ast.literal_eval(value)
#                 except (ValueError, SyntaxError):
#                     pass  # Si no se puede interpretar, dejar como está
#             elif isinstance(value, str) and value.startswith('{') and value.endswith('}'):
#                 try:
#                     value = ast.literal_eval(value)
#                 except (ValueError, SyntaxError):
#                     pass  # Si no se puede interpretar, dejar como está
#             row_dict[column] = value
#         # Añade el diccionario a la lista procesada
#         processed_rows.append(row_dict)
#     # Elimina duplicados basándose en el contenido de los diccionarios
#     for row in processed_rows:
#         if row not in unique_rows:
#             unique_rows.append(row)

#     return unique_rows


# def subir_y_compartir_archivo(file_path, file_name):
#     """Sube un archivo a Google Drive y lo hace accesible con el enlace"""
#     # Subir el archivo
#     media = MediaFileUpload(file_path, mimetype="application/pdf")
#     file_metadata = {'name': file_name}

#     archivo_subido = drive_service.files().create(
#         body=file_metadata, media_body=media).execute()

#     # Obtener el ID del archivo subido
#     file_id = archivo_subido['id']
#     print(f"Archivo subido con ID: {file_id}")

#     # Hacerlo accesible con el enlace
#     compartir_archivo_con_enlace(file_id)

#     return file_id


# def main(page: ft.Page):
#     page.title = "Editor CSV en Google Drive"

#     # Leer el CSV al inicio
#     df = leer_csv()

#     a = upload_users(df)
#     print(a)

#     def agregar_dato(e):
#         """Añadir una nueva fila al CSV"""
#         nueva_fila = {"parent_id": "Test App", "alumn_id": "Ha funcionado"}
#         df.loc[len(df)] = nueva_fila
#         escribir_csv(df)
#         resultado.value = "CSV actualizado en Google Drive"
#         page.update()

#     def cargar_archivo_pdf(e):
#         """Sube un archivo PDF desde el dispositivo y lo hace accesible"""
#         # Usar un file picker para seleccionar el archivo
#         file_picker = ft.FilePicker(on_result=lambda e: subir_y_compartir_archivo(
#             e.files[0].path, e.files[0].name))
#         page.add(file_picker)
#         file_picker.pick_files()

#     boton_cargar_pdf = ft.ElevatedButton(
#         "Cargar archivo PDF", on_click=cargar_archivo_pdf)
#     boton_agregar_fila = ft.ElevatedButton(
#         "Agregar fila al CSV", on_click=agregar_dato)

#     resultado = ft.Text("")

#     page.add(boton_cargar_pdf, boton_agregar_fila, resultado)


# ft.app(target=main)


# Autenticación con Google Drive
# SCOPES = ["https://www.googleapis.com/auth/drive"]
# creds = Credentials.from_service_account_file(
#     "./storage/credentials.json", scopes=SCOPES)
# drive_service = build("drive", "v3", credentials=creds)

# # Función para compartir el archivo con el enlace y los propietarios


# def compartir_archivo_con_enlace(file_id, emails_propietarios):
#     """Hacer el archivo accesible con el enlace y compartirlo con propietarios"""
#     permiso = {
#         'type': 'anyone',  # Cualquier persona
#         'role': 'reader'   # Solo lectura
#     }

#     # Crear el permiso de acceso público con enlace
#     drive_service.permissions().create(
#         fileId=file_id,
#         body=permiso
#     ).execute()

#     # Ahora compartimos el archivo con los propietarios específicos por su email
#     for email in emails_propietarios:
#         permiso_propietario = {
#             'type': 'user',  # Tipo de permiso para un usuario específico
#             'role': 'reader',  # Rol de propietario
#             'emailAddress': email,
#             # 'transferOwnership': True  # Habilita la transferencia de propiedad
#         }

#         try:
#             drive_service.permissions().create(
#                 fileId=file_id,
#                 body=permiso_propietario
#             ).execute()
#             print(f"Archivo compartido con el propietario: {email}")
#         except HttpError as error:
#             print(f"No se pudo compartir con {email}: {error}")

#     print("Archivo ahora es accesible con el enlace y con los propietarios.")

# # Función para subir un archivo PDF y compartirlo


# def subir_y_compartir_archivos(files, emails_propietarios, folder_id):
#     """Sube múltiples archivos PDF a una carpeta de Google Drive, los comparte y transfiere propiedad"""

#     file_ids = []  # Lista para almacenar los IDs de los archivos subidos

#     for file in files:
#         file_path = file.path
#         file_name = file.name

#         # Metadatos del archivo, incluyendo la carpeta destino
#         file_metadata = {
#             'name': file_name,
#             'parents': [folder_id]  # ID de la carpeta de destino
#         }

#         # Subir el archivo a Google Drive
#         media = MediaFileUpload(file_path, mimetype="application/pdf")

#         archivo_subido = drive_service.files().create(
#             body=file_metadata,
#             media_body=media
#         ).execute()

#         # Obtener el ID del archivo subido
#         file_id = archivo_subido['id']
#         file_ids.append(file_id)
#         print(
#             f"Archivo '{file_name}' subido con ID: {file_id} en la carpeta {folder_id}")

#         # Hacerlo accesible con el enlace y compartirlo con propietarios
#         compartir_archivo_con_enlace(file_id, emails_propietarios)

#         # Transferir la propiedad del archivo

#     return file_ids  # Devuelve la lista de IDs de los archivos subidos
# # Función de carga de archivo PDF desde el dispositivo


# # Función principal de la app


# def main(page: ft.Page):
#     page.title = "Subir archivo PDF a Google Drive"

#     def cargar_archivos_pdf(e):
#         """Sube múltiples archivos PDF desde el dispositivo"""
#         if e.files:
#             subir_y_compartir_archivos(
#                 e.files,  # Lista de archivos seleccionados
#                 ["taborinfo@tabor.cat"],  # Emails propietarios
#                 "1kVHZJm-j-Vn_AVyUDHScfg3kHI2_EyX0"  # ID de la carpeta en Drive
#             )

#     def load_pdf(e):
#         # file_picker = ft.FilePicker(on_result=lambda e: subir_y_compartir_archivo(
#         #     e.files[0].path, e.files[0].name, [
#         #         "taborinfo@tabor.cat"]
#         # ))
#         file_picker = ft.FilePicker(on_result=cargar_archivos_pdf)
#         page.add(file_picker)
#         file_picker.pick_files(allow_multiple=True)

#     # Crear el botón para cargar el archivo
#     boton_cargar = ft.ElevatedButton(
#         "Cargar archivo PDF", on_click=load_pdf)

#     page.add(boton_cargar)

#     def verificar_acceso_carpeta(folder_id):
#         """Verifica si la cuenta de servicio tiene acceso a la carpeta en Google Drive"""
#         try:
#             drive_service.files().get(fileId=folder_id).execute()
#             print("✅ La cuenta de servicio tiene acceso a la carpeta.")
#         except HttpError as error:
#             print(f"❌ No se pudo acceder a la carpeta: {error}")

#     verificar_acceso_carpeta("1kVHZJm-j-Vn_AVyUDHScfg3kHI2_EyX0")


# ft.app(target=main)
