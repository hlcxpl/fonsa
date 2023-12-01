from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from contextlib import contextmanager

app = Flask(__name__)
app.secret_key = "123456"


def get_db_connection():
    return mysql.connector.connect(
        host="localhost", user="root", password="losd3108", database="hospital"
    )


# Fuera de la función para crear las tablas
with get_db_connection() as conn:
    with conn.cursor() as cursor:
        # Creación de tablas
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Hospital (
                id INT PRIMARY KEY DEFAULT 0,
                nombre VARCHAR(80) NOT NULL,
                ubicacion VARCHAR(100) NOT NULL
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Paciente (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(80) NOT NULL,
                age INT NOT NULL,
                history_number VARCHAR(20) NOT NULL UNIQUE,
                priority FLOAT DEFAULT 0,
                risk FLOAT DEFAULT 0,
                category VARCHAR(255) DEFAULT NULL,
                hospital_id INT,
                FOREIGN KEY (hospital_id) REFERENCES Hospital(id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS PacienteNiño (
                id INT AUTO_INCREMENT PRIMARY KEY,
                relacion_peso_estatura FLOAT NOT NULL DEFAULT 0,
                paciente_id INT,
                FOREIGN KEY (paciente_id) REFERENCES Paciente(id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS PacienteJoven (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fumador BOOLEAN,
                years_smoking INT,
                paciente_id INT,
                FOREIGN KEY (paciente_id) REFERENCES Paciente(id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS PacienteAnciano (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tiene_dieta BOOLEAN,
                paciente_id INT,
                FOREIGN KEY (paciente_id) REFERENCES Paciente(id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Consulta (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cant_pacientes INT DEFAULT 0,
                nombre_especialista VARCHAR(80),
                tipo_consulta VARCHAR(20),
                estado BOOLEAN NOT NULL DEFAULT 0,
                hospital_id INT,
                FOREIGN KEY (hospital_id) REFERENCES Hospital(id)
            )
        """
        )

    # Commit fuera del bloque with
    conn.commit()


# Ruta para el formulario
@app.route("/")
def index():
    return render_template("index.html")


@contextmanager
def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost", user="root", password="losd3108", database="hospital"
    )
    try:
        yield connection
    finally:
        connection.close()


def determinar_categoria(edad):
    if 1 <= edad <= 15:
        return "niño"
    elif 16 <= edad <= 40:
        return "joven"
    else:
        return "anciano"


def calculate_priority_and_risk(edad, weight_height, smoker, years_smoking, has_diet):
    categoria = determinar_categoria(edad)

    if categoria == "niño":
        return calculate_priority_and_risk_for_children(edad, weight_height)
    elif categoria == "joven":
        return calculate_priority_and_risk_for_young(edad, smoker, years_smoking)
    elif categoria == "anciano":
        return calculate_priority_and_risk_for_elderly(edad, has_diet)
    else:
        return 0, 0  # Manejar otros casos si es necesario


def calculate_priority_and_risk_for_children(age, weight_height):
    if 1 <= age <= 5:
        priority_child = weight_height + 3
    elif 6 <= age <= 12:
        priority_child = weight_height + 2
    elif 13 <= age <= 15:
        priority_child = weight_height + 1
    else:
        priority_child = 0  # Prioridad predeterminada para otras edades

    risk_child = (age * priority_child) / 100

    return priority_child, risk_child


def calculate_priority_and_risk_for_young(age, smoker, years_smoking):
    if smoker == 1:
        priority_young = years_smoking / 4 + 2
    else:
        priority_young = 2  # Prioridad predeterminada para no fumadores

    risk_young = (age * priority_young) / 100

    return priority_young, risk_young


def calculate_priority_and_risk_for_elderly(age, has_diet):
    if 60 <= age <= 100:
        if has_diet == 1:
            priority_elderly = age / 20 + 4
        else:
            priority_elderly = age / 30 + 3
    else:
        priority_elderly = 0  # Prioridad predeterminada para otras edades

    risk_elderly = (age * priority_elderly) / 100

    return priority_elderly, risk_elderly


# def alterar_tabla_paciente():
#     with get_db_connection() as conn:
#         with conn.cursor() as cursor:
#             # Verificar si las columnas ya existen en la tabla
#             cursor.execute("SHOW COLUMNS FROM Paciente LIKE 'risk'")
#             risk_column = cursor.fetchone()

#             cursor.execute("SHOW COLUMNS FROM Paciente LIKE 'priority'")
#             priority_column = cursor.fetchone()

#             cursor.execute("SHOW COLUMNS FROM Paciente LIKE 'category'")
#             category_column = cursor.fetchone()

#             if not risk_column:
#                 # La columna risk no existe, la agregamos
#                 cursor.execute("ALTER TABLE Paciente ADD COLUMN risk FLOAT DEFAULT 0")

#             if not priority_column:
#                 # La columna priority no existe, la agregamos
#                 cursor.execute(
#                     "ALTER TABLE Paciente ADD COLUMN priority FLOAT DEFAULT 0"
#                 )

#             if not category_column:
#                 # La columna category no existe, la agregamos
#                 cursor.execute(
#                     "ALTER TABLE Paciente ADD COLUMN category VARCHAR(255) DEFAULT NULL"
#                 )

#             conn.commit()


@app.route("/register", methods=["POST"])
def register_patient():
    try:
        # Obtener datos del formulario
        name = request.form["name"]
        age = int(request.form["age"])
        history_number = request.form["history_number"]
        smoker = 1 if request.form["smoker"] == "yes" else 0
        years_smoking_str = request.form.get("years_smoking", "")
        years_smoking = int(years_smoking_str) if years_smoking_str.strip() else 0
        has_diet = 1 if request.form["has_diet"] == "yes" else 0
        weight_height_str = request.form["weight_height"]
        # Verificar si weight_height_str está vacío
        if not weight_height_str.strip():
            # Si está vacío, asignar 0 a weight_height
            weight_height = 0.0
        else:
            # Extracción de valores numéricos desde el formato '50/1.5'
            weight, height = map(float, weight_height_str.split("/"))
            # Realizar la operación weight/height y redondear a 2 decimales
            weight_height = round(weight / height, 2)
        # Determinar la categoría
        categoria = determinar_categoria(age)
        # Calculamos prioridades y riesgos utilizando la nueva función
        priority, risk = calculate_priority_and_risk(
            age, weight_height, smoker, years_smoking, has_diet
        )
        # Llamar a la función para alterar la tabla Paciente
        # alterar_tabla_paciente()
        # Conexión a la base de datos
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Insertar datos en la tabla Paciente
                cursor.execute(
                    """
                        INSERT INTO Paciente(name, age, history_number, priority, risk, category)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                    (name, age, history_number, priority, risk, categoria),
                )
                conn.commit()

                # Obtener el ID del paciente recién insertado
                paciente_id = cursor.lastrowid

                # Insertar información adicional según la categoría
                if categoria == "niño":
                    cursor.execute(
                        """
                            INSERT INTO PacienteNiño(relacion_peso_estatura, paciente_id)
                            VALUES (%s, %s)
                            """,
                        (weight_height, paciente_id),
                    )
                elif categoria == "joven":
                    cursor.execute(
                        """
                            INSERT INTO PacienteJoven(fumador, years_smoking, paciente_id)
                            VALUES (%s, %s, %s)
                            """,
                        (smoker, years_smoking, paciente_id),
                    )
                elif categoria == "anciano":
                    cursor.execute(
                        """
                            INSERT INTO PacienteAnciano(tiene_dieta, paciente_id)
                            VALUES (%s, %s)
                            """,
                        (has_diet, paciente_id),
                    )

                conn.commit()

                return redirect(url_for("index"))
    except mysql.connector.errors.IntegrityError as e:
        # Manejar la excepción de entrada duplicada
        if e.errno == 1062:
            return "Error: El número de historia clínica ya existe."
        else:
            raise  # Si es una excepción diferente, re-raise la excepción original


@app.route("/registrar_consulta", methods=["GET", "POST"])
def registrar_consulta():
    if request.method == "POST":
        # Obtener los datos del formulario
        nombre_especialista = request.form.get("nombre_especialista")
        tipo_consulta = request.form.get("tipo_consulta")
        cant_pacientes = 0
        # Conexión a la base de datos
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Insertar datos en la tabla Consulta
                cursor.execute(
                    """
                    INSERT INTO Consulta (nombre_especialista, tipo_consulta, cant_pacientes)
                    VALUES (%s, %s, %s)
                    """,
                    (nombre_especialista, tipo_consulta, cant_pacientes),
                )
                # Commit dentro del bloque with
                conn.commit()

    return render_template("registrar_consulta.html")


def obtener_datos_paciente(cursor, paciente_id):
    # Realizar la consulta SQL para obtener los datos del paciente
    cursor.execute(
        """
        SELECT 
            P.id, 
            P.age, 
            P.priority, 
            PN.relacion_peso_estatura AS weight_height, 
            PJ.fumador AS smoker, 
            PJ.years_smoking, 
            PA.tiene_dieta AS has_diet,
            P.category
        FROM Paciente P
        LEFT JOIN PacienteNiño PN ON P.id = PN.paciente_id
        LEFT JOIN PacienteJoven PJ ON P.id = PJ.paciente_id
        LEFT JOIN PacienteAnciano PA ON P.id = PA.paciente_id
        WHERE P.id = %s
        """,
        (paciente_id,),
    )
    paciente_data = cursor.fetchone()

    return paciente_data


def determinar_tipo_consulta(prioridad, categoria):
    if prioridad is not None:
        if prioridad > 4:
            return "Urgencias"
        elif categoria == "Niño" and prioridad <= 4:
            return "Pediatría"
        elif categoria == "Joven" and prioridad <= 4:
            return "CGI"
        elif categoria == "Anciano" and prioridad <= 4:
            return "CGI"
    return None


@app.route("/consultas")
def mostrar_consultas():
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM Consulta")
            consultas = cursor.fetchall()
    return render_template("consultas.html", consultas=consultas)


# Ruta para listar pacientes con mayor riesgo
@app.route("/consultar_historia", methods=["GET", "POST"])
def consultar_historiaform():
    if request.method == "POST":
        # Obtener el número de historia clínica del formulario
        history_number = request.form["history_number"]

        # Redirigir a la ruta que mostrará la lista de pacientes con mayor riesgo
        return redirect(
            url_for("listar_pacientes_mayor_riesgo", history_number=history_number)
        )

    # Renderizar la plantilla del formulario
    return render_template("consultar_historia.html")


# La función para listar pacientes con mayor riesgo
@app.route("/lista_mayor_riesgo/<int:history_number>")
def listar_pacientes_mayor_riesgo(history_number):
    try:
        print(f"History Number: {history_number}")

        # Obtener el riesgo del paciente dado su número de historia clínica
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT risk
                    FROM Paciente
                    WHERE history_number = %s
                    """,
                    (history_number,),
                )
                paciente_risk = cursor.fetchone()

                if not paciente_risk:
                    return "Error: No se encontró un paciente con el número de historia clínica proporcionado."

                # Obtener el riesgo del paciente actual
                riesgo_paciente = paciente_risk[0]

                # Consultar pacientes con mayor riesgo
                cursor.execute(
                    """
                    SELECT name, age, history_number, risk
                    FROM Paciente
                    WHERE risk > %s
                    ORDER BY risk DESC
                    """,
                    (riesgo_paciente,),
                )
                pacientes_mayor_riesgo = cursor.fetchall()

                # Definir los nombres de las columnas
                headers = ["Nombre", "Edad", "Número de Historia", "Riesgo"]
        # Renderizar la plantilla con la lista de pacientes de mayor riesgo
        return render_template(
            "lista_mayor_riesgo.html", headers=headers, pacientes=pacientes_mayor_riesgo
        )

    except Exception as e:
        return f"Error: {e}"


@app.route("/sala_espera")
def mostrar_pacientes():
    alterar_tabla_paciente()
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SHOW COLUMNS FROM Paciente")
            columnas = [columna["Field"] for columna in cursor.fetchall()]

            # Modificamos la consulta para incluir la condición en_sala_espera = 1
            cursor.execute(
                "SELECT * FROM Paciente WHERE en_sala_espera = 1 ORDER BY priority DESC"
            )
            pacientes = cursor.fetchall()

            # Asegurarnos de que los valores None se manejen adecuadamente
            for paciente in pacientes:
                for key, value in paciente.items():
                    if value is None:
                        paciente[key] = "N/A"  # o cualquier valor por defecto que desees

    return render_template("sala_espera.html", pacientes=pacientes, columnas=columnas)




def alterar_tabla_paciente():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Verificar si la columna en_sala_espera ya existe en la tabla
            cursor.execute("SHOW COLUMNS FROM Paciente LIKE 'en_sala_espera'")
            en_sala_espera_column = cursor.fetchone()

            if not en_sala_espera_column:
                # La columna en_sala_espera no existe, la agregamos
                cursor.execute(
                    "ALTER TABLE Paciente ADD COLUMN en_sala_espera BOOLEAN DEFAULT 1"
                )

            conn.commit()


@app.route("/atender_sala_espera", methods=["GET", "POST"])
def atender_sala_espera():
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            try:
                paciente_pendiente = obtener_paciente_pendiente(cursor)

                if not paciente_pendiente:
                    return "No hay pacientes en la sala de espera en este momento."

                if paciente_pendiente:
                    paciente_proceso_asignacion(conn, cursor, paciente_pendiente)

                tipo_consulta = determinar_tipo_consulta(
                    paciente_pendiente["priority"], paciente_pendiente["category"]
                )
                print(f"tipo de consulta: {tipo_consulta}")
                consulta_disponible = obtener_consulta_disponible(cursor, tipo_consulta)
                print(f"consultad dispo = {consulta_disponible}")
                if not consulta_disponible:
                    mover_paciente_a_sala_espera(conn, cursor, paciente_pendiente)
                    return f"No hay consultas de tipo {tipo_consulta} disponibles en este momento."

                if consulta_disponible:
                    ir_a_consulta(conn, cursor, tipo_consulta)
                    return f"Pacientes atendidos en la sala de espera correctamente. Tipo de consulta: {tipo_consulta}"

            except Exception as e:
                # Manejar otras excepciones específicas si es posible
                print(f"Error: {e}")
                conn.rollback()
                return "Ha ocurrido un error interno."


def obtener_consulta_disponible(cursor, tipo_consulta):
    cursor.execute(
        "SELECT estado FROM Consulta WHERE tipo_consulta = %s", (tipo_consulta,)
    )
    disponibilidad = cursor.fetchone()
    return disponibilidad


def obtener_paciente_pendiente(cursor):
    cursor.execute(
        "SELECT id, priority, category FROM Paciente WHERE en_sala_espera = 1 ORDER BY priority DESC LIMIT 1"
    )
    paciente_pendiente = cursor.fetchone()
    
    # Devolver solo los datos necesarios, no una tupla completa
    return paciente_pendiente if paciente_pendiente else None


def paciente_proceso_asignacion(conn, cursor, tipo_consulta):
    cursor.execute(
        "UPDATE Consulta SET estado = 1 WHERE tipo_consulta = %s",
        (tipo_consulta,),
    )
    conn.commit()


def mover_paciente_a_sala_espera(conn, cursor, paciente_pendiente):
    cursor.execute(
        "UPDATE Paciente SET en_sala_espera = 1 WHERE id = %s",
        (paciente_pendiente["id"],),
    )
    conn.commit()


def ir_a_consulta(conn, cursor, tipo_consulta):
    cursor.execute(
        "UPDATE Consulta SET cant_pacientes = cant_pacientes + 1, estado = 1 WHERE tipo_consulta = %s",
        (tipo_consulta,)
    )
    conn.commit()


if __name__ == "__main__":
    app.run(debug=True)
