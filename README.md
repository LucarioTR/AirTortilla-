# AirTortilla - Sistema de Gestión y Migración a Base de Datos Relacional

Este repositorio contiene la solución desarrollada para la **Entrega 2 de AirTortilla**, cumpliendo con los objetivos de migración tecnológica y las User Stories asignadas[cite: 1].

---

## 🚀 1. Stack Tecnológico

Siguiendo las directrices del proyecto, se ha seleccionado el siguiente stack para la implementación:
* **Backend:** Python con el framework **Flask**.
* **Gestión de Base de Datos (ORM):** **Flask-SQLAlchemy** (con SQLite por defecto para desarrollo local, altamente escalable a PostgreSQL o MySQL).
* **Control de Sesiones y Seguridad:** **Flask-Login** y **Werkzeug Security** (para el cifrado de contraseñas mediante hashes seguros).
* **Frontend:** HTML5 con **Bootstrap 5** para una interfaz web limpia, responsive y funcional.
* **Trazabilidad:** Sistema de registros de auditoría integrado en base de datos relacional.

---

## 👤 2. User Stories Implementadas

La aplicación da soporte a los requerimientos funcionales solicitados:
1. **Login de Empleados:** Los empleados de la compañía pueden acceder de forma segura a los recursos restringidos introduciendo sus credenciales[cite: 1].
2. **Alta de Usuarios (Administrador):** Los administradores de sistemas disponen de un panel exclusivo para dar de alta nuevos usuarios (tanto empleados como administradores), garantizando la seguridad interna[cite: 1].
3. **Trazabilidad de Modificaciones:** El sistema registra automáticamente en una tabla relacional de auditoría (`AuditLog`) las acciones críticas, como inicios de sesión, cierres de sesión y creaciones de usuarios, asegurando las buenas prácticas de seguridad[cite: 1].

---

## 🛠️ 3. Estructura del Proyecto

```text
AirTortilla/
│
├── app.py                  # Archivo principal de la aplicación y modelos de BD
├── README.md               # Documentación del proyecto
└── templates/              # Vistas HTML con Jinja2
    ├── base.html           # Layout global y barra de navegación
    ├── login.html          # Vista de inicio de sesión
    ├── index.html          # Panel principal de bienvenida
    ├── create_user.html    # Formulario de alta de usuarios (Admin)
    └── audit_logs.html     # Tabla de trazabilidad y auditoría (Admin)

 