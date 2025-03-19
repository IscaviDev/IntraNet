import ast
import flet as ft
import pandas as pd
# import json
from datetime import datetime, timedelta
import random
import re
import time
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from io import BytesIO  # Usamos BytesIO en lugar de StringIO

SCOPES = ["https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(
    "./storage/credentials.json", scopes=SCOPES)
# creds = Credentials.from_service_account_file(
#     "credentials.json", scopes=SCOPES)
drive_service = build("drive", "v3", credentials=creds)


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


PARENTS_FILE_ID = db_files_id["parents_csv"]
ALUMNS_FILE_ID = db_files_id["alumns_csv"]
TUTORS_FILE_ID = db_files_id["tutors_csv"]
CLASSES_FILE_ID = db_files_id["classes_csv"]
ALUMNS_TO_PARENTS_FILE_ID = db_files_id["alumns_to_parents_csv"]
ADMINISTRATORS_FILE_ID = db_files_id["administrators_csv"]
AUTORITZACIONS_FOLDER_ID = "14_CsfG3UCATBFijzcoTAn2AtY5Sn-Q1D"
CIRCULARS_FOLDER_ID = "1QY_RZ3-1VYbQu8e82YeDSQP7eVA6fC8o"


def obtener_id_subcarpeta(carpeta_padre_id, nombre_subcarpeta):
    # Realizar la búsqueda de la subcarpeta dentro de la carpeta padre
    query = f"'{carpeta_padre_id}' in parents and name = '{nombre_subcarpeta}' and mimeType = 'application/vnd.google-apps.folder'"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
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


def leer_csv(file_id):
    """Lee el archivo CSV desde Google Drive"""
    request = drive_service.files().get_media(fileId=file_id)
    csv_data = request.execute().decode("utf-8")
    # Usamos BytesIO aquí para manejar los datos en bytes
    df = pd.read_csv(BytesIO(csv_data.encode('utf-8')))
    return df


def escribir_csv(df, file_id, nombre_archivo):
    """Sube el archivo CSV modificado a Google Drive"""
    output = BytesIO()  # Usamos BytesIO para trabajar con datos en bytes
    file_df = pd.DataFrame(df)
    file_df.to_csv(output, index=False)
    output.seek(0)

    # Definir los metadatos del archivo (nombre)
    file_metadata = {"name": nombre_archivo}

    # Crear el cuerpo del archivo para la carga usando MediaIoBaseUpload
    media = MediaIoBaseUpload(output, mimetype="text/csv", resumable=True)

    # Actualizar el archivo en Google Drive con los metadatos y el contenido
    drive_service.files().update(fileId=file_id, body=file_metadata,
                                 media_body=media).execute()


def upload_users(table):
    columns = table.columns  # Nombres de las columnas del DataFrame
    processed_rows = []  # Lista para almacenar las filas procesadas como diccionarios
    unique_rows = []  # Lista para almacenar filas únicas sin duplicados
    # Recorre cada fila del DataFrame y construye un diccionario para cada una
    for index in table.index:
        row_dict = {}  # Nuevo diccionario para cada fila
        for column in columns:
            value = table.at[index, column]
            # Convierte strings con formato de lista en listas reales
            if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                try:
                    value = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    pass  # Si no se puede interpretar, dejar como está
            elif isinstance(value, str) and value.startswith('{') and value.endswith('}'):
                try:
                    value = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    pass  # Si no se puede interpretar, dejar como está
            row_dict[column] = value
        # Añade el diccionario a la lista procesada
        processed_rows.append(row_dict)
    # Elimina duplicados basándose en el contenido de los diccionarios
    for row in processed_rows:
        if row not in unique_rows:
            unique_rows.append(row)

    return unique_rows


df_parents = leer_csv(PARENTS_FILE_ID)
df_alumns = leer_csv(ALUMNS_FILE_ID)
df_classes = leer_csv(CLASSES_FILE_ID)
df_tutors = leer_csv(TUTORS_FILE_ID)
df_alumns_to_parents = leer_csv(ALUMNS_TO_PARENTS_FILE_ID)
df_administrators = leer_csv(ADMINISTRATORS_FILE_ID)
# Leer el archivo CSV en un DataFrame
# Convertir el DataFrame a una lista de diccionarios
parents = upload_users(df_parents)
alumns = upload_users(df_alumns)
classes = upload_users(df_classes)
tutors = upload_users(df_tutors)
alumns_to_parents = upload_users(df_alumns_to_parents)
administrators = upload_users(df_administrators)

CAIXABANK_API_URL = "https://your-caixabank-api-endpoint"
CAIXABANK_API_KEY = "your_api_key"

current_session = {"account": [], "sub-account": [],
                   "sub-account-active": [], "class-info": []}


def FindMatches(list_strings):
    match_obj = {"str1": [], "str2": []}
    obj_to_remove = ["\s", ",", ".pdf"]
    for i in range(1, 3):
        # print(list_strings[i-1])
        match_obj[f"str{str(i)}"].append(list_strings[i-1])
        for j in range(0, 3):
            element_to_remove = re.sub(
                obj_to_remove[j], "", match_obj[f"str{str(i)}"][0])
            match_obj[f"str{str(i)}"].clear()
            match_obj[f"str{str(i)}"].append(element_to_remove)
        sort_str = sorted(match_obj[f"str{str(i)}"][0].lower())
        match_obj[f"str{str(i)}"].clear()
        match_obj[f"str{str(i)}"].append(sort_str)
    if match_obj["str1"][0] != match_obj["str2"][0]:
        return False
    return True


async def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    page.expand = True

    page.bgcolor = "#f4f6f9"
    page.title = "Portal Tabor"
    stack = ft.Stack(
        expand=True)
    page.add(stack)
    email = ft.Ref[ft.TextField]()
    password = ft.Ref[ft.TextField]()
    error_message = ft.Ref[ft.Text]()
    event_text = ft.Ref[ft.TextField]()

    def background_image():
        stack.controls.append(ft.Container(
            expand=True,  # Expandir para cubrir todo el espacio
            image=ft.DecorationImage(src="./fondoTabor1.png",
                                     fit=ft.ImageFit.COVER,
                                     opacity=0.25)
        ))
        page.update()

    def background_opacity():
        stack.controls.append(ft.Container(
            expand=True,
            # Capa blanca semitransparente
            bgcolor=ft.colors.with_opacity(0.4, "white"),
        ))
        page.update()

    def create_container(controls):
        return ft.Container(
            content=ft.Column(
                controls=controls,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15
            ),
            padding=30,
            bgcolor=ft.colors.LIGHT_BLUE_50,
            border_radius=10,
            margin=20,
        )

    def login_search_user(table_users):  # Cambiado
        for user in table_users:
            if email.current.value == user["username"] and password.current.value == user["password"]:
                current_session["account"].append(user)
                # print#(current_session)
                return current_session

    def login_search_sub_user():  # Cambiado
        search_id = []
        transform_class = []
        if current_session["account"][0]["user-license"] == "parent":
            for relation in alumns_to_parents:
                if relation["parent_id"] == current_session["account"][0]["parent_id"]:
                    for id_alumn in relation["alumn_id"]:
                        search_id.append(id_alumn)
            for i in range(len(search_id)):
                for alumn in alumns:
                    print(type(search_id[i]))
                    print(type(alumn["alumn_id"]))
                    if search_id[i] == str(alumn["alumn_id"]):
                        print("matched")
                        current_session["sub-account"].append(alumn)
        elif current_session["account"][0]["user-license"] == "tutor":
            for clase in classes:
                if clase["class_id"] == current_session["account"][0]["class_id"]:
                    for i in range(len(clase["alumn_id"])):
                        search_id.append(clase["alumn_id"][i])
                    for j in range(len(search_id)):
                        for alumn in alumns:
                            if search_id[j] == str(alumn["alumn_id"]):
                                print("matched")
                                current_session["sub-account"].append(
                                    alumn)
        return current_session
    # print(current_session)

    def login(e):  # Cambiado
        while True:
            try:
                login_search_user(administrators)
                login_search_user(parents)
                login_search_user(tutors)
                login_search_sub_user()
                break
            except:
                error_message.current.value = "Correu o contrasenya incorrectes"
                return error_message
        # if current_session["account"][0]["user-license"] == "admin":
        #     admin_page()
        # page.clean()
        if len(current_session["sub-account"]) == 1:
            current_session["sub-account-active"].append(
                current_session["sub-account"][0])
            home_page()
        elif current_session["account"][0]["user-license"] == "tutor":
            # current_session["sub-account-active"].append(
            #     classes["events"])
            home_page()
        elif current_session["account"][0]["user-license"] == "admin":
            admin_page()
        else:
            user_select_page()
        # print(current_session)

    def login_page(e=None):  # stack hecho
        current_session["account"].clear()
        current_session["sub-account"].clear()
        current_session["sub-account-active"].clear()
        page.clean()
        page.add(stack)
        stack.controls.clear()
        background_image()

        stack.controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[
                        create_container([
                            ft.Text("Iniciar sessió", size=32, weight="bold",
                                    color=ft.colors.BLACK, text_align=ft.TextAlign.CENTER),
                            ft.TextField(
                                label="Correu electrònic", ref=email, width=300, bgcolor=ft.colors.WHITE),
                            ft.TextField(label="Contrasenya", password=True, can_reveal_password=True,
                                         ref=password, width=300, bgcolor=ft.colors.WHITE),
                            ft.ElevatedButton(text="Accedir", on_click=login, style=ft.ButtonStyle(
                                bgcolor=ft.colors.BLUE)),
                            ft.Text(ref=error_message, color="red")
                        ])
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                    expand=True
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
        )
        page.update()

    def create_app_bar(e=None):  # Cambiado
        page.add(ft.AppBar(
            title=ft.Text("Escola Tabor", size=28,
                          weight="bold", color=ft.colors.BLACK),
            center_title=True,
            bgcolor=ft.colors.BLUE_300,
            actions=[
                ft.IconButton(ft.icons.NOTIFICATIONS, on_click=lambda e: print(
                    "Notificacions"), tooltip="Notificacions"),
                ft.IconButton(ft.icons.ACCOUNT_CIRCLE,
                              on_click=user_menu, tooltip="Menú d'usuari")
            ],
        ))
        page.update()

    def current_user(e=None):  # Cambiado
        account_name = f"{current_session['account'][0]['name']} {current_session['account'][0]['first-surname']} {current_session['account'][0]['second-surname']}"
        if current_session["account"][0]["user-license"] == "admin":
            sub_account_name = "admin"
            stack.controls.append(ft.Column(
                controls=[ft.Row(
                    controls=[ft.Text("Sessió iniciada a:", size=18, weight="bold", color=ft.colors.BLACK, text_align=ft.TextAlign.CENTER), ft.Text(account_name, size=16, color=ft.colors.BLACK, text_align=ft.TextAlign.CENTER)]),
                    ft.Row(
                    controls=[ft.Text("Compte:", size=18, weight="bold", color=ft.colors.BLACK, text_align=ft.TextAlign.CENTER), ft.Text(sub_account_name, size=16, color=ft.colors.BLACK, text_align=ft.TextAlign.CENTER)])],
            )
            )
        else:
            if current_session["account"][0]["user-license"] == "tutor":
                sub_account_name = f"{current_session['account'][0]['class_id']}"
            elif current_session["account"][0]["user-license"] == "parent":
                sub_account_name = f"{current_session['sub-account-active'][0]['name']} {current_session['sub-account-active'][0]['first-surname']} {current_session['sub-account-active'][0]['second-surname']}"
            stack.controls.append(ft.Column(
                controls=[ft.Row(
                    controls=[ft.Text("Sessió iniciada a:", size=18, weight="bold", color=ft.colors.BLACK, text_align=ft.TextAlign.CENTER), ft.Text(account_name, size=16, color=ft.colors.BLACK, text_align=ft.TextAlign.CENTER)]),
                    ft.Row(
                    controls=[ft.Text("Compte:", size=18, weight="bold", color=ft.colors.BLACK, text_align=ft.TextAlign.CENTER), ft.Text(sub_account_name, size=16, color=ft.colors.BLACK, text_align=ft.TextAlign.CENTER)])],
            )
            )
        page.update()

    def admin_page(e=None):
        page.clean()
        page.add(stack)
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        current_user()
        update_admin_content()
        page.update()

    def home_page(e=None):  # Cambiado
        page.clean()
        page.add(stack)
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        current_user()
        update_home_content()
        print(current_session)
        page.update()

    def detect_click(e):  # Cambiado
        print(e)
        current_session["sub-account-active"].clear()
        if current_session["account"][0]["user-license"] == "parent":
            for i in range(len(current_session["sub-account"])):
                if e == current_session["sub-account"][i]["alumn_id"]:
                    current_session["sub-account-active"].append(
                        current_session["sub-account"][i])
        elif current_session["account"][0]["user-license"] == "tutor":
            pass
        page.update()
        home_page()

    def create_admin_uniform_button(label, on_click_action):
        button_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(label, size=18, weight="bold",
                            text_align=ft.TextAlign.CENTER),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
            padding=ft.padding.all(10),
            bgcolor=ft.colors.WHITE,
            border_radius=10,
            border=ft.border.all(ft.colors.BLUE_300),
            width=150,
            height=140,
        )

        return ft.ElevatedButton(
            content=button_content,
            on_click=on_click_action,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.TRANSPARENT,
                elevation=0,
            )
        )

    def create_admin_db_uniform_button(label, on_click_action, db_table, file_id, nombre_archivo):
        button_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(label, size=18, weight="bold",
                            text_align=ft.TextAlign.CENTER),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
            padding=ft.padding.all(10),
            bgcolor=ft.colors.WHITE,
            border_radius=10,
            border=ft.border.all(ft.colors.BLUE_300),
            width=150,
            height=140,
        )

        return ft.ElevatedButton(
            content=button_content,
            on_click=lambda e, db=db_table, fid=file_id, fn=nombre_archivo: on_click_action(
                db, fid, fn),
            style=ft.ButtonStyle(
                bgcolor=ft.colors.TRANSPARENT,
                elevation=0,
            )
        )

    def create_uniform_button(image_src, label, on_click_action, user_active_page, width_img, height_img):  # Cambiado
        button_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Image(
                        src=image_src,
                        width=width_img,
                        height=height_img,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    ft.Text(label, size=18, weight="bold",
                            text_align=ft.TextAlign.CENTER),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
            padding=ft.padding.all(10),
            bgcolor=ft.colors.WHITE,
            border_radius=10,
            border=ft.border.all(ft.colors.BLUE_300),
            width=150,
            height=140,
        )
        if user_active_page:
            return ft.ElevatedButton(
                content=button_content,
                on_click=lambda e: detect_click(on_click_action),
                style=ft.ButtonStyle(
                    elevation=0,
                    padding=ft.padding.symmetric(
                        horizontal=20, vertical=10),
                    bgcolor={
                        ft.ControlState.DEFAULT: ft.colors.TRANSPARENT,
                    })
            )
        else:
            return ft.ElevatedButton(
                content=button_content,
                on_click=on_click_action,
                style=ft.ButtonStyle(
                    bgcolor=ft.colors.TRANSPARENT,
                    elevation=0,
                )
            )

    def data_base_info(db_table, file_id, nombre_archivo):
        page.clean()
        page.add(stack)
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        current_user()
        table_df = pd.DataFrame(db_table)
        tabla = ft.Row(controls=[ft.DataTable(
            columns=[ft.DataColumn(ft.Text(col)) for col in table_df.columns],
            rows=[ft.DataRow(cells=[ft.DataCell(ft.Text(str(value)))
                                    for value in row]) for row in table_df.values]
        )], scroll=ft.ScrollMode.ADAPTIVE)
        stack.controls.append(ft.Container(content=ft.Column(controls=[tabla, ft.ElevatedButton(
            "Torna a l'inici",
            on_click=admin_page,
            style=ft.ButtonStyle(
                color=ft.colors.PRIMARY,
            ),
        )])))
        page.update()

    def update_data_base_info(db_table, file_id, nombre_archivo):
        page.clean()
        page.add(stack)
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        current_user()

        def agregar_registro(file_id, nombre_archivo):
            output = BytesIO()  # Usamos BytesIO para trabajar con datos en bytes
            nuevo_registro = [campo.value for campo in inputs]
            db_table.loc[len(db_table)] = nuevo_registro
            db_table.to_csv(output, index=False)
            output.seek(0)

            # Definir los metadatos del archivo (nombre)
            file_metadata = {"name": nombre_archivo}

            # Crear el cuerpo del archivo para la carga usando MediaIoBaseUpload
            media = MediaIoBaseUpload(
                output, mimetype="text/csv", resumable=True)

            # Actualizar el archivo en Google Drive con los metadatos y el contenido
            drive_service.files().update(fileId=file_id, body=file_metadata,
                                         media_body=media).execute()
            # subir_csv()
        # table_df = pd.DataFrame(db_table)
        tabla = ft.Row(controls=[ft.DataTable(
            columns=[ft.DataColumn(ft.Text(col)) for col in db_table.columns],
            rows=[ft.DataRow(cells=[ft.DataCell(ft.Text(str(value)))
                                    for value in row]) for row in db_table.values]
        )], scroll=ft.ScrollMode.ADAPTIVE)
        inputs = [ft.TextField(label=col) for col in db_table.columns]
        boton_agregar = ft.ElevatedButton(
            "Agregar", on_click=lambda e, fid=file_id, fn=nombre_archivo: agregar_registro(fid, fn))
        stack.controls.append(ft.Container(
            content=ft.Column(controls=[*inputs, boton_agregar, ft.ElevatedButton(
                "Torna a l'inici",
                on_click=admin_page,
                style=ft.ButtonStyle(
                    color=ft.colors.PRIMARY,
                ),
            )])))
        page.update()

    def update_db_admin_content(db_table, file_id, nombre_archivo):
        data_base_info_button_elevated = create_admin_db_uniform_button(
            "DataBase Table", data_base_info, db_table, file_id, nombre_archivo
        )
        add_data_base_info_button_elevated = create_admin_db_uniform_button(
            "Add DataBase Datas", update_data_base_info, db_table, file_id, nombre_archivo
        )
        stack.controls.append(ft.Column(controls=[ft.Column(controls=[
            ft.Row(
                controls=[data_base_info_button_elevated,
                          add_data_base_info_button_elevated],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0
            )
        ]), ft.Column(controls=[ft.ElevatedButton(
            "Torna a l'inici",
            on_click=admin_page,
            style=ft.ButtonStyle(
                color=ft.colors.PRIMARY,
            ),
        )])]))
        page.update()

    def update_admin_content(e=None):
        parents_button_elevated = create_admin_uniform_button(
            "Parents", parents_page
        )
        alumns_button_elevated = create_admin_uniform_button(
            "Alumns", alumns_page
        )
        tutors_button_elevated = create_admin_uniform_button(
            "Tutors", tutors_page
        )
        classes_button_elevated = create_admin_uniform_button(
            "Classes", classes_page
        )
        administrators_button_elevated = create_admin_uniform_button(
            "Administrators", administrators_page
        )
        alumns_to_parents_button_elevated = create_admin_uniform_button(
            "Alumns to Parens", alumns_to_parents_page
        )
        buttons = [
            parents_button_elevated,
            alumns_button_elevated,
            tutors_button_elevated,
            classes_button_elevated,
            administrators_button_elevated,
            alumns_to_parents_button_elevated
        ]
        stack.controls.append(ft.Column(controls=[ft.Column(controls=[
            ft.Row(
                controls=[parents_button_elevated,
                          alumns_button_elevated],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0
            )
        ]), ft.Column(controls=[
            ft.Row(
                controls=[tutors_button_elevated,
                      classes_button_elevated],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0
            )
        ]),
            ft.Column(controls=[
                ft.Row(
                    controls=[administrators_button_elevated,
                              alumns_to_parents_button_elevated],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=0
                )
            ])],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER))
        print(stack.controls)
        # page.add(row)
        page.update()

    def parents_page(e=None):
        page.clean()
        page.add(stack)
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        current_user()
        update_db_admin_content(
            df_parents, PARENTS_FILE_ID, "Parents.csv")
        page.update()

    def alumns_page(e=None):
        page.clean()
        page.add(stack)
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        current_user()
        update_db_admin_content(
            df_alumns, ALUMNS_FILE_ID, "Alumns.csv")
        page.update()

    def tutors_page(e=None):
        page.clean()
        page.add(stack)
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        current_user()
        update_db_admin_content(
            df_tutors, TUTORS_FILE_ID, "Tutors.csv")
        page.update()

    def classes_page(e=None):
        page.clean()
        page.add(stack)
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        current_user()
        update_db_admin_content(
            df_classes, CLASSES_FILE_ID, "Classes.csv")
        page.update()

    def administrators_page(e=None):
        page.clean()
        page.add(stack)
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        current_user()
        update_db_admin_content(
            df_administrators, ADMINISTRATORS_FILE_ID, "Administrators.csv")
        page.update()

    def alumns_to_parents_page(e=None):
        page.clean()
        page.add(stack)
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        current_user()
        update_db_admin_content(
            df_alumns_to_parents, ALUMNS_TO_PARENTS_FILE_ID, "Alumns_to_Parents.csv")
        page.update()

    def update_home_content(e=None):  # Cambiado
        calendar_button_elevated = create_uniform_button(
            "./calendari.png", "Calendari", calendar_page, False, 60, 60  # Agenda
        )
        document_button_elevated = create_uniform_button(
            "./documents.png", "Circulars", documents_page, False, 60, 60
        )
        avisos_button_elevated = create_uniform_button(
            "./avisos.png", "Avisos", messages_page, False, 60, 60
        )
        autorizaciones_button_elevated = create_uniform_button(
            "./autoritzacions.png", "Autoritzacions", tasks_page, False, 60, 60
        )
        payments_button_elevated = create_uniform_button(
            "./pagaments.png", "Pagaments", school_page, False, 60, 60
        )
        logout_button_elevated = create_uniform_button(
            "./informes.png", "Informes", informes_page, False, 60, 60
        )
        buttons = [
            calendar_button_elevated,
            document_button_elevated,
            avisos_button_elevated,
            autorizaciones_button_elevated,
            payments_button_elevated,
            logout_button_elevated
        ]
        stack.controls.append(ft.Column(controls=[ft.Column(controls=[
            ft.Row(
                controls=[calendar_button_elevated,
                          document_button_elevated],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0
            )
        ]), ft.Column(controls=[
            ft.Row(
                controls=[avisos_button_elevated,
                      autorizaciones_button_elevated],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0
            )
        ]),
            ft.Column(controls=[
                ft.Row(
                    controls=[payments_button_elevated,
                              logout_button_elevated],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=0
                )
            ])],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER))
        print(stack.controls)
        # page.add(row)
        page.update()

    def user_menu(e):  # Cambiado
        # page.clean()
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        if current_session["account"][0]["user-license"] == "parent":
            info_name = "Informació de l'alumne"
        elif current_session["account"][0]["user-license"] == "tutor":
            info_name = "Informació de la classe"
        stack.controls.append(ft.Container(content=ft.Column(controls=[
            ft.ResponsiveRow(
                controls=[
                    ft.Text(
                        "Configuració del compte d'usuari",
                        size=28,
                        weight="bold",
                        color=ft.colors.BLUE_GREY_800,
                        text_align=ft.TextAlign.CENTER,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Container(height=15),
            ft.ResponsiveRow(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(
                                "Opcions del Compte",
                                size=20,
                                color=ft.colors.INDIGO_700,
                                weight="w600",
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.ResponsiveRow(
                controls=[
                    ft.Column(
                        controls=[
                            ft.OutlinedButton(
                                "Informació del compte",
                                on_click=settings_user_page,
                                style=ft.ButtonStyle(
                                    color=ft.colors.INDIGO_600,
                                    padding=ft.padding.symmetric(
                                        horizontal=20, vertical=10),
                                    elevation=1,
                                ),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.ResponsiveRow(
                controls=[
                    ft.Column(
                        controls=[
                            ft.OutlinedButton(
                                info_name,
                                on_click=settings_sub_account_page,
                                style=ft.ButtonStyle(
                                    color=ft.colors.INDIGO_600,
                                    padding=ft.padding.symmetric(
                                        horizontal=20, vertical=10),
                                    elevation=1,
                                ),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Container(height=10),
            ft.ResponsiveRow(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(
                                "Navegació",
                                size=20,
                                color=ft.colors.GREEN_700,
                                weight="w600",
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.ResponsiveRow(
                controls=[
                    ft.Column(
                        controls=[
                            ft.OutlinedButton(
                                text="Tanca sessió",
                                on_click=login_page,
                                style=ft.ButtonStyle(
                                    color=ft.colors.WHITE,
                                    padding=ft.padding.symmetric(
                                        horizontal=18, vertical=10),
                                    bgcolor={
                                        ft.ControlState.DEFAULT: ft.colors.RED_600,
                                        ft.ControlState.HOVERED: ft.colors.RED_800,
                                    },
                                ),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Container(height=30),
            ft.ResponsiveRow(
                controls=[
                    ft.Column(
                        controls=[
                            ft.ElevatedButton(
                                text="Enrere",
                                icon=ft.icons.ARROW_BACK,
                                on_click=home_page,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.TEAL_700,
                                    color=ft.colors.WHITE,
                                    padding=ft.padding.symmetric(
                                        horizontal=16, vertical=8),
                                ),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        ))
        page.update()

    def settings_user_page(e=None):  # Cambiado
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        sub_accounts = []
        isProfe = False
        active = []
        buttons = []

        def create_info_card(title, content, icon_name, select_user_page, is_active, onclick_action):
            if select_user_page:
                if is_active:
                    return ft.ElevatedButton(
                        content=ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Icon(name=icon_name, size=20,
                                                    color=ft.colors.TEAL_ACCENT),
                                            ft.Text(
                                                title, size=16, weight="bold", color=ft.colors.TEAL_700)
                                        ],
                                        alignment=ft.MainAxisAlignment.START,
                                        spacing=8
                                    ),
                                    ft.Row(
                                        controls=[ft.Text(content, size=14, color=ft.colors.BLACK, weight="w400"), ft.Icon(
                                            name="CHECK", size=20, color=ft.colors.GREEN_ACCENT_700)],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                    )
                                ],
                                spacing=4,
                                alignment=ft.MainAxisAlignment.START,
                                horizontal_alignment=ft.CrossAxisAlignment.START
                            ),
                            padding=ft.padding.all(15),
                            border_radius=ft.border_radius.all(10),
                            bgcolor=ft.colors.BLUE_100,
                            width=300,
                            height=90,
                            alignment=ft.alignment.center
                        ),
                        on_click=lambda e: detect_click(onclick_action),
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.TRANSPARENT,
                            elevation=0
                        )
                    )
                else:
                    return ft.ElevatedButton(
                        content=ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Icon(name=icon_name, size=20,
                                                    color=ft.colors.TEAL_ACCENT),
                                            ft.Text(
                                                title, size=16, weight="bold", color=ft.colors.TEAL_700)
                                        ],
                                        alignment=ft.MainAxisAlignment.START,
                                        spacing=8
                                    ),
                                    ft.Text(content, size=14,
                                            color=ft.colors.GREY_900, weight="w400"),
                                ],
                                spacing=4,
                                alignment=ft.MainAxisAlignment.START,
                                horizontal_alignment=ft.CrossAxisAlignment.START
                            ),
                            padding=ft.padding.all(15),
                            border_radius=ft.border_radius.all(10),
                            bgcolor=ft.colors.TEAL_50,
                            width=300,
                            height=90,
                            alignment=ft.alignment.center
                        ),
                        on_click=lambda e: detect_click(onclick_action),
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.TRANSPARENT,
                            elevation=0
                        )
                    )
            else:
                return ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(name=icon_name, size=20,
                                            color=ft.colors.TEAL_ACCENT),
                                    ft.Text(title, size=16, weight="bold",
                                            color=ft.colors.TEAL_700)
                                ],
                                alignment=ft.MainAxisAlignment.START,
                                spacing=8
                            ),
                            ft.Text(content, size=14,
                                    color=ft.colors.BLACK, weight="w400"),
                        ],
                        spacing=4,
                        alignment=ft.MainAxisAlignment.START,
                        horizontal_alignment=ft.CrossAxisAlignment.START
                    ),
                    padding=ft.padding.all(15),
                    border_radius=ft.border_radius.all(10),
                    bgcolor=ft.colors.AMBER,
                    width=300,
                    height=90,
                    alignment=ft.alignment.center
                )
        back_button = ft.ElevatedButton(
            text="Volver",
            icon=ft.icons.ARROW_BACK,
            on_click=user_menu,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.TEAL_700,
                color=ft.colors.WHITE,
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
            )
        )
        user_name = f"{current_session['account'][0]['name']} {current_session['account'][0]['first-surname']} {current_session['account'][0]['second-surname']}"
        if current_session["account"][0]["user-license"] == "tutor":
            sub_account_name = f"{current_session['account'][0]['class_id']}"
            buttons.append(create_info_card(
                current_session["account"][0]["class_id"], sub_account_name, "school", True, True, current_session["account"][0]["class_id"]))
        elif current_session["account"][0]["user-license"] == "parent":
            for i in range(len(current_session["sub-account"])):
                sub_account_name = f"{current_session['sub-account'][i]['name']} {current_session['sub-account'][i]['first-surname']} {current_session['sub-account'][i]['second-surname']}"
                if current_session["sub-account-active"][0]["alumn_id"] == current_session["sub-account"][i]["alumn_id"]:
                    buttons.append(create_info_card(
                        sub_account_name, sub_account_name, "school", True, True, current_session["sub-account"][i]["alumn_id"]))
                else:
                    buttons.append(create_info_card(
                        sub_account_name, sub_account_name, "school", True, False, current_session["sub-account"][i]["alumn_id"]))
        buttons.insert(0, create_info_card(
            "Usuari", user_name, "person", False, False, False))

        def student_info_section(controls):
            stack.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Perfil de l'usuari", size=26, weight="bold",
                                    color=ft.colors.TEAL_800, text_align=ft.TextAlign.CENTER),
                            ft.Column(
                                controls=controls,
                                spacing=15,
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            ft.Row(
                                controls=[back_button],
                                alignment=ft.MainAxisAlignment.CENTER,
                            )
                        ],
                        spacing=20,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    alignment=ft.alignment.center,
                    padding=ft.padding.symmetric(vertical=20),
                    expand=True,
                ))
        student_info_section(buttons)
        page.update()

    def settings_sub_account_page(e=None):  # Cambiado
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        if current_session["account"][0]["user-license"] == "parent":
            class_name = f"{current_session['sub-account-active'][0]['class_id']}"
            student_name = f"{current_session['sub-account-active'][0]['name']} {current_session['sub-account-active'][0]['first-surname']} {current_session['sub-account-active'][0]['second-surname']}"
            for i in range(len(tutors)):
                if current_session["sub-account-active"][0]["class_id"] == tutors[i]["class_id"]:
                    tutor_name = f"{tutors[i]['name']} {tutors[i]['first-surname']} {tutors[i]['second-surname']}"
        elif current_session["account"][0]["user-license"] == "tutor":
            class_name = f"{current_session['account'][0]['class_id']}"
            tutor_name = f"{current_session['account'][0]['name']} {current_session['account'][0]['first-surname']} {current_session['account'][0]['second-surname']}"

        def create_info_card(title, content, icon_name, is_button, onclick_action):
            if is_button:
                return ft.ElevatedButton(
                    content=ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(name=icon_name, size=22,
                                                color=ft.colors.TEAL_ACCENT),
                                        ft.Text(title, size=20, weight="bold",
                                                color=ft.colors.TEAL_700)
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                    spacing=8
                                ),
                                ft.Text(content, size=14,
                                        color=ft.colors.GREY_900, weight="w400"),
                            ],
                            spacing=4,
                            alignment=ft.MainAxisAlignment.START,
                            horizontal_alignment=ft.CrossAxisAlignment.START
                        ),
                        padding=ft.padding.all(15),
                        border_radius=ft.border_radius.all(10),
                        bgcolor=ft.colors.TEAL_50,
                        width=300,
                        height=90,
                        alignment=ft.alignment.center
                    ),
                    on_click=onclick_action,
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.TRANSPARENT,
                        elevation=0
                    ))
            else:
                return ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(name=icon_name, size=22,
                                            color=ft.colors.TEAL_ACCENT),
                                    ft.Text(title, size=20, weight="bold",
                                            color=ft.colors.TEAL_700)
                                ],
                                alignment=ft.MainAxisAlignment.START,
                                spacing=8
                            ),
                            ft.Text(content, size=14,
                                    color=ft.colors.GREY_900, weight="w400"),
                        ],
                        spacing=4,
                        alignment=ft.MainAxisAlignment.START,
                        horizontal_alignment=ft.CrossAxisAlignment.START
                    ),
                    padding=ft.padding.all(15),
                    border_radius=ft.border_radius.all(10),
                    bgcolor=ft.colors.TEAL_50,
                    width=300,
                    height=90,
                    alignment=ft.alignment.center
                )

        def create_location_card():
            location_content = ft.Row(
                controls=[
                    ft.Text(f"Clase: {class_name}", size=14,
                            color=ft.colors.GREY_900)
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.START
            )
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(name="location_on", size=20,
                                        color=ft.colors.TEAL_ACCENT),
                                ft.Text("Ubicació", size=16,
                                        weight="bold", color=ft.colors.TEAL_700)
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=8
                        ),
                        location_content
                    ],
                    spacing=4,
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.START
                ),
                padding=ft.padding.all(15),
                border_radius=ft.border_radius.all(10),
                bgcolor=ft.colors.TEAL_50,
                width=300,
                height=90,
                alignment=ft.alignment.center
            )
        back_button = ft.ElevatedButton(
            text="Enrere",
            icon=ft.icons.ARROW_BACK,
            on_click=user_menu,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.TEAL_700,
                color=ft.colors.WHITE,
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
            )
        )
        if current_session["account"][0]["user-license"] == "tutor":
            student_info_section = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Informació de la classe", size=26, weight="bold",
                                color=ft.colors.TEAL_800, text_align=ft.TextAlign.CENTER),
                        ft.Column(
                            controls=[
                                create_info_card(
                                    "Tutor", tutor_name, "school", False, False),
                                create_info_card(
                                    "Alumnat", "Alumnes de la classe", "school", True, view_educational_staff),  # Por cambiar
                                create_location_card(),
                            ],
                            spacing=15,
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        ft.Row(
                            controls=[back_button],
                            alignment=ft.MainAxisAlignment.CENTER,
                        )
                    ],
                    spacing=20,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                alignment=ft.alignment.center,
                padding=ft.padding.symmetric(vertical=20),
                expand=True,
            )
        elif current_session["account"][0]["user-license"] == "parent":
            student_info_section = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Informació de l'alumne", size=26, weight="bold",
                                color=ft.colors.TEAL_800, text_align=ft.TextAlign.CENTER),
                        ft.Column(
                            controls=[
                                create_info_card(
                                    "Alumne", student_name, "person", False, False),
                            ],
                            spacing=15,
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        ft.Text("Informació de la classe", size=26, weight="bold",
                                color=ft.colors.TEAL_800, text_align=ft.TextAlign.CENTER),
                        ft.Column(
                            controls=[
                                create_info_card(
                                    "Tutor", tutor_name, "school", False, False),
                                create_location_card(),
                            ],
                            spacing=15,
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        ft.Row(
                            controls=[back_button],
                            alignment=ft.MainAxisAlignment.CENTER,
                        )
                    ],
                    spacing=20,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                alignment=ft.alignment.center,
                padding=ft.padding.symmetric(vertical=20),
                expand=True,
            )
        stack.controls.append(student_info_section)
        page.update()

    def view_educational_staff(e=None):  # Cambiado
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        alumns_table_info = []

        def create_table_row(alumnId, name, firstSurname, secondSurname):
            return ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(alumnId)),
                    ft.DataCell(ft.Text(name)),
                    ft.DataCell(ft.Text(firstSurname)),
                    ft.DataCell(ft.Text(secondSurname)),
                ])
        for i in range(len(current_session["sub-account"])):
            alumns_table_info.append(create_table_row(str(current_session["sub-account"][i]["alumn_id"]), current_session["sub-account"]
                                     [i]["name"], current_session["sub-account"][i]["first-surname"], current_session["sub-account"][i]["second-surname"]))
        table = ft.ResponsiveRow(
            controls=[
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Id d'alumne")),
                        ft.DataColumn(ft.Text("Nom")),
                        ft.DataColumn(ft.Text("Primer cognom")),
                        ft.DataColumn(ft.Text("Segon cognom")),
                    ],
                    rows=alumns_table_info,
                )],
            alignment=ft.MainAxisAlignment.CENTER,
            # scroll=ft.ScrollMode.ALWAYS
        )
        back_button = ft.ElevatedButton(
            text="Enrere",
            icon=ft.icons.ARROW_BACK,
            on_click=settings_sub_account_page,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.TEAL_700,
                color=ft.colors.WHITE,
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
            )
        )
        stack.controls.append(ft.Column(controls=[
            table, back_button
        ], scroll=ft.ScrollMode.AUTO))
        # page.add(table)
        # page.add(back_button)
        page.update()

    def user_select_page(e=None):  # Cambiado
        stack.controls.clear()
        page.clean()
        # background_image()
        # background_opacity()
        accounts_buttons = []
        page.add(ft.Row(
            controls=[ft.Text("Selecció de compte", size=32, weight="bold",
                              color=ft.colors.BLACK, text_align=ft.TextAlign.CENTER)],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        ),
            ft.Container(height=10))
        for i in range(len(current_session["sub-account"])):
            sub_account_name = f"{current_session['sub-account'][i]['name']} {current_session['sub-account'][i]['first-surname']} {current_session['sub-account'][i]['second-surname']}"
            accounts_buttons.append(create_uniform_button(
                "./avatar.png", sub_account_name, current_session["sub-account"][i]["alumn_id"], True, 60, 60))
        for i in range(0, len(accounts_buttons), 2):
            row = ft.Row(
                controls=accounts_buttons[i:i + 2],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0
            )
            page.add(row)
        page.update()

    def calendar_page(e=None):
        # page.clean()
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        current_user()
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        calendar_column_spacing = 60 if page.platform == ft.PagePlatform.WINDOWS else 20
        row_spacing = 0
        months = [
            "Gener", "Febrer", "Març", "Abril", "Maig", "Juny",
            "Juliol", "Agost", "Setembre", "Octubre", "Novembre", "Desembre"
        ]
        days_of_week = ["Dl", "Dt", "Dc", "Dj", "Dv", "Ds", "Dg"]
        selected_month = ft.Text(value=months[current_month - 1], size=22)
        selected_year = ft.Text(value=str(current_year), size=22)
        calendar_width = len(days_of_week) * (calendar_column_spacing + 30)
        calendar_table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(day, size=16, text_align=ft.TextAlign.CENTER))
                     for day in days_of_week],
            rows=[],
            column_spacing=calendar_column_spacing,
            heading_row_height=60,
            horizontal_lines=ft.BorderSide(4, "white"),
            width=calendar_width,
        )
        updating_calendar = False
        if current_session["account"][0]["user-license"] == "parent":
            for i in classes:
                if i["class_id"] == current_session["sub-account-active"][0]["class_id"]:
                    events = i["events"]
        elif current_session["account"][0]["user-license"] == "tutor":
            for j in classes:
                if j["class_id"] == current_session["account"][0]["class_id"]:
                    events = j["events"]
        dialog = ft.AlertDialog()
        # page.add(dialog)
        event_title = ft.TextField(label="Títol", autofocus=False)
        event_description = ft.TextField(
            label="Descripció", multiline=True)

        def update_calendar(month, year):
            nonlocal updating_calendar
            updating_calendar = True
            calendar_table.rows.clear()
            first_day_of_month = datetime(year, month, 1)
            last_day_of_month = (datetime(year, month + 1, 1) -
                                 timedelta(days=1)).day if month < 12 else 31
            start_weekday = first_day_of_month.weekday()
            previous_month_days = [""] * start_weekday
            current_month_days = list(range(1, last_day_of_month + 1))
            next_month_days = [""] * \
                (42 - len(previous_month_days + current_month_days))
            days = previous_month_days + current_month_days + next_month_days
            weeks = [days[i:i + 7] for i in range(0, len(days), 7)]
            for week in weeks:
                row = ft.DataRow(
                    cells=[ft.DataCell(
                        ft.Container(
                            content=ft.Text(
                                str(day) if day != "" else "",
                                color=ft.colors.LIGHT_BLUE_ACCENT_700 if isinstance(day, int) and f"{year}-{month:02d}-{day:02d}" in events else (
                                    ft.colors.RED if isinstance(day, int) and datetime(
                                        year, month, day).weekday() in [5, 6] else ft.colors.BLACK
                                ),
                                size=16,
                                weight="bold" if isinstance(
                                    day, int) and f"{year}-{month:02d}-{day:02d}" in events else None,
                            ),
                            alignment=ft.alignment.center,
                            bgcolor=ft.colors.ORANGE_200 if isinstance(
                                day, int) and f"{year}-{month:02d}-{day:02d}" in events else ft.colors.TRANSPARENT,
                            border_radius=ft.border_radius.all(8),
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=4,
                                color=ft.colors.ORANGE_200,
                            ) if isinstance(day, int) and f"{year}-{month:02d}-{day:02d}" in events else None,
                            on_click=lambda e, d=day: manage_events(d),
                        ),
                    ) for day in week]
                )
                calendar_table.rows.append(row)
                calendar_table.rows.append(ft.DataRow(
                    cells=[ft.DataCell(ft.Container(height=row_spacing))] * 7, ))
            updating_calendar = False
            page.update()
        # Definición de navegación entre meses

        def previous_month(e=None):
            nonlocal current_month, current_year
            if updating_calendar:
                return
            if current_month == 1:
                current_month = 12
                current_year -= 1
            else:
                current_month -= 1
            selected_month.value = months[current_month - 1]
            selected_year.value = str(current_year)
            update_calendar(current_month, current_year)

        def next_month(e=None):
            nonlocal current_month, current_year
            if updating_calendar:
                return
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1
            selected_month.value = months[current_month - 1]
            selected_year.value = str(current_year)
            update_calendar(current_month, current_year)
        header_container = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(icon=ft.icons.ARROW_BACK,
                                  on_click=previous_month, icon_size=20),
                    ft.Container(
                        content=ft.Row(
                            [selected_month, selected_year],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        width=160,
                    ),
                    ft.IconButton(icon=ft.icons.ARROW_FORWARD,
                                  on_click=next_month, icon_size=20),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
        )

        def on_pan_end(e):
            """Detecta la dirección al finalizar el deslizamiento"""
            if updating_calendar:
                return
            if e.velocity_x < -0.5:  # Deslizar #hacia la izquierda
                next_month()
            elif e.velocity_x > 0.5:  # Deslizar hacia la derecha
                previous_month()
        swipe_detector = ft.GestureDetector(
            on_pan_end=on_pan_end,
            content=ft.Container(
                content=ft.Column(
                    controls=[header_container, calendar_table],
                    spacing=20,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                border=ft.border.all(1, ft.colors.WHITE),
                border_radius=ft.border_radius.all(10),
                bgcolor=ft.colors.WHITE,
                alignment=ft.alignment.center,
                width=calendar_width + 20,
                padding=10,
            ),
        )

        def save_edit(e, edit_event_title, edit_event_description, event_date_key, index, day):
            if edit_event_title.value.strip():
                # Guardar los cambios en el evento
                events[event_date_key][index]["title"] = edit_event_title.value.strip()
                events[event_date_key][index]["description"] = edit_event_description.value.strip(
                )
                update_calendar(current_month, current_year)
                close_dialog(e)
                time.sleep(0.01)
                manage_events(day)
                escribir_csv(parents, PARENTS_FILE_ID, "Parents.csv")
                escribir_csv(classes, CLASSES_FILE_ID, "Classes.csv")
                escribir_csv(alumns, ALUMNS_FILE_ID, "Alumns.csv")
                escribir_csv(tutors, TUTORS_FILE_ID, "Tutors.csv")
                escribir_csv(alumns_to_parents, ALUMNS_TO_PARENTS_FILE_ID,
                             "Alumns_to_Parents.csv")

                page.update()

        def edit_event(e, index, day):
            selected_date = datetime(current_year, current_month, day)
            event_date_key = selected_date.strftime("%Y-%m-%d")
            """Actualiza el contenido del diálogo para editar un evento existente."""
            event = events[event_date_key][index]
            # Crear campos de edición
            edit_event_title = ft.TextField(
                label="Títol", value=event["title"], autofocus=False)
            edit_event_description = ft.TextField(
                label="Descripció", value=event["description"], multiline=True)
            dialog.title = ft.Text(
                f"Editar esdeveniment - {selected_date.strftime('%d/%m/%Y')}")
            dialog.content = ft.Column(
                controls=[edit_event_title,
                          edit_event_description,
                          ft.Row(
                              controls=[
                                  ft.ElevatedButton(
                                      "Guardar", on_click=lambda e, t=edit_event_title, desc=edit_event_description, dk=event_date_key, idx=index, d=day: save_edit(e, t, desc, dk, idx, d)),
                                  ft.ElevatedButton(
                                      "Cancelar", on_click=lambda e, d=day: cancel_edit(e, d)),
                              ],
                              spacing=10,
                          ),
                          ],
                spacing=10,
            )
            page.update()

        def cancel_edit(e, day):
            close_dialog(e)
            time.sleep(0.01)
            manage_events(day)

        def manage_events(day):
            if day == "" or not isinstance(day, int):
                return
            selected_date = datetime(current_year, current_month, day)
            event_date_key = selected_date.strftime("%Y-%m-%d")
            open_event_dialog(day)

        def add_event(e, day):
            selected_date = datetime(current_year, current_month, day)
            event_date_key = selected_date.strftime("%Y-%m-%d")
            print(event_title.value)
            print(event_title.value.strip())
            for j in classes:
                if j["class_id"] == current_session["account"][0]["class_id"]:
                    if event_title.value.strip():
                        j["events"].setdefault(event_date_key, []).append({
                            "title": event_title.value.strip(),
                            "description": event_description.value.strip()
                        })
                        event_title.value = ""
                        event_description.value = ""
                        update_event_list(day)
                        update_calendar(current_month, current_year)
                        close_dialog(e)
                        time.sleep(0.01)
                        manage_events(day)
                        escribir_csv(parents, PARENTS_FILE_ID, "Parents.csv")
                        escribir_csv(classes, CLASSES_FILE_ID, "Classes.csv")
                        escribir_csv(alumns, ALUMNS_FILE_ID, "Alumns.csv")
                        escribir_csv(tutors, TUTORS_FILE_ID, "Tutors.csv")
                        escribir_csv(alumns_to_parents, ALUMNS_TO_PARENTS_FILE_ID,
                                     "Alumns_to_Parents.csv")
                        page.update()

        def delete_event(e, index, day):
            selected_date = datetime(current_year, current_month, day)
            event_date_key = selected_date.strftime("%Y-%m-%d")
            events[event_date_key].pop(index)
            if not events[event_date_key]:
                del events[event_date_key]
            update_event_list(day)
            update_calendar(current_month, current_year)
            close_dialog(e)
            time.sleep(0.01)
            manage_events(day)
            escribir_csv(parents, PARENTS_FILE_ID, "Parents.csv")
            escribir_csv(classes, CLASSES_FILE_ID, "Classes.csv")
            escribir_csv(alumns, ALUMNS_FILE_ID, "Alumns.csv")
            escribir_csv(tutors, TUTORS_FILE_ID, "Tutors.csv")
            escribir_csv(alumns_to_parents, ALUMNS_TO_PARENTS_FILE_ID,
                         "Alumns_to_Parents.csv")
            page.update()

        def update_event_list(day):
            selected_date = datetime(current_year, current_month, day)
            event_date_key = selected_date.strftime("%Y-%m-%d")
            event_list.controls.clear()
            if current_session["account"][0]["user-license"] != "tutor":
                for i, event in enumerate(events.get(event_date_key, [])):
                    event_controls = ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(event["title"],
                                            size=18, weight="bold"),
                                    ft.Text(event["description"], size=16),
                                ],
                                expand=True,
                            ),
                        ],
                    )
                    event_list.controls.append(event_controls)
                    event_list.controls.append(ft.Divider())
            else:
                for i, event in enumerate(events.get(event_date_key, [])):
                    event_controls = ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(event["title"],
                                            size=18, weight="bold"),
                                    ft.Text(event["description"], size=16),
                                ],
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.icons.EDIT,
                                on_click=lambda e, idx=i, d=day: edit_event(
                                    e, idx, d),
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                on_click=lambda e, idx=i, d=day: delete_event(
                                    e, idx, d),
                            ),
                        ],
                    )
                    event_list.controls.append(event_controls)
                    event_list.controls.append(ft.Divider())
            page.update()

        def close_dialog(e):
            print(e)
            dialog.open = False
            page.update()

        def close_dialog_definitivo(e):
            print(e)
            dialog.open = False
            time.sleep(0.01)
            page.update()

        def open_event_dialog(day):
            selected_date = datetime(current_year, current_month, day)
            update_event_list(day)
            add_event_tab = ft.Column(
                controls=[
                    ft.Text("Afegeix un nou esdeveniment",
                            weight="bold", size=20, text_align=ft.TextAlign.CENTER),
                    event_title,
                    event_description,
                    ft.ElevatedButton("Afegir", on_click=lambda e,
                                      d=day: add_event(e, d)),
                ],
                spacing=10,
            )
            view_events_tab = ft.Container(
                content=ft.Column(
                    controls=[event_list],
                    spacing=10,
                ),
            )
            if current_session["account"][0]["user-license"] != "tutor":
                tabs = ft.Tabs(
                    selected_index=0,
                    tabs=[
                        # ft.Tab(text="Afegir esdeveniment",
                        #        content=add_event_tab),
                        ft.Tab(text="Esdeveniments existents",
                               content=view_events_tab),
                    ],
                )
            else:
                tabs = ft.Tabs(
                    selected_index=0,
                    tabs=[
                        ft.Tab(text="Afegir esdeveniment",
                               content=add_event_tab),
                        ft.Tab(text="Esdeveniments existents",
                               content=view_events_tab),
                    ],
                )
            dialog.title = ft.Text(
                f"Esdeveniments - {selected_date.strftime('%d/%m/%Y')}")
            dialog.content = tabs
            dialog.open = True
            # stack.controls.append()
            page.dialog = dialog
            page.update()
        dialog.actions = [
            ft.ElevatedButton(
                "Tancar", on_click=lambda e: close_dialog_definitivo(e)),
        ]
        event_list = ft.Column(scroll="auto")
        update_calendar(current_month, current_year)
        stack.controls.append(ft.Container(content=ft.Column(controls=[swipe_detector,
                                                                       ft.ElevatedButton(
                                                                           "Torna a l'inici",
                                                                           on_click=home_page,
                                                                           style=ft.ButtonStyle(
                                                                               color=ft.colors.PRIMARY,
                                                                           ),
                                                                       )
                                                                       ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                             alignment=ft.MainAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO), alignment=ft.alignment.center))
        page.update()

    def informes_page(e=None):  # Página rediseñada

        stack.controls.clear()
        background_image()
        create_app_bar()
        current_user()
        # Estilo para el fondo de la página
        page.bgcolor = "#f4f6f9"  # Fondo claro para una apariencia moderna
        # Añadir controles a la página
        stack.controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ElevatedButton(
                            text="Informes primer trimestre",
                            on_click=informes_page_first_term,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=15),
                                color=ft.colors.WHITE,
                                bgcolor=ft.colors.PRIMARY,
                                elevation=6,
                            ),
                            width=300,
                            height=60,
                        ),
                        ft.ElevatedButton(
                            text="Informes segon trimestre",
                            on_click=informes_page_second_term,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=15),
                                color=ft.colors.WHITE,
                                bgcolor=ft.colors.SECONDARY,
                                elevation=6,
                            ),
                            width=300,
                            height=60,
                        ),
                        ft.ElevatedButton(
                            text="Informes tercer trimestre",
                            on_click=informes_page_third_term,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=15),
                                color=ft.colors.WHITE,
                                bgcolor=ft.colors.TERTIARY,
                                elevation=6,
                            ),
                            width=300,
                            height=60,
                        ), ft.Container(
                            content=ft.ResponsiveRow(
                                controls=[
                                    ft.Column(
                                        controls=[
                                            ft.ElevatedButton(
                                                "Torna a l'inici", bgcolor=ft.Colors.INDIGO_500, color=ft.Colors.WHITE, on_click=home_page)
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            margin=ft.Margin(
                                top=20, left=0, right=0, bottom=0),
                        ),
                    ],
                    spacing=20,
                    expand=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=30,
                alignment=ft.alignment.center
            ),
            # Fila de navegación para volver a la página de inicio
        )
        page.update()

    def informes_page_first_term(e=None):
        stack.controls.clear()
        background_image()
        create_app_bar()
        current_user()
        # Contenedor principal con scroll
        content = ft.Column(scroll="auto", height=350,
                            width=page.width, expand=True, horizontal_alignment=ft.CrossAxisAlignment.START)

        def load_pdf(e):
            file_picker = ft.FilePicker(
                on_result=cargar_archivos_pdf)
            page.overlay.append(file_picker)
            page.add(file_picker)
            file_picker.pick_files(allow_multiple=True)

        def cargar_archivos_pdf(e):
            """Sube múltiples archivos PDF desde el dispositivo"""
            if e.files:

                subir_y_compartir_archivos(
                    e.files,  # Lista de archivos seleccionados
                    ["taborinfo@tabor.cat"],  # Emails propietarios
                )
        # Subir el PDF al servidor

        def compartir_archivo_con_enlace(file_id, emails_propietarios):
            """Hacer el archivo accesible con el enlace y compartirlo con propietarios"""
            permiso = {
                'type': 'anyone',  # Cualquier persona
                'role': 'reader'   # Solo lectura
            }

            # Crear el permiso de acceso público con enlace
            drive_service.permissions().create(
                fileId=file_id,
                body=permiso
            ).execute()

            # Ahora compartimos el archivo con los propietarios específicos por su email
            for email in emails_propietarios:
                permiso_propietario = {
                    'type': 'user',  # Tipo de permiso para un usuario específico
                    'role': 'reader',  # Rol de propietario
                    'emailAddress': email,
                    # 'transferOwnership': True  # Habilita la transferencia de propiedad
                }

                try:
                    drive_service.permissions().create(
                        fileId=file_id,
                        body=permiso_propietario
                    ).execute()
                    print(f"Archivo compartido con el propietario: {email}")
                except HttpError as error:
                    print(f"No se pudo compartir con {email}: {error}")

            print("Archivo ahora es accesible con el enlace y con los propietarios.")

        # Función para subir un archivo PDF y compartirlo

        def subir_y_compartir_archivos(files, emails_propietarios):
            """Sube múltiples archivos PDF a una carpeta de Google Drive, los comparte y transfiere propiedad"""
            for i in classes:
                if i["class_id"] == current_session["account"][0]["class_id"]:
                    folder_id = i["reports"]["first-term"]["folder_id"]
            file_ids = []  # Lista para almacenar los IDs de los archivos subidos

            for file in files:
                file_path = file.path
                file_name = file.name

                # Metadatos del archivo, incluyendo la carpeta destino
                file_metadata = {
                    'name': file_name,
                    'parents': [folder_id]  # ID de la carpeta de destino
                }

                # Subir el archivo a Google Drive
                media = MediaFileUpload(file_path, mimetype="application/pdf")

                archivo_subido = drive_service.files().create(
                    body=file_metadata,
                    media_body=media
                ).execute()

                # Obtener el ID del archivo subido
                file_id = archivo_subido['id']
                file_ids.append(file_id)
                print(
                    f"Archivo '{file_name}' subido con ID: {file_id} en la carpeta {folder_id}")

                for i in classes:
                    if i["class_id"] == current_session["account"][0]["class_id"]:
                        i["reports"]["first-term"]["reports"].append(
                            {'file_id': file_id, 'file_name': file_name})
                        for j in alumns:
                            full_name = f"{j['name']} {j['first-surname']} {j['second-surname']}"
                            pdf_alumn_name = []
                            remove_term = re.sub("first_term_", "", file.name)
                            pdf_alumn_name.append(remove_term)
                            if FindMatches([full_name, pdf_alumn_name[0]]):
                                j["report-first-term"].append(
                                    {'file_id': file_id, 'file_name': file_name})

                # Hacerlo accesible con el enlace y compartirlo con propietarios
                compartir_archivo_con_enlace(file_id, emails_propietarios)

                # Transferir la propiedad del archivo
            escribir_csv(parents, PARENTS_FILE_ID, "Parents.csv")
            escribir_csv(classes, CLASSES_FILE_ID, "Classes.csv")
            escribir_csv(alumns, ALUMNS_FILE_ID, "Alumns.csv")
            escribir_csv(tutors, TUTORS_FILE_ID, "Tutors.csv")
            escribir_csv(alumns_to_parents, ALUMNS_TO_PARENTS_FILE_ID,
                         "Alumns_to_Parents.csv")
            return file_ids  # Devuelve la lista de IDs de los archivos subidos

        def redirect_to_pdf_images(pdf_id):

            pdf_url = f"https://drive.google.com/file/d/{pdf_id}/view"
            page.launch_url(pdf_url)  # Abrir la URL en una nueva ventana

        def load_existing_pdfs():
            if current_session["account"][0]["user-license"] == "parent":
                print(current_session["sub-account-active"])
                if not current_session["sub-account-active"][0]["report-first-term"]:
                    pdf_files = []
                else:
                    pdf_files = [current_session["sub-account-active"]
                                 [0]["report-first-term"][0]]
            elif current_session["account"][0]["user-license"] == "tutor":
                for i in classes:
                    print(i)
                    if i["class_id"] == current_session["account"][0]["class_id"]:
                        print(i["reports"]["first-term"]["reports"])
                        pdf_files = i["reports"]["first-term"]["reports"]
            for pdf_file in pdf_files:
                pdf_alumn_name = []
                remove_term = re.sub("first_term_", "", pdf_file["file_name"])
                pdf_alumn_name.append(remove_term)
                remove_extension = re.sub(".pdf", "", pdf_alumn_name[0])
                pdf_alumn_name.clear()
                pdf_alumn_name.append(remove_extension)
                pdf_id = pdf_file["file_id"]
                content.controls.append(
                    ft.ElevatedButton(
                        text=f"{pdf_alumn_name[0]}",
                        on_click=lambda e, pdf_name=pdf_id: redirect_to_pdf_images(
                            pdf_name),
                        width=page.width,
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE_100, color="black", shape=ft.RoundedRectangleBorder(radius=10)
                        )
                    )
                )
            page.update()
        # # Cargar PDFs existentes al inicio
        load_existing_pdfs()
        # # Botón para cargar un nuevo PDF
        load_button = ft.ElevatedButton(
            "Cargar PDF",
            on_click=load_pdf,
            style=ft.ButtonStyle(
                bgcolor="orange", color="black"
            )
        )
        # Configuración visual según el tipo de usuario
        main_container = ft.Column(
            controls=[
                ft.Text("Gestió d'informes del primer trimestre",
                        size=24, weight="bold", color="darkblue"),
                ft.Divider(height=2, color="lightgrey"),
                content,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
            spacing=20
        )
        footer_buttons = ft.Row(
            controls=[
                load_button,
                ft.ElevatedButton(
                    "Torna a l'inici", bgcolor=ft.Colors.INDIGO_500, color=ft.Colors.WHITE, on_click=informes_page)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        if current_session["account"][0]["user-license"] == "parent":
            stack.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[ft.Container(height=50), main_container, ft.ElevatedButton(
                            "Torna a l'inici", bgcolor=ft.Colors.INDIGO_500, color=ft.Colors.WHITE, on_click=informes_page)],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=30
                    ),
                    padding=20
                )
            )
        elif current_session["account"][0]["user-license"] == "tutor":
            stack.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[ft.Container(
                            height=50), main_container, footer_buttons],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=30
                    ),
                    padding=20
                )
            )
        page.update()

    def informes_page_second_term(e=None):
        stack.controls.clear()
        background_image()
        create_app_bar()
        current_user()
        content = ft.Column(scroll="auto", height=350,
                            width=page.width, expand=True, horizontal_alignment=ft.CrossAxisAlignment.START)

        def load_pdf(e):
            file_picker = ft.FilePicker(
                on_result=cargar_archivos_pdf)
            page.overlay.append(file_picker)
            page.add(file_picker)
            file_picker.pick_files(allow_multiple=True)

        def cargar_archivos_pdf(e):
            """Sube múltiples archivos PDF desde el dispositivo"""
            if e.files:

                subir_y_compartir_archivos(
                    e.files,  # Lista de archivos seleccionados
                    ["taborinfo@tabor.cat"],  # Emails propietarios
                )
        # Subir el PDF al servidor

        def compartir_archivo_con_enlace(file_id, emails_propietarios):
            """Hacer el archivo accesible con el enlace y compartirlo con propietarios"""
            permiso = {
                'type': 'anyone',  # Cualquier persona
                'role': 'reader'   # Solo lectura
            }

            # Crear el permiso de acceso público con enlace
            drive_service.permissions().create(
                fileId=file_id,
                body=permiso
            ).execute()

            # Ahora compartimos el archivo con los propietarios específicos por su email
            for email in emails_propietarios:
                permiso_propietario = {
                    'type': 'user',  # Tipo de permiso para un usuario específico
                    'role': 'reader',  # Rol de propietario
                    'emailAddress': email,
                    # 'transferOwnership': True  # Habilita la transferencia de propiedad
                }

                try:
                    drive_service.permissions().create(
                        fileId=file_id,
                        body=permiso_propietario
                    ).execute()
                    print(f"Archivo compartido con el propietario: {email}")
                except HttpError as error:
                    print(f"No se pudo compartir con {email}: {error}")

            print("Archivo ahora es accesible con el enlace y con los propietarios.")

        # Función para subir un archivo PDF y compartirlo

        def subir_y_compartir_archivos(files, emails_propietarios):
            """Sube múltiples archivos PDF a una carpeta de Google Drive, los comparte y transfiere propiedad"""
            for i in classes:
                if i["class_id"] == current_session["account"][0]["class_id"]:
                    folder_id = i["reports"]["second-term"]["folder_id"]
            file_ids = []  # Lista para almacenar los IDs de los archivos subidos

            for file in files:
                file_path = file.path
                file_name = file.name

                # Metadatos del archivo, incluyendo la carpeta destino
                file_metadata = {
                    'name': file_name,
                    'parents': [folder_id]  # ID de la carpeta de destino
                }

                # Subir el archivo a Google Drive
                media = MediaFileUpload(file_path, mimetype="application/pdf")

                archivo_subido = drive_service.files().create(
                    body=file_metadata,
                    media_body=media
                ).execute()

                # Obtener el ID del archivo subido
                file_id = archivo_subido['id']
                file_ids.append(file_id)
                print(
                    f"Archivo '{file_name}' subido con ID: {file_id} en la carpeta {folder_id}")

                for i in classes:
                    if i["class_id"] == current_session["account"][0]["class_id"]:
                        i["reports"]["second-term"]["reports"].append(
                            {'file_id': file_id, 'file_name': file_name})
                        for j in alumns:
                            full_name = f"{j['name']} {j['first-surname']} {j['second-surname']}"
                            pdf_alumn_name = []
                            remove_term = re.sub("second_term_", "", file.name)
                            pdf_alumn_name.append(remove_term)
                            if FindMatches([full_name, pdf_alumn_name[0]]):
                                j["report-second-term"].append(
                                    {'file_id': file_id, 'file_name': file_name})

                # Hacerlo accesible con el enlace y compartirlo con propietarios
                compartir_archivo_con_enlace(file_id, emails_propietarios)

                # Transferir la propiedad del archivo
            escribir_csv(parents, PARENTS_FILE_ID, "Parents.csv")
            escribir_csv(classes, CLASSES_FILE_ID, "Classes.csv")
            escribir_csv(alumns, ALUMNS_FILE_ID, "Alumns.csv")
            escribir_csv(tutors, TUTORS_FILE_ID, "Tutors.csv")
            escribir_csv(alumns_to_parents, ALUMNS_TO_PARENTS_FILE_ID,
                         "Alumns_to_Parents.csv")
            return file_ids  # Devuelve la lista de IDs de los archivos subidos

        def redirect_to_pdf_images(pdf_id):

            pdf_url = f"https://drive.google.com/file/d/{pdf_id}/view"
            page.launch_url(pdf_url)  # Abrir la URL en una nueva ventana

        def load_existing_pdfs():
            if current_session["account"][0]["user-license"] == "parent":
                if not current_session["sub-account-active"][0]["report-second-term"]:
                    pdf_files = []
                else:
                    pdf_files = [current_session["sub-account-active"]
                                 [0]["report-second-term"][0]]
            elif current_session["account"][0]["user-license"] == "tutor":
                for i in classes:
                    print(i)
                    if i["class_id"] == current_session["account"][0]["class_id"]:
                        print(i["reports"]["second-term"]["reports"])
                        pdf_files = i["reports"]["second-term"]["reports"]
            for pdf_file in pdf_files:
                pdf_alumn_name = []
                remove_term = re.sub("second_term_", "", pdf_file["file_name"])
                pdf_alumn_name.append(remove_term)
                remove_extension = re.sub(".pdf", "", pdf_alumn_name[0])
                pdf_alumn_name.clear()
                pdf_alumn_name.append(remove_extension)
                pdf_id = pdf_file["file_id"]
                content.controls.append(
                    ft.ElevatedButton(
                        text=f"{pdf_alumn_name[0]}",
                        on_click=lambda e, pdf_name=pdf_id: redirect_to_pdf_images(
                            pdf_name),
                        width=page.width,
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE_100, color="black", shape=ft.RoundedRectangleBorder(radius=10)
                        )
                    )
                )
            page.update()
        # # Cargar PDFs existentes al inicio
        load_existing_pdfs()
        # # Botón para cargar un nuevo PDF
        load_button = ft.ElevatedButton(
            "Cargar PDF",
            on_click=load_pdf,
            style=ft.ButtonStyle(
                bgcolor="orange", color="black"
            )
        )
        # Configuración visual según el tipo de usuario
        main_container = ft.Column(
            controls=[
                ft.Text("Gestió d'informes del segon trimestre",
                        size=24, weight="bold", color="darkblue"),
                ft.Divider(height=2, color="lightgrey"),
                content,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
            spacing=20
        )
        footer_buttons = ft.Row(
            controls=[
                load_button,
                ft.ElevatedButton(
                    "Torna a l'inici", bgcolor=ft.Colors.INDIGO_500, color=ft.Colors.WHITE, on_click=informes_page)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        if current_session["account"][0]["user-license"] == "parent":
            stack.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[ft.Container(height=50), main_container, ft.ElevatedButton(
                            "Torna a l'inici", bgcolor=ft.Colors.INDIGO_500, color=ft.Colors.WHITE, on_click=informes_page)],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=30
                    ),
                    padding=20
                )
            )
        elif current_session["account"][0]["user-license"] == "tutor":
            stack.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[ft.Container(
                            height=50), main_container, footer_buttons],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=30
                    ),
                    padding=20
                )
            )
        page.update()

    def informes_page_third_term(e=None):
        stack.controls.clear()
        background_image()
        create_app_bar()
        current_user()
        content = ft.Column(scroll="auto", height=350,
                            width=page.width, expand=True, horizontal_alignment=ft.CrossAxisAlignment.START)

        def load_pdf(e):
            file_picker = ft.FilePicker(
                on_result=cargar_archivos_pdf)
            page.overlay.append(file_picker)
            page.add(file_picker)
            file_picker.pick_files(allow_multiple=True)

        def cargar_archivos_pdf(e):
            """Sube múltiples archivos PDF desde el dispositivo"""
            if e.files:

                subir_y_compartir_archivos(
                    e.files,  # Lista de archivos seleccionados
                    ["taborinfo@tabor.cat"],  # Emails propietarios
                )
        # Subir el PDF al servidor

        def compartir_archivo_con_enlace(file_id, emails_propietarios):
            """Hacer el archivo accesible con el enlace y compartirlo con propietarios"""
            permiso = {
                'type': 'anyone',  # Cualquier persona
                'role': 'reader'   # Solo lectura
            }

            # Crear el permiso de acceso público con enlace
            drive_service.permissions().create(
                fileId=file_id,
                body=permiso
            ).execute()

            # Ahora compartimos el archivo con los propietarios específicos por su email
            for email in emails_propietarios:
                permiso_propietario = {
                    'type': 'user',  # Tipo de permiso para un usuario específico
                    'role': 'reader',  # Rol de propietario
                    'emailAddress': email,
                    # 'transferOwnership': True  # Habilita la transferencia de propiedad
                }

                try:
                    drive_service.permissions().create(
                        fileId=file_id,
                        body=permiso_propietario
                    ).execute()
                    print(f"Archivo compartido con el propietario: {email}")
                except HttpError as error:
                    print(f"No se pudo compartir con {email}: {error}")

            print("Archivo ahora es accesible con el enlace y con los propietarios.")

        # Función para subir un archivo PDF y compartirlo

        def subir_y_compartir_archivos(files, emails_propietarios):
            """Sube múltiples archivos PDF a una carpeta de Google Drive, los comparte y transfiere propiedad"""
            for i in classes:
                if i["class_id"] == current_session["account"][0]["class_id"]:
                    folder_id = i["reports"]["third-term"]["folder_id"]
            file_ids = []  # Lista para almacenar los IDs de los archivos subidos

            for file in files:
                file_path = file.path
                file_name = file.name

                # Metadatos del archivo, incluyendo la carpeta destino
                file_metadata = {
                    'name': file_name,
                    'parents': [folder_id]  # ID de la carpeta de destino
                }

                # Subir el archivo a Google Drive
                media = MediaFileUpload(file_path, mimetype="application/pdf")

                archivo_subido = drive_service.files().create(
                    body=file_metadata,
                    media_body=media
                ).execute()

                # Obtener el ID del archivo subido
                file_id = archivo_subido['id']
                file_ids.append(file_id)
                print(
                    f"Archivo '{file_name}' subido con ID: {file_id} en la carpeta {folder_id}")

                for i in classes:
                    if i["class_id"] == current_session["account"][0]["class_id"]:
                        i["reports"]["third-term"]["reports"].append(
                            {'file_id': file_id, 'file_name': file_name})
                        for j in alumns:
                            full_name = f"{j['name']} {j['first-surname']} {j['second-surname']}"
                            pdf_alumn_name = []
                            remove_term = re.sub("third_term_", "", file.name)
                            pdf_alumn_name.append(remove_term)
                            if FindMatches([full_name, pdf_alumn_name[0]]):
                                j["report-third-term"].append(
                                    {'file_id': file_id, 'file_name': file_name})

                # Hacerlo accesible con el enlace y compartirlo con propietarios
                compartir_archivo_con_enlace(file_id, emails_propietarios)

                # Transferir la propiedad del archivo
            escribir_csv(parents, PARENTS_FILE_ID, "Parents.csv")
            escribir_csv(classes, CLASSES_FILE_ID, "Classes.csv")
            escribir_csv(alumns, ALUMNS_FILE_ID, "Alumns.csv")
            escribir_csv(tutors, TUTORS_FILE_ID, "Tutors.csv")
            escribir_csv(alumns_to_parents, ALUMNS_TO_PARENTS_FILE_ID,
                         "Alumns_to_Parents.csv")
            return file_ids  # Devuelve la lista de IDs de los archivos subidos

        def redirect_to_pdf_images(pdf_id):

            pdf_url = f"https://drive.google.com/file/d/{pdf_id}/view"
            page.launch_url(pdf_url)  # Abrir la URL en una nueva ventana

        def load_existing_pdfs():
            if current_session["account"][0]["user-license"] == "parent":
                if not current_session["sub-account-active"][0]["report-third-term"]:
                    pdf_files = []
                else:
                    pdf_files = [current_session["sub-account-active"]
                                 [0]["report-third-term"][0]]
            elif current_session["account"][0]["user-license"] == "tutor":
                for i in classes:
                    print(i)
                    if i["class_id"] == current_session["account"][0]["class_id"]:
                        print(i["reports"]["third-term"]["reports"])
                        pdf_files = i["reports"]["third-term"]["reports"]
            for pdf_file in pdf_files:
                pdf_alumn_name = []
                remove_term = re.sub("third_term_", "", pdf_file["file_name"])
                pdf_alumn_name.append(remove_term)
                remove_extension = re.sub(".pdf", "", pdf_alumn_name[0])
                pdf_alumn_name.clear()
                pdf_alumn_name.append(remove_extension)
                pdf_id = pdf_file["file_id"]
                content.controls.append(
                    ft.ElevatedButton(
                        text=f"{pdf_alumn_name[0]}",
                        on_click=lambda e, pdf_name=pdf_id: redirect_to_pdf_images(
                            pdf_name),
                        width=page.width,
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE_100, color="black", shape=ft.RoundedRectangleBorder(radius=10)
                        )
                    )
                )
            page.update()
        # # Cargar PDFs existentes al inicio
        load_existing_pdfs()
        # # Botón para cargar un nuevo PDF
        load_button = ft.ElevatedButton(
            "Cargar PDF",
            on_click=load_pdf,
            style=ft.ButtonStyle(
                bgcolor="orange", color="black"
            )
        )
        # Configuración visual según el tipo de usuario
        main_container = ft.Column(
            controls=[
                ft.Text("Gestió d'informes del tercer trimestre",
                        size=24, weight="bold", color="darkblue"),
                ft.Divider(height=2, color="lightgrey"),
                content,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
            spacing=20
        )
        footer_buttons = ft.Row(
            controls=[
                load_button,
                ft.ElevatedButton(
                    "Torna a l'inici", bgcolor=ft.Colors.INDIGO_500, color=ft.Colors.WHITE, on_click=informes_page)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        if current_session["account"][0]["user-license"] == "parent":
            stack.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[ft.Container(height=50), main_container, ft.ElevatedButton(
                            "Torna a l'inici", bgcolor=ft.Colors.INDIGO_500, color=ft.Colors.WHITE, on_click=informes_page)],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=30
                    ),
                    padding=20
                )
            )
        elif current_session["account"][0]["user-license"] == "tutor":
            stack.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[ft.Container(
                            height=50), main_container, footer_buttons],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=30
                    ),
                    padding=20
                )
            )
        page.update()

    def tasks_page(e=None):  # Por cambiar # Autorizaciones
        stack.controls.clear()
        background_image()
        create_app_bar()
        current_user()
        # Contenedor principal con scroll
        content = ft.Column(scroll="auto", height=350,
                            width=page.width, expand=True, horizontal_alignment=ft.CrossAxisAlignment.START)

        def load_pdf(e):
            file_picker = ft.FilePicker(
                on_result=cargar_archivos_pdf)
            page.overlay.append(file_picker)
            page.add(file_picker)
            file_picker.pick_files(allow_multiple=True)

        def cargar_archivos_pdf(e):
            """Sube múltiples archivos PDF desde el dispositivo"""
            if e.files:

                subir_y_compartir_archivos(
                    e.files,  # Lista de archivos seleccionados
                    ["taborinfo@tabor.cat"],  # Emails propietarios
                )
        # Subir el PDF al servidor

        def compartir_archivo_con_enlace(file_id, emails_propietarios):
            """Hacer el archivo accesible con el enlace y compartirlo con propietarios"""
            permiso = {
                'type': 'anyone',  # Cualquier persona
                'role': 'reader'   # Solo lectura
            }

            # Crear el permiso de acceso público con enlace
            drive_service.permissions().create(
                fileId=file_id,
                body=permiso
            ).execute()

            # Ahora compartimos el archivo con los propietarios específicos por su email
            for email in emails_propietarios:
                permiso_propietario = {
                    'type': 'user',  # Tipo de permiso para un usuario específico
                    'role': 'reader',  # Rol de propietario
                    'emailAddress': email,
                    # 'transferOwnership': True  # Habilita la transferencia de propiedad
                }

                try:
                    drive_service.permissions().create(
                        fileId=file_id,
                        body=permiso_propietario
                    ).execute()
                    print(f"Archivo compartido con el propietario: {email}")
                except HttpError as error:
                    print(f"No se pudo compartir con {email}: {error}")

            print("Archivo ahora es accesible con el enlace y con los propietarios.")

        # Función para subir un archivo PDF y compartirlo
        def subir_y_compartir_archivos(files, emails_propietarios):
            """Sube múltiples archivos PDF a una carpeta de Google Drive, los comparte y transfiere propiedad"""
            for i in classes:
                if i["class_id"] == current_session["account"][0]["class_id"]:
                    folder_id = i["authorizations_folder_id"]
            file_ids = []  # Lista para almacenar los IDs de los archivos subidos

            for file in files:
                file_path = file.path
                file_name = file.name

                # Metadatos del archivo, incluyendo la carpeta destino
                file_metadata = {
                    'name': file_name,
                    'parents': [folder_id]  # ID de la carpeta de destino
                }

                # Subir el archivo a Google Drive
                media = MediaFileUpload(file_path, mimetype="application/pdf")

                archivo_subido = drive_service.files().create(
                    body=file_metadata,
                    media_body=media
                ).execute()

                # Obtener el ID del archivo subido
                file_id = archivo_subido['id']
                file_ids.append(file_id)
                print(
                    f"Archivo '{file_name}' subido con ID: {file_id} en la carpeta {folder_id}")

                for i in classes:
                    if i["class_id"] == current_session["account"][0]["class_id"]:
                        i["authorizations"].append(
                            {'file_id': file_id, 'file_name': file_name})

                # Hacerlo accesible con el enlace y compartirlo con propietarios
                compartir_archivo_con_enlace(file_id, emails_propietarios)

                # Transferir la propiedad del archivo
            escribir_csv(parents, PARENTS_FILE_ID, "Parents.csv")
            escribir_csv(classes, CLASSES_FILE_ID, "Classes.csv")
            escribir_csv(alumns, ALUMNS_FILE_ID, "Alumns.csv")
            escribir_csv(tutors, TUTORS_FILE_ID, "Tutors.csv")
            escribir_csv(alumns_to_parents, ALUMNS_TO_PARENTS_FILE_ID,
                         "Alumns_to_Parents.csv")
            return file_ids  # Devuelve la lista de IDs de los archivos subidos

        def redirect_to_pdf_images(pdf_id):

            pdf_url = f"https://drive.google.com/file/d/{pdf_id}/view"
            page.launch_url(pdf_url)  # Abrir la URL en una nueva ventana

        def load_existing_pdfs():
            if current_session["account"][0]["user-license"] == "parent":
                for j in classes:
                    if j["class_id"] == current_session["sub-account-active"][0]["class_id"]:
                        pdf_files = j["authorizations"]
            elif current_session["account"][0]["user-license"] == "tutor":
                for i in classes:
                    if i["class_id"] == current_session["account"][0]["class_id"]:
                        pdf_files = i["authorizations"]

            for pdf_file in pdf_files:
                pdf_name = []

                remove_extension = re.sub(".pdf", "", pdf_file["file_name"])
                pdf_name.append(remove_extension)
                pdf_id = pdf_file["file_id"]
                content.controls.append(
                    ft.ElevatedButton(
                        text=f"{pdf_name[0]}",
                        on_click=lambda e, pdf_name=pdf_id: redirect_to_pdf_images(
                            pdf_name),
                        width=page.width,
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE_100, color="black", shape=ft.RoundedRectangleBorder(radius=10)
                        )
                    )
                )

            page.update()
        # # Cargar PDFs existentes al inicio
        load_existing_pdfs()
        # # Botón para cargar un nuevo PDF
        load_button = ft.ElevatedButton(
            "Cargar PDF",
            on_click=load_pdf,
            style=ft.ButtonStyle(
                bgcolor="orange", color="black"
            )
        )

        main_container = ft.Column(
            controls=[
                ft.Text("Gestió d'autoritzacions",
                        size=24, weight="bold", color="darkblue"),
                ft.Divider(height=2, color="lightgrey"),
                content,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
            spacing=20
        )
        footer_buttons = ft.Row(
            controls=[
                load_button,
                ft.ElevatedButton(
                    "Torna a l'inici", bgcolor=ft.Colors.INDIGO_500, color=ft.Colors.WHITE, on_click=home_page)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        if current_session["account"][0]["user-license"] == "parent":
            stack.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[ft.Container(height=50), main_container, ft.ElevatedButton(
                            "Torna a l'inici", bgcolor=ft.Colors.INDIGO_500, color=ft.Colors.WHITE, on_click=home_page)],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=30
                    ),
                    padding=20
                )
            )
        elif current_session["account"][0]["user-license"] == "tutor":
            stack.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[ft.Container(
                            height=50), main_container, footer_buttons],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=30
                    ),
                    padding=20
                )
            )
        page.update()

    def messages_page(e=None):  # Por cambiar # Avisos
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        current_user()
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        current_day = current_date.day
        notices_list = ft.Column(scroll="auto")
        if current_session["account"][0]["user-license"] == "parent":
            for i in classes:
                if i["class_id"] == current_session["sub-account-active"][0]["class_id"]:
                    notices = i["notices"]
                    class_key = i["class_id"]
        elif current_session["account"][0]["user-license"] == "tutor":
            for j in classes:
                if j["class_id"] == current_session["account"][0]["class_id"]:
                    notices = j["notices"]
                    class_key = j["class_id"]
        event_title = ft.TextField(label="Títol", autofocus=False)
        event_description = ft.TextField(
            label="Descripció", multiline=True)

        def add_event(e=None):
            selected_date = datetime(
                current_year, current_month, current_day)
            event_date_key = selected_date.strftime("%Y-%m-%d")
            print(event_title.value)
            print(event_title.value.strip())
            for j in classes:
                if j["class_id"] == current_session["account"][0]["class_id"]:
                    if event_title.value.strip():
                        j["notices"].append({
                            "title": event_title.value.strip(),
                            "description": event_description.value.strip(),
                            "date_added": event_date_key
                        })
                        event_title.value = ""
                        event_description.value = ""
                        update_event_list()
                        escribir_csv(parents, PARENTS_FILE_ID, "Parents.csv")
                        escribir_csv(classes, CLASSES_FILE_ID, "Classes.csv")
                        escribir_csv(alumns, ALUMNS_FILE_ID, "Alumns.csv")
                        escribir_csv(tutors, TUTORS_FILE_ID, "Tutors.csv")
                        escribir_csv(alumns_to_parents, ALUMNS_TO_PARENTS_FILE_ID,
                                     "Alumns_to_Parents.csv")
                        page.update()
        # def delete_event(e, index, day):
        #     selected_date = datetime(current_year, current_month, current_day)
        #     event_date_key = selected_date.strftime("%Y-%m-%d")
        #     events[event_date_key].pop(index)
        #     if not events[event_date_key]:
        #         del events[event_date_key]
        #     update_event_list(day)
        #     update_calendar(current_month, current_year)
        #     close_dialog(e)
        #     time.sleep(0.01)
        #     manage_events(day)
        #     escribir_csv(parents, PARENTS_FILE_ID, "Parents.csv")
            # escribir_csv(classes, CLASSES_FILE_ID, "Classes.csv")
            # escribir_csv(alumns, ALUMNS_FILE_ID, "Alumns.csv")
            # escribir_csv(tutors, TUTORS_FILE_ID, "Tutors.csv")
            # escribir_csv(alumns_to_parents, ALUMNS_TO_PARENTS_FILE_ID,
            #              "Alumns_to_Parents.csv")
        #     page.update()

        def update_event_list(e=None):
            selected_date = datetime(
                current_year, current_month, current_day)
            event_date_key = selected_date.strftime("%Y-%m-%d")
            notices_list.controls.clear()
            if current_session["account"][0]["user-license"] != "tutor":
                for notice in notices:
                    event_controls = ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(notice["title"],
                                            size=18, weight="bold"),
                                    ft.Text(
                                        notice["description"], size=16),
                                ],
                                expand=True,
                            ),
                        ],
                    )
                    notices_list.controls.append(event_controls)
                    notices_list.controls.append(ft.Divider())
                    page.update()
            else:
                for notice in notices:
                    event_controls = ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(notice["title"],
                                            size=18, weight="bold"),
                                    ft.Text(
                                        notice["description"], size=16),
                                ],
                                expand=True,
                            ),
                            # ft.IconButton(
                            #     icon=ft.icons.EDIT,
                            #     on_click=lambda e, idx=i, d=day: edit_event(
                            #         e, idx, d),
                            # ),
                            # ft.IconButton(
                            #     icon=ft.icons.DELETE,
                            #     on_click=lambda e, idx=i, d=day: delete_event(
                            #         e, idx, d),
                            # ),
                        ],
                    )
                    notices_list.controls.append(event_controls)
                    notices_list.controls.append(ft.Divider())
                    page.update()
            page.update()
        update_event_list()
        back_button = ft.Container(
            content=ft.ResponsiveRow(
                controls=[
                    ft.Column(
                        controls=[
                            ft.ElevatedButton(
                                "Torna a l'inici", bgcolor=ft.Colors.INDIGO_500, color=ft.Colors.WHITE, on_click=home_page)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            margin=ft.Margin(
                top=20, left=0, right=0, bottom=0),
        )
        add_event_tab = ft.Column(
            controls=[
                ft.Text("Afegeix un nou avís",
                        weight="bold", size=20, text_align=ft.TextAlign.CENTER),
                event_title,
                event_description,
                ft.ElevatedButton("Afegir", on_click=add_event),
                back_button
            ],
            spacing=10,
        )
        view_events_tab = ft.Container(
            content=ft.Column(
                controls=[notices_list, back_button],
                spacing=10,
            ),
        )
        if current_session["account"][0]["user-license"] != "tutor":
            tabs = ft.Tabs(
                selected_index=0,
                tabs=[
                    # ft.Tab(text="Afegir esdeveniment",
                    #        content=add_event_tab),
                    ft.Tab(text="Avisos existents",
                           content=view_events_tab),
                ],
                tab_alignment=ft.TabAlignment.CENTER
            )
        else:
            tabs = ft.Tabs(
                selected_index=0,
                tabs=[
                    ft.Tab(text="Afegir avís",
                           content=add_event_tab),
                    ft.Tab(text="Avisos existents",
                           content=view_events_tab),
                ],
                tab_alignment=ft.TabAlignment.CENTER
            )
        stack.controls.append(ft.Container(content=ft.Column(controls=[ft.Container(height=30), tabs], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                             alignment=ft.MainAxisAlignment.CENTER), alignment=ft.alignment.center))
        page.update()

    def documents_page(e=None):  # Por cambiar # Circulares
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        current_user()
        content = ft.Column(scroll="auto", height=350,
                            width=page.width, expand=True, horizontal_alignment=ft.CrossAxisAlignment.START)

        def load_pdf(e):
            file_picker = ft.FilePicker(
                on_result=cargar_archivos_pdf)
            page.overlay.append(file_picker)
            page.add(file_picker)
            file_picker.pick_files(allow_multiple=True)

        def cargar_archivos_pdf(e):
            """Sube múltiples archivos PDF desde el dispositivo"""
            if e.files:
                subir_y_compartir_archivos(
                    e.files,  # Lista de archivos seleccionados
                    ["taborinfo@tabor.cat"],  # Emails propietarios
                )
        # Subir el PDF al servidor

        def compartir_archivo_con_enlace(file_id, emails_propietarios):
            """Hacer el archivo accesible con el enlace y compartirlo con propietarios"""
            permiso = {
                'type': 'anyone',  # Cualquier persona
                'role': 'reader'   # Solo lectura
            }

            # Crear el permiso de acceso público con enlace
            drive_service.permissions().create(
                fileId=file_id,
                body=permiso
            ).execute()

            # Ahora compartimos el archivo con los propietarios específicos por su email
            for email in emails_propietarios:
                permiso_propietario = {
                    'type': 'user',  # Tipo de permiso para un usuario específico
                    'role': 'reader',  # Rol de propietario
                    'emailAddress': email,
                    # 'transferOwnership': True  # Habilita la transferencia de propiedad
                }

                try:
                    drive_service.permissions().create(
                        fileId=file_id,
                        body=permiso_propietario
                    ).execute()
                    print(f"Archivo compartido con el propietario: {email}")
                except HttpError as error:
                    print(f"No se pudo compartir con {email}: {error}")

            print("Archivo ahora es accesible con el enlace y con los propietarios.")

        # Función para subir un archivo PDF y compartirlo

        def subir_y_compartir_archivos(files, emails_propietarios):
            """Sube múltiples archivos PDF a una carpeta de Google Drive, los comparte y transfiere propiedad"""
            for i in classes:
                if i["class_id"] == current_session["account"][0]["class_id"]:
                    folder_id = i["mailshot_folder_id"]
            file_ids = []  # Lista para almacenar los IDs de los archivos subidos

            for file in files:
                file_path = file.path
                file_name = file.name

                # Metadatos del archivo, incluyendo la carpeta destino
                file_metadata = {
                    'name': file_name,
                    'parents': [folder_id]  # ID de la carpeta de destino
                }

                # Subir el archivo a Google Drive
                media = MediaFileUpload(file_path, mimetype="application/pdf")

                archivo_subido = drive_service.files().create(
                    body=file_metadata,
                    media_body=media
                ).execute()

                # Obtener el ID del archivo subido
                file_id = archivo_subido['id']
                file_ids.append(file_id)
                print(
                    f"Archivo '{file_name}' subido con ID: {file_id} en la carpeta {folder_id}")
                # pdf_name = pdf_info["pdf_name"]
                # print(pdf_name)
                for i in classes:
                    if i["class_id"] == current_session["account"][0]["class_id"]:
                        i["mailshot"].append(
                            {'file_id': file_id, 'file_name': file_name})
                        # for j in alumns:
                        #     full_name = f"{j['name']} {j['first-surname']} {j['second-surname']}"
                        #     pdf_alumn_name = []
                        #     remove_term = re.sub("first_term_", "", file.name)
                        #     pdf_alumn_name.append(remove_term)
                        #     if FindMatches([full_name, pdf_alumn_name[0]]):
                        #         j["report-first-term"].append(
                        #             {'file_id': file_id, 'file_name': file_name})

                # Hacerlo accesible con el enlace y compartirlo con propietarios
                compartir_archivo_con_enlace(file_id, emails_propietarios)

                # Transferir la propiedad del archivo
            escribir_csv(parents, PARENTS_FILE_ID, "Parents.csv")
            escribir_csv(classes, CLASSES_FILE_ID, "Classes.csv")
            escribir_csv(alumns, ALUMNS_FILE_ID, "Alumns.csv")
            escribir_csv(tutors, TUTORS_FILE_ID, "Tutors.csv")
            escribir_csv(alumns_to_parents, ALUMNS_TO_PARENTS_FILE_ID,
                         "Alumns_to_Parents.csv")
            return file_ids  # Devuelve la lista de IDs de los archivos subidos

        def redirect_to_pdf_images(pdf_id):

            pdf_url = f"https://drive.google.com/file/d/{pdf_id}/view"
            page.launch_url(pdf_url)  # Abrir la URL en una nueva ventana

        def load_existing_pdfs():
            if current_session["account"][0]["user-license"] == "parent":
                for j in classes:
                    if j["class_id"] == current_session["sub-account-active"][0]["class_id"]:
                        pdf_files = j["mailshot"]
            elif current_session["account"][0]["user-license"] == "tutor":
                for i in classes:
                    if i["class_id"] == current_session["account"][0]["class_id"]:
                        pdf_files = i["mailshot"]
            # if current_session["account"][0]["user-license"] == "parent":
            #     pdf_files = [current_session["sub-account-active"]
            #                  [0]["report-first-term"][0]]
            # elif current_session["account"][0]["user-license"] == "tutor":
            #     for i in classes:
            #         print(i)
            #         if i["class_id"] == current_session["account"][0]["class_id"]:
            #             print(i["reports"]["first-term"]["reports"])
            #             pdf_files = i["reports"]["first-term"]["reports"]
            for pdf_file in pdf_files:
                pdf_name = []
                # remove_term = re.sub("first_term_", "", pdf_file["file_name"])
                # pdf_alumn_name.append(remove_term)
                remove_extension = re.sub(".pdf", "", pdf_file["file_name"])
                # pdf_name.clear()
                pdf_name.append(remove_extension)
                pdf_id = pdf_file["file_id"]
                content.controls.append(
                    ft.ElevatedButton(
                        text=f"{pdf_name[0]}",
                        on_click=lambda e, pdf_name=pdf_id: redirect_to_pdf_images(
                            pdf_name),
                        width=page.width,
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE_100, color="black", shape=ft.RoundedRectangleBorder(radius=10)
                        )
                    )
                )

            page.update()
        # # Cargar PDFs existentes al inicio
        load_existing_pdfs()
        # # Botón para cargar un nuevo PDF
        load_button = ft.ElevatedButton(
            "Cargar PDF",
            on_click=load_pdf,
            style=ft.ButtonStyle(
                bgcolor="orange", color="black"
            )
        )
        # Configuración visual según el tipo de usuario
        main_container = ft.Column(
            controls=[
                ft.Text("Gestió de circulars",
                        size=24, weight="bold", color="darkblue"),
                ft.Divider(height=2, color="lightgrey"),
                content,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
            spacing=20
        )
        footer_buttons = ft.Row(
            controls=[
                load_button,
                ft.ElevatedButton(
                    "Torna a l'inici", bgcolor=ft.Colors.INDIGO_500, color=ft.Colors.WHITE, on_click=home_page)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        if current_session["account"][0]["user-license"] == "parent":
            stack.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[ft.Container(height=50), main_container, ft.ElevatedButton(
                            "Torna a l'inici", bgcolor=ft.Colors.INDIGO_500, color=ft.Colors.WHITE, on_click=home_page)],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=30
                    ),
                    padding=20
                )
            )
        elif current_session["account"][0]["user-license"] == "tutor":
            stack.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[ft.Container(
                            height=50), main_container, footer_buttons],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=30
                    ),
                    padding=20
                )
            )
        page.update()

    def school_page(e=None):  # Por cambiar # Pagaments
        stack.controls.clear()
        background_image()
        # background_opacity()
        create_app_bar()
        current_user()
        card_number = ft.TextField(
            label="Número de tarjeta", width=300)
        expiration_date = ft.TextField(
            label="Fecha de expiración (MM/AA)", width=300)
        cvv = ft.TextField(label="CVV", width=300, password=True)
        amount = ft.TextField(label="Monto (€)", width=300)
        result_message = ft.Text(value="", color=ft.colors.GREEN, size=16)
        # Lógica de envío de pago

        def send_payment(e):
            # Simular una solicitud de pago sin conexión real
            card_data = {
                "card_number": card_number.value,
                "expiration_date": expiration_date.value,
                "cvv": cvv.value,
                "amount": amount.value,
            }
            # Simulación de la respuesta de la API (mismo comportamiento sin realizar transacciones reales)
            try:
                # Simulación de respuesta aleatoria para el éxito o el fallo del pago
                success = random.choice([True, False])
                if success:
                    result_message.value = "Pago simulado realizado con éxito."
                    result_message.color = ft.colors.GREEN
                else:
                    result_message.value = "Error en el pago: Datos inválidos."
                    result_message.color = ft.colors.RED
            except Exception as ex:
                result_message.value = f"Error al conectar con el servidor: {str(ex)}"
                result_message.color = ft.colors.RED
            page.update()
        # Botón para realizar el pago
        pay_button = ft.ElevatedButton(
            text="Realizar Pago", on_click=send_payment)
        # Añadir componentes a la página
        stack.controls.append(ft.Container(content=ft.Column(controls=[
            card_number,
            expiration_date,
            cvv,
            amount,
            ft.Row(controls=[pay_button,
                                           ft.ElevatedButton(
                                               "Torna a l'inici", bgcolor=ft.Colors.INDIGO_500, color=ft.Colors.WHITE, on_click=home_page),], spacing=50, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),

            result_message,
        ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        ), alignment=ft.alignment.center,))
        page.update()
    login_page()

if __name__ == "__main__":
    # Iniciar el backend en un hilo separado
    # threading.Thread(target=start_fastapi_server, daemon=True).start()
    ft.app(target=main, assets_dir="assets")
    # Iniciar el frontend
