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
app.config['SECRET_KEY'] = 'clave_secreta_airtortilla_muy_segura'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///airtortilla.db'

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


class Flight(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  flight_number = db.Column(db.String(50), unique=True, nullable=False)
  origin = db.Column(db.String(100), nullable=False)
  destination = db.Column(db.String(100), nullable=False)
  departure_time = db.Column(db.DateTime, nullable=False)
  seats_available = db.Column(db.Integer, nullable=False)


class Reservation(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  flight_id = db.Column(db.Integer, db.ForeignKey('flight.id'), nullable=False)
  booking_date = db.Column(db.DateTime, default=datetime.utcnow)

  # Relaciones
  user = db.relationship('User', backref=db.backref('reservations', lazy=True))
  flight = db.relationship(
      'Flight', backref=db.backref('reservations', lazy=True)
  )


class AuditLog(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  action = db.Column(db.String(255), nullable=False)
  timestamp = db.Column(db.DateTime, default=datetime.utcnow)
  user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))


@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))


# ==========================================
# RUTAS Y CONTROLADORES
# ==========================================


@app.route('/')
@login_required
def index():
  flights = Flight.query.all()
  user_reservations = Reservation.query.filter_by(user_id=current_user.id).all()
  return render_template(
      'index.html', flights=flights, user_reservations=user_reservations
  )


@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
      login_user(user)
      log = AuditLog(
          user_id=user.id, action=f'El usuario {username} inició sesión.'
      )
      db.session.add(log)
      db.session.commit()
      flash('¡Bienvenido al sistema de AirTortilla!', 'success')
      return redirect(url_for('index'))
    else:
      flash('Credenciales inválidas.', 'danger')

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


# --- GESTIÓN DE VUELOS Y RESERVAS ---


@app.route('/book/<int:flight_id>', methods=['POST'])
@login_required
def book_flight(flight_id):
  flight = Flight.query.get_or_404(flight_id)

  if flight.seats_available > 0:
    flight.seats_available -= 1
    reservation = Reservation(user_id=current_user.id, flight_id=flight.id)
    db.session.add(reservation)

    # Trazabilidad de la reserva
    log = AuditLog(
        user_id=current_user.id,
        action=(
            f'El usuario {current_user.username} reservó el vuelo'
            f' {flight.flight_number} ({flight.origin} ->'
            f' {flight.destination}).'
        ),
    )
    db.session.add(log)
    db.session.commit()

    flash(f'¡Vuelo {flight.flight_number} reservado con éxito!', 'success')
  else:
    flash('Lo sentimos, no quedan asientos disponibles en este vuelo.', 'danger')

  return redirect(url_for('index'))


# --- PANEL DE ADMINISTRACIÓN ---


@app.route('/admin/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
  if current_user.role != 'admin':
    flash('Acceso denegado.', 'danger')
    return redirect(url_for('index'))

  if request.method == 'POST':
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'empleado')

    if User.query.filter_by(username=username).first():
      flash('El nombre de usuario ya existe.', 'warning')
      return redirect(url_for('create_user'))

    hashed_password = generate_password_hash(password, method='scrypt')
    new_user = User(username=username, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()

    log = AuditLog(
        user_id=current_user.id,
        action=(
            f'El administrador {current_user.username} creó al usuario'
            f' "{username}" con rol "{role}".'
        ),
    )
    db.session.add(log)
    db.session.commit()

    flash(f'Usuario {username} creado con éxito.', 'success')
    return redirect(url_for('index'))

  return render_template('create_user.html')


@app.route('/admin/create_flight', methods=['GET', 'POST'])
@login_required
def create_flight():
  if current_user.role != 'admin':
    flash('Acceso denegado.', 'danger')
    return redirect(url_for('index'))

  if request.method == 'POST':
    flight_number = request.form.get('flight_number')
    origin = request.form.get('origin')
    destination = request.form.get('destination')
    departure_str = request.form.get('departure_time')
    seats = int(request.form.get('seats_available'))

    departure_time = datetime.strptime(departure_str, '%Y-%m-%dT%H:%M')

    new_flight = Flight(
        flight_number=flight_number,
        origin=origin,
        destination=destination,
        departure_time=departure_time,
        seats_available=seats,
    )
    db.session.add(new_flight)
    db.session.commit()

    log = AuditLog(
        user_id=current_user.id,
        action=(
            f'El administrador {current_user.username} creó el vuelo'
            f' {flight_number} ({origin} a {destination}).'
        ),
    )
    db.session.add(log)
    db.session.commit()

    flash(f'Vuelo {flight_number} creado correctamente.', 'success')
    return redirect(url_for('index'))

  return render_template('create_flight.html')


@app.route('/admin/audit_logs')
@login_required
def view_audit_logs():
  if current_user.role != 'admin':
    flash('Acceso denegado.', 'danger')
    return redirect(url_for('index'))

  logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
  return render_template('audit_logs.html', logs=logs)


# Inicialización de la BD con datos de prueba
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

    # Añadir un vuelo de prueba si la tabla está vacía
    if not Flight.query.first():
      sample_flight = Flight(
          flight_number='AT-101',
          origin='Madrid',
          destination='Barcelona',
          departure_time=datetime(2026, 6, 15, 10, 30),
          seats_available=50,
      )
      db.session.add(sample_flight)
      db.session.commit()

  app.run(debug=True)