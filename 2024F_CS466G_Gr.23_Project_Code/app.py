import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.orm import joinedload

# Database Configuration
DATABASE_URI = 'sqlite:///hotel_management.db'
engine = create_engine(DATABASE_URI)
Base = declarative_base()
Session = scoped_session(sessionmaker(bind=engine))
session = Session()

# Models
class User(Base, UserMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True)
    full_name = Column(String(100))
    role = Column(String(50), nullable=False)  # 'admin', 'receptionist', 'manager'
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)

class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    phone_number = Column(String(20), unique=True)
    address = Column(String(255))
    identification_number = Column(String(50), unique=True)
    date_of_birth = Column(DateTime)
    nationality = Column(String(50))
    total_stays = Column(Integer, default=0)
    loyalty_points = Column(Integer, default=0)

    # Thêm mối quan hệ với Booking
    bookings = relationship("Booking", back_populates="customer")

class Room(Base):
    __tablename__ = 'rooms'
    
    id = Column(Integer, primary_key=True)
    room_number = Column(String(10), unique=True, nullable=False)
    room_type = Column(String(50))  # Single, Double, Suite, etc.
    price_per_night = Column(Float)
    status = Column(String(20), default='AVAILABLE')  # AVAILABLE, OCCUPIED, MAINTENANCE
    
    # Thêm mối quan hệ với Booking
    bookings = relationship("Booking", back_populates="room")

    @classmethod
    def get_all_rooms(cls):
        return session.query(cls).all()

class Booking(Base):
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    check_in_date = Column(DateTime, nullable=False)
    check_out_date = Column(DateTime, nullable=False)
    status = Column(String(20), default='CONFIRMED')  # Trạng thái booking là CONFIRMED, CANCELLED, COMPLETED
    total_price = Column(Float, nullable=True)

    # Thêm các mối quan hệ
    customer = relationship("Customer", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")


class Report(Base):
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True)
    report_date = Column(DateTime, default=datetime.utcnow)
    total_rooms = Column(Integer)
    total_occupied_rooms = Column(Integer)
    total_active_bookings = Column(Integer)
    total_revenue = Column(Float)

# Thêm bảng report vào cơ sở dữ liệu
Base.metadata.create_all(engine)

# Flask Application Setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Login Manager Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'



@login_manager.user_loader
def load_user(user_id):
    return session.query(User).get(int(user_id))

# Utility function to create initial admin
def create_admin_user():
    existing_admin = session.query(User).filter_by(username='admin').first()
    if not existing_admin:
        # Create admin with a specific password using Werkzeug's secure hashing
        admin_password = 'admin123'
        hashed_password = generate_password_hash(admin_password)
        
        admin_user = User(
            username='admin', 
            password_hash=hashed_password,
            email='admin@hotel.com',
            full_name='Hotel Admin',
            role='admin',
            is_active=True
        )
        
        session.add(admin_user)
        session.commit()
        
        print(f"Admin created. Username: admin, Password: {admin_password}")
        return admin_password
    return None
    
# Gọi hàm tạo admin ngay sau khi cấu hình ứng dụng Flask
create_admin_user()

# Routes
@app.route('/')
@login_required
def dashboard():
    total_rooms = session.query(Room).count()
    occupied_rooms = session.query(Room).filter(Room.status == 'OCCUPIED').count()
    active_bookings = session.query(Booking).filter(Booking.status == 'CONFIRMED').count()
    
    return render_template('dashboard.html', 
                           total_rooms=total_rooms, 
                           occupied_rooms=occupied_rooms,
                           active_bookings=active_bookings)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = session.query(User).filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            user.last_login = datetime.now()
            session.commit()
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/rooms')
@login_required
def room_list():
    rooms = Room.get_all_rooms()
    return render_template('rooms.html', rooms=rooms)

@app.route('/customers')
@login_required
def customer_list():
    customers = session.query(Customer).all()
    return render_template('customers.html', customers=customers)

@app.route('/bookings')
@login_required
def booking_list():
    bookings = session.query(Booking).options(
        joinedload(Booking.customer), 
        joinedload(Booking.room)
    ).all()
    
    customers = session.query(Customer).all()
    available_rooms = session.query(Room).filter(Room.status == 'AVAILABLE').all()

    return render_template('bookings.html', bookings=bookings, customers=customers, available_rooms=available_rooms)

@app.route('/add_booking', methods=['POST'])
@login_required
def add_booking():
    # Get form data
    customer_id = request.form.get('customer_id')
    room_id = request.form.get('room_id')
    check_in_date = request.form.get('check_in_date')
    check_out_date = request.form.get('check_out_date')

    try:
        # Convert to datetime objects
        check_in_date = datetime.strptime(check_in_date, '%Y-%m-%d')
        check_out_date = datetime.strptime(check_out_date, '%Y-%m-%d')
    except ValueError:
        flash('Ngày không hợp lệ. Vui lòng kiểm tra lại.', 'error')
        return redirect(url_for('booking_list'))

    # Get room and validate availability
    room = session.query(Room).get(room_id)
    if room and room.status == 'AVAILABLE':
        # Calculate total price (example logic)
        days = (check_out_date - check_in_date).days
        if days <= 0:
            flash('Ngày trả phòng phải lớn hơn ngày nhận phòng.', 'error')
            return redirect(url_for('booking_list'))
        total_price = days * room.price_per_night

        # Create and add the new booking
        new_booking = Booking(
            customer_id=customer_id,
            room_id=room_id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            total_price=total_price,
            status='CONFIRMED'
        )
        session.add(new_booking)

        # Update room status to 'OCCUPIED'
        room.status = 'OCCUPIED'
        session.commit()

        flash('Đặt phòng thành công!', 'success')
    else:
        flash('Phòng không có sẵn hoặc đã được đặt!', 'error')

    return redirect(url_for('booking_list'))

def create_report():
    total_rooms = session.query(Room).count()
    total_occupied_rooms = session.query(Room).filter(Room.status == 'Đã sử dụng').count()
    total_active_bookings = session.query(Booking).filter(Booking.status == 'CONFIRMED').count()
    
    total_revenue = session.query(Booking).join(Room).filter(Booking.status == 'CONFIRMED').\
                    filter(Booking.check_out_date <= datetime.now()).\
                    with_entities(Room.price_per_night).all()
    
    revenue = sum(room.price_per_night for room in total_revenue)

    new_report = Report(
        total_rooms=total_rooms,
        total_occupied_rooms=total_occupied_rooms,
        total_active_bookings=total_active_bookings,
        total_revenue=revenue
    )
    
    session.add(new_report)
    session.commit()

@app.route('/report')
@login_required
def report_list():
    reports = session.query(Report).all()
    return render_template('reports.html', reports=reports)


from flask import redirect, url_for, flash
from flask_login import logout_user, login_required

@app.route('/room/<int:room_id>')
@login_required
def room_detail(room_id):
    room = session.query(Room).get(room_id)
    if room:
        return render_template('room_detail.html', room=room)
    else:
        flash('Room not found!', 'error')
        return redirect(url_for('room_list'))

@app.route('/edit_room/<int:room_id>', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = session.query(Room).get(room_id)
    if request.method == 'POST':
        room.room_number = request.form['room_number']
        room.room_type = request.form['room_type']
        room.price_per_night = float(request.form['price'])
        session.commit()
        flash('Room updated successfully!', 'success')
        return redirect(url_for('room_list'))
    
    if room:
        return render_template('edit_room.html', room=room)
    else:
        flash('Room not found!', 'error')
        return redirect(url_for('room_list'))

@app.route('/delete_room/<int:room_id>', methods=['POST'])
@login_required
def delete_room(room_id):
    room = session.query(Room).get(room_id)
    
    if not room:
        flash("Room not found", "error")
        return redirect(url_for('room_list'))

    # Kiểm tra các booking còn hiệu lực của phòng
    active_bookings = session.query(Booking).filter(
        Booking.room_id == room_id,
        Booking.status.in_(['CONFIRMED', 'IN_PROGRESS'])
    ).all()
    
    if active_bookings:
        flash("Cannot delete room with active bookings", "error")
        return redirect(url_for('room_list'))

    # Nếu có các booking đã hủy hoặc hoàn thành, ta sẽ xóa chúng trước
    old_bookings = session.query(Booking).filter(
        Booking.room_id == room_id,
        Booking.status.in_(['CANCELLED', 'COMPLETED'])
    ).all()
    
    # Xóa các booking cũ
    for booking in old_bookings:
        session.delete(booking)

    # Xóa phòng
    try:
        session.delete(room)
        session.commit()
        flash("Room deleted successfully", "success")
    except Exception as e:
        session.rollback()
        flash(f"Error deleting room: {str(e)}", "error")

    return redirect(url_for('room_list'))


@login_required
def booking_list():
    bookings = session.query(Booking).options(
        joinedload(Booking.customer), 
        joinedload(Booking.room)
    ).all()
    
    customers = session.query(Customer).all()
    available_rooms = session.query(Room).filter(Room.status == 'AVAILABLE').all()

    return render_template('bookings.html', bookings=bookings, customers=customers, available_rooms=available_rooms)

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    booking = session.query(Booking).get(booking_id)
    
    if not booking:
        flash('Không tìm thấy booking!', 'danger')
        return redirect(url_for('booking_list'))
    
    # Update booking status to CANCELLED
    booking.status = 'CANCELLED'
    
    # Update the room status to AVAILABLE
    room = booking.room
    if room:
        room.status = 'AVAILABLE'  

    try:
        session.commit()
        flash(f'Booking #{booking.id} đã được hủy thành công!', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Đã xảy ra lỗi khi hủy booking: {str(e)}', 'danger')

    return redirect(url_for('booking_list'))


@app.route('/delete_customer/<int:customer_id>', methods=['POST'])
@login_required
def delete_customer(customer_id):
    customer = session.query(Customer).get(customer_id)
    if customer:
        session.delete(customer)
        session.commit()
        flash('Customer deleted successfully!', 'success')
    else:
        flash('Customer not found!', 'error')
    return redirect(url_for('customer_list'))

@app.route('/logout')
@login_required
def logout():
    # Đăng xuất người dùng
    logout_user()
    
    # Hiển thị thông báo đăng xuất thành công
    flash('Bạn đã đăng xuất thành công.', 'info')
    
    # Chuyển hướng về trang đăng nhập
    return redirect(url_for('login'))


@app.route('/add_room', methods=['GET', 'POST'])
@login_required
def add_room():
    if request.method == 'POST':
        room_number = request.form['room_number']
        room_type = request.form['room_type']
        price = request.form['price']
        
        new_room = Room(
            room_number=room_number,
            room_type=room_type,
            price_per_night=float(price),
            status='AVAILABLE'
        )
        
        session.add(new_room)
        session.commit()
        
        flash('Room added successfully!', 'success')
        return redirect(url_for('room_list'))
    
    return render_template('rooms.html')



@app.route('/add_customer', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        address = request.form['address']
        
        # Validate data if necessary
        new_customer = Customer(
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            address=address
        )
        
        session.add(new_customer)
        session.commit()
        
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customer_list'))
    
    return render_template('customers.html')

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/favicon.ico')
def favicon():
    return '', 204  # Trả về trạng thái 204 (No Content)


if __name__ == '__main__':
    app.run(debug=False)