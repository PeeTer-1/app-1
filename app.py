from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
import os
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marketplace.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ----------- Models -----------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_premium = db.Column(db.Boolean, default=False)
    products = db.relationship('Product', backref='seller', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(200), nullable=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_advertised = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    category = db.Column(db.String(50), nullable=True)
    condition = db.Column(db.String(50), nullable=True)
    quantity = db.Column(db.Integer, default=1)

# ----------- Routes -----------
@app.route('/')
def home():
    search_query = request.args.get('search', '')
    category = request.args.get('category', '')
    
    query = Product.query
    
    if search_query:
        query = query.filter(Product.name.contains(search_query))
    
    if category:
        query = query.filter(Product.category == category)
    
    # Show advertised products first
    products = query.order_by(Product.is_advertised.desc(), Product.created_at.desc()).all()
    
    return render_template('home.html', 
                          products=products, 
                          search_query=search_query,
                          category=category,
                          user_id=session.get('user_id'),
                          is_premium=session.get('is_premium', False))

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        seller = User.query.get(product.seller_id)
        
        # Get related products (same category)
        related_products = []
        if product.category:
            related_products = Product.query.filter(
                Product.category == product.category,
                Product.id != product.id
            ).limit(4).all()
            
        return render_template('product_detail.html', 
                              product=product, 
                              seller=seller,
                              related_products=related_products,
                              user_id=session.get('user_id'),
                              is_premium=session.get('is_premium', False))
    except Exception as e:
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
        return redirect(url_for('home'))

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        flash('กรุณาเข้าสู่ระบบก่อนเพิ่มสินค้า', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            name = request.form['name']
            price = float(request.form['price'])
            description = request.form['description']
            category = request.form.get('category')
            condition = request.form.get('condition')
            quantity = int(request.form.get('quantity', 1))
            
            # Validate data
            if not name or price <= 0:
                flash('กรุณากรอกชื่อสินค้าและราคาให้ถูกต้อง', 'danger')
                return redirect(url_for('add_product'))
                
            # Handle image upload
            image_filename = None
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and image_file.filename != '' and allowed_file(image_file.filename):
                    # Generate unique filename
                    filename = secure_filename(image_file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                    image_filename = unique_filename
            
            new_product = Product(
                name=name, 
                price=price, 
                description=description, 
                image=image_filename, 
                seller_id=session['user_id'],
                category=category,
                condition=condition,
                quantity=quantity
            )
            
            db.session.add(new_product)
            db.session.commit()
            flash('เพิ่มสินค้าสำเร็จ!', 'success')
            return redirect(url_for('home'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
            return redirect(url_for('add_product'))

    return render_template('add_product.html',
                          is_premium=session.get('is_premium', False))

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'user_id' not in session:
        flash('กรุณาเข้าสู่ระบบก่อนแก้ไขสินค้า', 'warning')
        return redirect(url_for('login'))
        
    product = Product.query.get_or_404(product_id)
    
    # Check if current user is the seller
    if product.seller_id != session['user_id']:
        flash('คุณไม่มีสิทธิ์แก้ไขสินค้านี้', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        try:
            product.name = request.form['name']
            product.price = float(request.form['price'])
            product.description = request.form['description']
            product.category = request.form.get('category')
            product.condition = request.form.get('condition')
            product.quantity = int(request.form.get('quantity', 1))
            
            # Handle image upload
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and image_file.filename != '' and allowed_file(image_file.filename):
                    # Generate unique filename
                    filename = secure_filename(image_file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                    
                    # Delete old image if exists
                    if product.image:
                        try:
                            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image)
                            if os.path.exists(old_image_path):
                                os.remove(old_image_path)
                        except:
                            pass
                            
                    product.image = unique_filename
            
            db.session.commit()
            flash('แก้ไขสินค้าสำเร็จ!', 'success')
            return redirect(url_for('product_detail', product_id=product.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
            
    return render_template('edit_product.html', 
                          product=product,
                          is_premium=session.get('is_premium', False))

@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    if 'user_id' not in session:
        flash('กรุณาเข้าสู่ระบบก่อนลบสินค้า', 'warning')
        return redirect(url_for('login'))
        
    product = Product.query.get_or_404(product_id)
    
    # Check if current user is the seller
    if product.seller_id != session['user_id']:
        flash('คุณไม่มีสิทธิ์ลบสินค้านี้', 'danger')
        return redirect(url_for('home'))
        
    try:
        # Delete product image if exists
        if product.image:
            try:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            except:
                pass
                
        db.session.delete(product)
        db.session.commit()
        flash('ลบสินค้าสำเร็จ!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
        
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            confirm_password = request.form.get('confirm_password')
            
            # Simple validation
            if not username or not password:
                flash('กรุณากรอกชื่อผู้ใช้และรหัสผ่าน', 'danger')
                return render_template('register.html')
                
            if password != confirm_password:
                flash('รหัสผ่านไม่ตรงกัน', 'danger')
                return render_template('register.html')
                
            # Check if username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('ชื่อผู้ใช้นี้มีอยู่แล้ว กรุณาใช้ชื่ออื่น', 'danger')
                return render_template('register.html')
            
            # Create new user
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            
            flash('สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            
            user = User.query.filter_by(username=username).first()
            if user and bcrypt.check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['username'] = user.username
                session['is_premium'] = user.is_premium
                flash(f'ยินดีต้อนรับกลับ {username}!', 'success')
                return redirect(url_for('home'))
            else:
                flash('เข้าสู่ระบบไม่สำเร็จ กรุณาตรวจสอบชื่อผู้ใช้และรหัสผ่าน', 'danger')
                
        except Exception as e:
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_premium', None)
    flash('ออกจากระบบสำเร็จ!', 'success')
    return redirect(url_for('home'))

@app.route('/upgrade_premium')
def upgrade_premium():
    if 'user_id' not in session:
        flash('กรุณาเข้าสู่ระบบก่อนอัพเกรด', 'warning')
        return redirect(url_for('login'))
        
    try:
        user = User.query.get(session['user_id'])
        if user:
            user.is_premium = True
            db.session.commit()
            session['is_premium'] = True
            flash('อัพเกรดเป็นสมาชิกพรีเมียมสำเร็จ!', 'success')
        else:
            flash('ไม่พบข้อมูลผู้ใช้', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
        
    return redirect(url_for('home'))

@app.route('/advertise/<int:product_id>')
def advertise_product(product_id):
    if 'user_id' not in session:
        flash('กรุณาเข้าสู่ระบบก่อนโฆษณาสินค้า', 'warning')
        return redirect(url_for('login'))
        
    try:
        product = Product.query.get_or_404(product_id)
        
        # Check if current user is the seller
        if product.seller_id != session['user_id']:
            flash('คุณไม่มีสิทธิ์โฆษณาสินค้านี้', 'danger')
            return redirect(url_for('home'))
            
        # Check if user is premium
        user = User.query.get(session['user_id'])
        if not user.is_premium:
            flash('คุณต้องเป็นสมาชิกพรีเมียมก่อนจึงจะโฆษณาสินค้าได้', 'warning')
            return redirect(url_for('upgrade_premium'))
            
        product.is_advertised = True
        db.session.commit()
        flash('โฆษณาสินค้าสำเร็จ!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
        
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/my_products')
def my_products():
    if 'user_id' not in session:
        flash('กรุณาเข้าสู่ระบบก่อนดูสินค้าของคุณ', 'warning')
        return redirect(url_for('login'))
        
    products = Product.query.filter_by(seller_id=session['user_id']).order_by(Product.created_at.desc()).all()
    return render_template('my_products.html', 
                          products=products,
                          is_premium=session.get('is_premium', False))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)