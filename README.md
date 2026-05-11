# 🎓 UniSena - Gestión de Uniformes

UniSena es una plataforma web desarrollada en Django diseñada para facilitar la compra y venta de uniformes. El sistema permite a los vendedores gestionar sus locales e inventarios, y a los clientes explorar catálogos, gestionar carritos de compras y realizar pedidos con seguimiento de abonos.

## 🚀 Características Principales

- **Gestión de Usuarios Multi-rol**: Administradores, Vendedores y Clientes.
- **Autenticación Social**: Integración con Google (Django Allauth).
- **Gestión de Locales**: Los vendedores pueden registrar hasta 3 locales con horarios y estados de actividad.
- **Catálogo de Productos**: Filtros avanzados por talla, tipo de prenda, material y rango de precios.
- **Módulo de Inventario**: Registro automático de movimientos (entradas y salidas) y carga masiva de productos mediante archivos Excel/CSV.
- **Sistema de Pedidos**: Gestión de carrito, procesamiento de pagos con abonos parciales y seguimiento de pedidos.
- **Notificaciones**: Envío de correos electrónicos transaccionales (bienvenida, recuperación de contraseña, alertas de seguridad).

## 🛠️ Tecnologías Utilizadas

- **Backend**: [Django 5.1.6](https://www.djangoproject.com/)
- **Base de Datos**: MySQL
- **Frontend**: HTML5, Tailwind CSS (JavaScript para modales e interactividad)
- **Librerías clave**: 
    - `django-allauth` (Google Login)
    - `pandas` & `openpyxl` (Procesamiento de archivos)
    - `python-dotenv` (Variables de entorno)
    - `mysqlclient` (Conector BD)

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:
- Python 3.10 o superior
- MySQL Server
- Un entorno virtual (recomendado)

## ⚙️ Instalación y Configuración

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/phlpwht/Unisena-Python.git
   cd Unisena
   ```

2. **Crear y activar el entorno virtual:**
   ```bash
   python -m venv venv 
   # En Windows:
   .\venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   Copia el archivo `.env.example` a uno nuevo llamado `.env` y completa tus credenciales:
   ```bash
   copy .env.example .env
   ```
   *Es obligatorio configurar DB_NAME, DB_USER, DB_PASSWORD y la SECRET_KEY para que la app inicie.*

5. **Migraciones de Base de Datos:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Crear un superusuario:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Ejecutar el servidor de desarrollo:**
   ```bash
   python manage.py runserver
   ```

## 📦 Estructura del Proyecto

- `usuario/`: Manejo de perfiles, roles, señales y autenticación.
- `locales/`: Gestión de tiendas y vistas para vendedores.
- `uniformes/`: Catálogo, carrito y lógica de procesamiento de pedidos.
- `inventario/`: Registro de movimientos de stock.
- `config/`: Configuraciones principales del proyecto (settings, urls, wsgi).

## 📧 Contacto
Si tienes dudas o sugerencias sobre el proyecto, puedes contactar al administrador en: `unisena.app@gmail.com`.

---
*Desarrollado para la gestión eficiente de uniformes escolares y corporativos - 2024.*
