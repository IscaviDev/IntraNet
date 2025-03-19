import flet as ft
import pandas as pd
import os
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.http import MediaFileUpload

# Configuración de Google Drive
SCOPES = ["https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(
    "./storage/credentials.json", scopes=SCOPES)
drive_service = build("drive", "v3", credentials=creds)

# Reemplaza con el ID de tu archivo en Google Drive


def search_id():
    files_names = ["Classes.csv", "Tutors.csv", "Alumns_to_Parents.csv",
                   "Parents.csv", "Alumns.csv", "Administrators.csv"]  # 🔹 Cambia esto por el nombre que buscas
    files_ids = []
# Realizar la búsqueda en Google Drive
    for i in files_names:
        query = f"name = '{i}'"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        # Mostrar resultados
        if not files:
            print(f'❌ No se encontraron archivos con el nombre "{i}".')
        else:
            for file in files:
                print(
                    f"✅ Archivo encontrado: {file['name']} - ID: {file['id']}")
                files_ids.append(file['id'])

    return {'classes_csv': files_ids[0], 'tutors_csv': files_ids[1], 'alumns_to_parents_csv': files_ids[2], 'parents_csv': files_ids[3], 'alumns_csv': files_ids[4], 'administrators_csv': files_ids[5]}


# ID del archivo CSV en Google Drive


db_files_id = search_id()

CSV_FILE_ID = db_files_id["alumns_csv"]
LOCAL_CSV_PATH = "./data.csv"

# Función para descargar el archivo CSV desde Google Drive


def descargar_csv():
    request = drive_service.files().get_media(fileId=CSV_FILE_ID)
    with open(LOCAL_CSV_PATH, "wb") as f:
        f.write(request.execute())


def subir_csv():
    media = MediaFileUpload(LOCAL_CSV_PATH, mimetype="text/csv")
    drive_service.files().update(fileId=CSV_FILE_ID, media_body=media).execute()


def main(page: ft.Page):
    page.title = "Gestor de CSV con Flet"
    page.auto_scroll = True
    page.scroll = ft.ScrollMode.ALWAYS
    # Descargar el CSV al iniciar la app
    stack = ft.Stack(
        expand=True)
    page.add(stack)
    descargar_csv()
    df = pd.read_csv(LOCAL_CSV_PATH)

    tabla = ft.Row(controls=[ft.DataTable(
        columns=[ft.DataColumn(ft.Text(col)) for col in df.columns],
        rows=[ft.DataRow(cells=[ft.DataCell(ft.Text(str(value)))
                         for value in row]) for row in df.values]
    )], scroll=ft.ScrollMode.ADAPTIVE)

    def actualizar_tabla():
        df = pd.read_csv(LOCAL_CSV_PATH)
        tabla.rows = [ft.DataRow(cells=[ft.DataCell(
            ft.Text(str(value))) for value in row]) for row in df.values]
        page.update()

    def agregar_registro(e):
        nuevo_registro = [campo.value for campo in inputs]
        df.loc[len(df)] = nuevo_registro
        df.to_csv(LOCAL_CSV_PATH, index=False)
        subir_csv()
        actualizar_tabla()
    inputs = [ft.TextField(label=col) for col in df.columns]
    boton_agregar = ft.ElevatedButton("Agregar", on_click=agregar_registro)
    tabs = ft.Tabs(
        selected_index=1,
        tabs=[
            ft.Tab(text="DataBase",
                   content=tabla),
            ft.Tab(text="Add datas",
                   content=ft.Container(content=ft.Column(controls=[*inputs, boton_agregar]))),
        ],
        tab_alignment=ft.TabAlignment.CENTER
    )
    stack.controls.append(ft.Container(content=ft.Column(controls=[ft.Container(height=30), tabs], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                         alignment=ft.MainAxisAlignment.CENTER), alignment=ft.alignment.center))
    page.update()
    # page.add(tabla)
    # page.add(tabla, *inputs, boton_agregar)


ft.app(target=main)
