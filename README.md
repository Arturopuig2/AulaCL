# Aula CL - Plataforma de Comprensión Lectora

Aula CL es una aplicación web educativa diseñada para mejorar la comprensión lectora en estudiantes de Primaria y ESO. La plataforma ofrece una selección de textos literarios multilingües, acompañados de audios y cuestionarios interactivos.

## 🚀 Características Principales

-   **Biblioteca Multilingüe**: Lecturas disponibles en Español, Inglés, Valenciano/Catalán, etc.
-   **Audio Integrado**: Reproductor de audio para acompañar la lectura (Read-along).
-   **Cuestionarios Interactivos**: Tests de comprensión con feedback inmediato.
-   **Gamificación**: Sistema de puntuación y seguimiento de progreso ("Completado").
-   **Predicción de Rendimiento**: Modelo de ML simple que predice futuras puntuaciones basadas en el historial.
-   **Panel de Administración**: Gestión completa de textos (subida de archivos, asignación de cursos/idiomas).
-   **Filtros Avanzados**: Búsqueda por Curso (Primaria/ESO/Bachillerato) e Idioma.
-   **Gestión de Usuarios**: Registro, Login y Recuperación de Contraseña seguro.
-   **Interfaz Moderna**: Diseño limpio y amigable (Glassmorphism) adaptado a estudiantes.

## 🛠 Tecnologías Utilizadas

-   **Backend**: Python (FastAPI), SQLAlchemy (SQLite).
-   **Frontend**: HTML5, CSS3, JavaScript (Vanilla), Jinja2 Templates.
-   **Base de Datos**: SQLite.
-   **Otros**: Axios (peticiones HTTP), scikit-learn (ML).

## 📦 Instalación y Uso

1.  **Clonar el repositorio** (o descargar el código):
    ```bash
    git clone https://github.com/tu-usuario/AulaCL.git
    cd AulaCL
    ```

2.  **Crear un entorno virtual** (recomendado):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # En Mac/Linux
    # venv\Scripts\activate   # En Windows
    ```

3.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Inicializar la Base de Datos**:
    ```bash
    python3 init_db.py
    ```
    *Esto creará la base de datos y añadirá el usuario admin inicial.*

5.  **Ejecutar la aplicación**:
    Puedes usar el script incluido:
    ```bash
    ./run.sh
    ```
    O ejecutar manualmente con Uvicorn:
    ```bash
    uvicorn app.main:app --reload
    ```

6.  **Acceder en el navegador**:
    Visita `http://127.0.0.1:8000`

## 📂 Estructura del Proyecto

-   `app/`: Código fuente del backend (modelos, rutas, lógica).
-   `data/`: Archivos de texto (.txt) organizados por nivel.
-   `static/`: Archivos estáticos (CSS, JS, imágenes, audios).
-   `templates/`: Plantillas HTML (Jinja2).
-   `init_db.py`: Script de inicialización de la BD.

## 👥 Usuarios de Prueba

El script `init_db.py` crea por defecto:
-   **Usuario**: `admin`
-   **Contraseña**: `1234`

---
*Desarrollado para fines educativos.*
