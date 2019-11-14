from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__) # '__main__ or app'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'etoaysekretolamang'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), unique=True)
    password = db.Column(db.String(200))

    def hash_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True)
    name = db.Column(db.String(50))
    quantity = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    adjustment_line = db.relationship('AdjustmentDetail',backref='adjustment_detail')
    purchase_line = db.relationship('PurchaseDetail',backref='purchase_detail')

    def check_fields(self, mode):
        error_list = []

        if self.code == '':
            error_list.append('Invalid Product code')
        else:
            if mode == 'Add':
                check_prod = Product.query.filter_by(code=self.code).first()
                if check_prod:
                    error_list.append(f'Product code: {self.code} already exist')
        
        if self.name == '':
            error_list.append('Invalid Product Name')
        
        if not self.quantity.isdigit():
            error_list.append('Invalid Product Quantity')
        else:
            self.quantity = int(self.quantity)
        
        return error_list

class AdjustmentHeader(db.Model):
    __tablename__ = 'adjustment_header'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(30))
    adjustment_details = db.relationship('AdjustmentDetail', backref='adjustment_reference')

class AdjustmentDetail(db.Model):
    __tablename__ = 'adjustment_detail'
    id = db.Column(db.Integer, primary_key=True)
    quantity_adjust = db.Column(db.Integer)
    adjustment_header_id = db.Column(db.Integer, db.ForeignKey('adjustment_header.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))

class PurchaseHeader(db.Model):
    __tablename__ = 'purchase_header'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(30))
    status = db.Column(db.String(30))
    purchase_details = db.relationship('PurchaseDetail', backref='purchase_reference')

class PurchaseDetail(db.Model):
    __tablename__ = 'purchase_detail'
    id = db.Column(db.Integer, primary_key=True)
    quantity_purchase = db.Column(db.Integer)
    quantity_receive = db.Column(db.Integer)
    purchase_header_id = db.Column(db.Integer, db.ForeignKey('purchase_header.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signin', methods=['POST'])
def signin():
    if request.method == 'POST':
        # get the values from the html form
        username = request.form['username']
        password = request.form['password']

        # query if the user is existing on db
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password=password):
            login_user(user)
            return redirect(url_for('products'))
        else:
            return render_template('index.html', message='Invalid Login!')
        # return f'uid: {username} pwd: {password}'

@app.route('/products')
@login_required
def products():
    all_products = Product.query.order_by(Product.updated_at.desc()).all()
    return render_template('products.html', all_products=all_products)    

@app.route('/add_product', methods=['POST', 'GET'])
@login_required
def add_product():
    # multi line assign
    message, css_class, code, name, quantity = ('', '', '', '', '')

    if request.method == 'GET':
        return render_template('add_product.html')  
    
    if request.method == 'POST':
        code = request.form['code']
        name = request.form['name']
        quantity = request.form['quantity']

        new_product = Product(code=code, name=name, quantity=quantity)
        error_list = new_product.check_fields(mode='Add')

        if error_list:
            message = 'Please check errors. [ ' + ','.join(error_list) +' ]'
            css_class = 'alert-danger'
            return render_template('add_product.html', **locals())  
        else:
            db.session.add(new_product)
            db.session.commit()
            message = f'Product code: {new_product.code} added'
            css_class = 'alert-success'
            code, name, quantity = ('', '', '')
            return render_template('add_product.html', **locals())  


@app.route('/edit_product/<string:id>', methods=['POST', 'GET'])
@login_required
def edit_product(id):
    # multi line assign
    message, css_class, code, name, quantity = ('', '', '', '', '')

    edit_product = Product.query.filter_by(id=id).first_or_404()

    if edit_product:
        
        if request.method == 'GET':
            code = edit_product.code
            name = edit_product.name
            quantity = edit_product.quantity
            return render_template('edit_product.html', **locals()) 

        if request.method == 'POST':
            # retrieve values from html form
            code = request.form['code']
            name = request.form['name']
            quantity = request.form['quantity']

            # query if the product code is already existing 
            existing_product = Product.query.filter(Product.code==code, Product.id!=edit_product.id).count()

            if existing_product:
                error_list = [f'Product code {edit_product.code} is already taken']
            else:
                # save new values to the new product 
                edit_product.code = code
                edit_product.name = name
                edit_product.quantity = quantity
                # validate if fields are blank 
                error_list = edit_product.check_fields(mode='Edit')

            if error_list:
                message = 'Please check errors. [ ' + ','.join(error_list) +' ]'
                css_class = 'alert-danger'
                return render_template('edit_product.html', **locals())  
            else:
                # save to database 
                db.session.commit()
                message = f'Product code: {edit_product.code} updated'
                css_class = 'alert-success'
                return render_template('edit_product.html', **locals())   
    else:
        return 'Invalid Request'

@app.route('/delete_product/<string:id>', methods=['POST'])
@login_required
def delete_product(id):
    if request.method == 'POST':
        delete_product = Product.query.filter_by(id=id).first_or_404()
        if delete_product:
            db.session.delete(delete_product)
            db.session.commit()
            return redirect(url_for('products'))

@app.route('/adjustment')
@login_required
def adjustment():
    return render_template('adjustment.html')   

@app.route('/purchase')
@login_required
def purchase():
    return render_template('purchase.html')   

@app.route('/changepassword', methods=['POST', 'GET'])
@login_required
def changepassword():
    if request.method == 'GET':
        return render_template('changepassword.html') 

    if request.method == 'POST':
        save_status = ''
        css_alert_class = ''

        username = request.form['username']
        oldpassword = request.form['oldpassword']
        newpassword = request.form['newpassword']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password=oldpassword) and newpassword != '':
            user.hash_password(password=newpassword)
            db.session.commit()
            save_status = 'Password change complete!'
            css_alert_class = 'alert-success'
        else:
           save_status = 'Password change failed!'
           css_alert_class = 'alert-danger'

        return render_template('changepassword.html',message=save_status, css_alert_class=css_alert_class)
    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# if __name__ = '__main__':
#     app.run(debug=True)


@app.route('/resetdevpassword')
def resetdevpassword():
    user = User.query.filter_by(username='dev').first()
    if user:
        user.hash_password(password='dev')
        db.session.commit()
    return redirect('/')