# 🎓 UniSena - Plataforma de Gestión de Uniformes

[!Python](https://www.python.org/)
[!Django](https://www.djangoproject.com/)
[!Tailwind CSS](https://tailwindcss.com/)
[!MySQL](https://www.mysql.com/)

UniSena es una solución web integral diseñada para la comunidad institucional, facilitando la comercialización y gestión de uniformes. La plataforma conecta a vendedores locales con clientes (estudiantes/administrativos), ofreciendo un entorno seguro, eficiente y moderno para la gestión de inventarios y pedidos.

---

## 🌟 Características Principales

### 👥 Gestión Multi-rol
*   **Administradores:** Supervisión global, gestión de usuarios, locales y moderación proactiva de comentarios con filtros de lenguaje.
*   **Vendedores:** Control de hasta 3 locales, gestión de stock, reportes de ventas y carga masiva de productos.
*   **Clientes:** Exploración de catálogos con filtros avanzados, sistema de carrito y seguimiento de pedidos con abonos.

### 🚀 Funcionalidades Clave
*   **🔐 Autenticación Segura:** Login tradicional y social (Google) integrado.
*   **🌓 Modo Oscuro:** Interfaz adaptable para una mejor experiencia visual en cualquier entorno.
*   **📦 Inventario Inteligente:** Registro automático de movimientos (entradas/salidas) y soporte para archivos Excel/CSV.
*   **💳 Sistema de Pagos y Abonos:** Los clientes pueden realizar pagos parciales y los vendedores gestionar saldos pendientes.
*   **💬 Moderación de Comunidad:** Sistema de calificaciones con detección automática de términos inapropiados.
*   **📧 Notificaciones:** Correos transaccionales para bienvenida, recuperación de cuenta y alertas de seguridad.
*   **📱 Comunicación Directa:** Integración con WhatsApp para contactar a los vendedores desde el resumen del pedido.

---

## 🛠️ Stack Tecnológico

| Área | Tecnología |
| :--- | :--- |
| **Backend** | Python / Django 5.1.6 |
| **Base de Datos** | MySQL |
| **Frontend** | HTML5 / Tailwind CSS / JavaScript (Vanilla) |
| **Librerías** | Pandas, Openpyxl, Django Allauth, Dotenv |

---

## � Requisitos Previos

*   Python 3.10 o superior.
*   Servidor MySQL.
*   Navegador web moderno.

---

## ⚙️ Instalación y Configuración

### 1. Preparar el Entorno
```bash
# Clonar el repositorio
git clone https://github.com/phlpwht/Unisena-Python.git
cd Unisena

# Crear y activar entorno virtual
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto basándote en `.env.example`:
```env
DEBUG=True
SECRET_KEY=tu_clave_secreta

# Configuración de Base de Datos
DB_NAME=unisena
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
DB_HOST=127.0.0.1
DB_PORT=3306

# Google Auth & Dominio
GOOGLE_CLIENT_ID=tu_id_de_google
GOOGLE_SECRET_KEY=tu_secret_de_google
SITE_DOMAIN=127.0.0.1:8000
```

### 4. Desplegar Base de Datos
```bash
# Ejecutar migraciones (puebla roles y estados automáticamente)
python manage.py migrate

# Crear cuenta de administrador
python manage.py createsuperuser
```

### 5. Iniciar Aplicación
```bash
python manage.py runserver
```

---

## 📂 Estructura del Proyecto

*   `usuario/`: Gestión de perfiles, roles, lógica de bloqueos y autenticación.
*   `locales/`: Módulo de gestión de tiendas y dashboard para vendedores.
*   `uniformes/`: Catálogo público, gestión de carrito y procesamiento de pedidos.
*   `inventario/`: Registro de movimientos de stock y utilidades de carga masiva.
*   `administradores/`: Panel de control administrativo y herramientas de moderación.
*   `config/`: Ajustes centrales del proyecto, URLs y configuración de WSGI/ASGI.

---

## 📧 Contacto & Soporte

Si tienes dudas o sugerencias sobre **UniSena**, puedes contactar al equipo de desarrollo:
📩 **Email:** unisena.app@gmail.com

---
*© 2024 UniSena - Gestión eficiente de uniformes institucionales.*
