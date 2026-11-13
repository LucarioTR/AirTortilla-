from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = (
    'clave_secreta_airtortilla_muy_segura'  # Cambiar en producción
)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'sqlite:///airtortilla.db'  # Base de datos relacional
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# ==========================================
# MODELOS DE LA BASE DE DATOS RELACIONAL
# ==========================================


class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(150), unique=True, nullable=False)
  password = db.Column(db.String(255), nullable=False)
  role = db.Column(
      db.String(50), nullable=False, default='empleado'
  )  # 'admin' o 'empleado'


class AuditLog(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  action = db.Column(db.String(255), nullable=False)
  timestamp = db.Column(db.DateTime, default=datetime.utcnow)

  # Relación con el usuario para mantener la trazabilidad
  user = db.relationship(
      'User', backref=db.backref('audit_logs', lazy=True)
  )


@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))


# ==========================================
# RUTAS Y CONTROLADORES
# ==========================================


@app.route('/')
@login_required
def index():
  return render_template('index.html')


# US 1: Como Empleado Quiero Poder hacer log in
@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
      login_user(user)

      # Registro de trazabilidad para el login
      log = AuditLog(
          user_id=user.id, action=f'El usuario {username} inició sesión.'
      )
      db.session.add(log)
      db.session.commit()

      flash('¡Bienvenido al sistema de AirTortilla!', 'success')
      return redirect(url_for('index'))
    else:
      flash('Credenciales inválidas. Por favor, inténtalo de nuevo.', 'danger')

  return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
  log = AuditLog(
      user_id=current_user.id,
      action=f'El usuario {current_user.username} cerró sesión.',
  )
  db.session.add(log)
  db.session.commit()

  logout_user()
  flash('Has cerrado sesión correctamente.', 'info')
  return redirect(url_for('login'))


# US 2: Como Administrador de Sistemas quiero dar de alta usuarios
@app.route('/admin/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
  if current_user.role != 'admin':
    flash('Acceso denegado. Se requieren permisos de Administrador.', 'danger')
    return redirect(url_for('index'))

  if request.method == 'POST':
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'empleado')

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
      flash('El nombre de usuario ya existe.', 'warning')
      return redirect(url_for('create_user'))

    hashed_password = generate_password_hash(password, method='scrypt')
    new_user = User(username=username, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()

    # US 3: Trazabilidad de modificaciones (alta de usuario)
    log = AuditLog(
        user_id=current_user.id,
        action=(
            f'El administrador {current_user.username} dio de alta al usuario'
            f' "{username}" con rol "{role}".'
        ),
    )
    db.session.add(log)
    db.session.commit()

    flash(f'Usuario {username} creado con éxito.', 'success')
    return redirect(url_for('index'))

  return render_template('create_user.html')


# US 3: Como Administrador Quiero mantener la trazabilidad de las modificaciones
@app.route('/admin/audit_logs')
@login_required
def view_audit_logs():
  if current_user.role != 'admin':
    flash('Acceso denegado. Se requieren permisos de Administrador.', 'danger')
    return redirect(url_for('index'))

  logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
  return render_template('audit_logs.html', logs=logs)


# Inicialización de la BD y creación de un admin por defecto
if __name__ == '__main__':
  with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
      admin_user = User(
          username='admin',
          password=generate_password_hash('admin123', method='scrypt'),
          role='admin',
      )
      db.session.add(admin_user)
      db.session.commit()
      print(
          'Usuario Administrador por defecto creado: admin / contraseña: admin123'
      )
  app.run(debug=True)