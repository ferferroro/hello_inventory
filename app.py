from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import ast 

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
    price = db.Column(db.Float)
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

class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(50))
    balance = db.Column(db.Float)
    remarks = db.Column(db.String(50))

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
            return redirect(url_for('home'))
        else:
            return render_template('index.html', message='Invalid Login!')
        # return f'uid: {username} pwd: {password}'

@app.route('/home')
@login_required
def home():
    prod_count = Product.query.count()
    adj_count = AdjustmentDetail.query.count()
    purch_count =  Customer.query.count()
    cust_count = Customer.query.count()
    return render_template('home.html', **locals())  

@app.route('/customers')
@login_required
def customers():
    all_customers = Customer.query.all()
    return render_template('customers.html', all_customers=all_customers)  

@app.route('/add_customer', methods=['POST', 'GET'])
@login_required
def add_customer():
    # multi line assign
    message, css_class, fullname, balance, remarks = ('', '', '', '', '')

    if request.method == 'GET':
        return render_template('add_customer.html', **locals())  
    
    if request.method == 'POST':
        fullname = request.form['fullname']
        balance = request.form['balance']
        remarks = request.form['remarks']

        new_customer = Customer(fullname=fullname, balance=balance, remarks=remarks)
        db.session.add(new_customer)
        db.session.commit()
        message = f'Customer : {new_customer.fullname} added'
        css_class = 'alert-success'
        return render_template('add_customer.html', **locals())  

@app.route('/edit_customer/<string:id>', methods=['POST', 'GET'])
@login_required
def edit_customer(id):
    # multi line assign
    message, css_class, fullname, balance, remarks = ('', '', '', '', '')

    edit_customer = Customer.query.filter_by(id=id).first_or_404()

    if edit_customer: 

        if request.method == 'GET':
            fullname, balance, remarks = edit_customer.fullname, edit_customer.balance, edit_customer.remarks
            return render_template('edit_customer.html', **locals())  
        
        if request.method == 'POST':
            fullname = request.form['fullname']
            balance = request.form['balance']
            remarks = request.form['remarks']

            edit_customer.fullname, edit_customer.balance, edit_customer.remarks = fullname, balance, remarks
            db.session.commit()
            message = f'Customer : {edit_customer.fullname} updated'
            css_class = 'alert-success'
            return render_template('edit_customer.html', **locals())  

@app.route('/delete_customer/<string:id>', methods=['POST'])
@login_required
def delete_customer(id):
    if request.method == 'POST':
        delete_customer = Customer.query.filter_by(id=id).first_or_404()
        if delete_customer:
            db.session.delete(delete_customer)
            db.session.commit()
            return redirect(url_for('customers'))

@app.route('/products')
@login_required
def products():
    all_products = Product.query.order_by(Product.updated_at.desc()).all()
    return render_template('products.html', all_products=all_products)    

@app.route('/add_product', methods=['POST', 'GET'])
@login_required
def add_product():
    # multi line assign
    message, css_class, code, name, quantity, price = ('', '', '', '', '', '')

    if request.method == 'GET':
        return render_template('add_product.html')  
    
    if request.method == 'POST':
        code = request.form['code']
        name = request.form['name']
        quantity = request.form['quantity']
        price = request.form['price']

        new_product = Product(code=code, name=name, quantity=quantity, price=price)
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
    message, css_class, code, name, quantity, price = ('', '', '', '', '', '')

    edit_product = Product.query.filter_by(id=id).first_or_404()

    if edit_product:
        
        if request.method == 'GET':
            code = edit_product.code
            name = edit_product.name
            quantity = edit_product.quantity
            price = edit_product.price
            return render_template('edit_product.html', **locals()) 

        if request.method == 'POST':
            # retrieve values from html form
            code = request.form['code']
            name = request.form['name']
            quantity = request.form['quantity']
            price = request.form['price']

            # query if the product code is already existing 
            existing_product = Product.query.filter(Product.code==code, Product.id!=edit_product.id).count()

            if existing_product:
                error_list = [f'Product code {edit_product.code} is already taken']
            else:
                # save new values to the new product 
                edit_product.code = code
                edit_product.name = name
                edit_product.quantity = quantity
                edit_product.price = price
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

@app.route('/adjustment', methods=['POST','GET'])
@login_required
def adjustment():
    adjustment_header = AdjustmentHeader.query.filter_by(id=1).first_or_404()

    if request.method == 'GET':
        return render_template('adjustment.html', 
            adjustment_header=adjustment_header,
            message='', 
            css_class=''
        )   
    
    if request.method == 'POST' and adjustment_header: 
        # get the submit type | save or apply
        submit_type = request.form['submit_type']

        # if load products 
        if submit_type == '1':
            # get all the products
            all_products = Product.query.all()
            for product in all_products:
                existing_prod = AdjustmentDetail.query.filter_by(product_id=product.id).first()
                if not existing_prod:
                    adjustment_detail = AdjustmentDetail(quantity_adjust=0, 
                        adjustment_reference=adjustment_header, 
                        adjustment_detail=product)
                    db.session.add(adjustment_detail)
                    db.session.commit()
            # return redirect('/adjustment')
            return render_template('adjustment.html', 
                    adjustment_header=adjustment_header,
                    message='All the products has been loaded!', 
                    css_class='alert-success')

        if submit_type == 'save_adjustment' or submit_type == 'apply_adjustment':
            # get the form data 
            raw_datas = request.form 
            # set the form data to dictionary
            raw_datas = raw_datas.to_dict(flat=False)
            # strip off unwated characters
            raw_datas = str(raw_datas).replace("[", "")
            raw_datas = str(raw_datas).replace("]", "")
            # convert the raw data to a dictionary
            adj_lines = ast.literal_eval(raw_datas) 

            # save current adjustment 
            if submit_type == 'save_adjustment':
                # loop all lines
                for adj_id in adj_lines:
                    if adj_id == 'submit_type':
                        continue
                    # commit changes
                    adj_detail = AdjustmentDetail.query.filter_by(id=int(adj_id)).first()
                    if adj_detail:
                        adj_detail.quantity_adjust = int(adj_lines[adj_id])
                        db.session.commit()
                message = 'Adjustment has been Saved!'
            if submit_type == 'apply_adjustment':
                # loop all lines
                for adj_id in adj_lines:
                    if adj_id == 'submit_type':
                        continue
                    # commit changes
                    adj_detail = AdjustmentDetail.query.filter_by(id=int(adj_id)).first()
                    if adj_detail:
                        # save the current screen to adjustment datail table
                        adj_detail.quantity_adjust = int(adj_lines[adj_id])
                        # now save to the product able
                        prod = Product.query.filter_by(id=adj_detail.product_id).first()
                        if prod:
                            prod.quantity = adj_detail.quantity_adjust
                            adj_detail.quantity_adjust = 0
                        db.session.commit()
                message = 'Adjustment has been Applied!'

            return render_template('adjustment.html', 
                    adjustment_header=adjustment_header,
                    message=message, 
                    css_class='alert-success'
                ) 
        temp_char = submit_type.split('-')
        if temp_char[0] == "DEL":
            adj_detail = AdjustmentDetail.query.filter_by(id=int(temp_char[1])).first()
            if adj_detail:
                db.session.delete(adj_detail)
                db.session.commit()
                return render_template('adjustment.html', 
                        adjustment_header=adjustment_header,
                        message='Stock adjustment line removed!', 
                        css_class='alert-success')

@app.route('/purchase', methods=['POST','GET'])
@login_required
def purchase():
    purchase_header = PurchaseHeader.query.filter_by(id=1).first_or_404()

    receive_field_state = ''
    purchase_field_state = ''
    if purchase_header.status == 'New':
        receive_field_state = ''
        receive_field_state = 'readonly="readonly"'
    elif purchase_header.status == 'In Transit':
        receive_field_state = 'readonly="readonly"'
        purchase_field_state = 'readonly="readonly"'
    elif  purchase_header.status == 'Received':
        receive_field_state = ''
        purchase_field_state = 'readonly="readonly"'

    if request.method == 'GET':
        return render_template('purchase.html', 
            purchase_header=purchase_header,
            message='', 
            css_class='',
            receive_field_state=receive_field_state,
            purchase_field_state=purchase_field_state
        )   
    
    if request.method == 'POST' and purchase_header: 
        # get the submit type | save or apply
        submit_type = request.form['submit_type']
        css_class = 'alert-success' 

        # if load products 
        if submit_type == '1':
            # get all the products
            all_products = Product.query.all()
            for product in all_products:
                existing_prod = PurchaseDetail.query.filter_by(product_id=product.id).first()
                if not existing_prod:
                    purchase_detail = PurchaseDetail(quantity_purchase=0, 
                        quantity_receive=0,
                        purchase_reference=purchase_header, 
                        purchase_detail=product)
                    db.session.add(purchase_detail)
                    db.session.commit()
            return render_template('purchase.html', 
                purchase_header=purchase_header,
                message='Products has been loaded!', 
                css_class='alert-success',
                receive_field_state=receive_field_state,
                purchase_field_state=purchase_field_state
            )   

        if (submit_type == 'save_purchase' or 
            submit_type == 'export_purchase' or
            submit_type == 'start_purchase' or
            submit_type == 'receive_purchase' or
            submit_type == 'apply_purchase'
            ):
            # get the form data 
            raw_datas = request.form 
            # set the form data to dictionary
            raw_datas = raw_datas.to_dict(flat=False)
            # strip off unwated characters
            raw_datas = str(raw_datas).replace("[", "")
            raw_datas = str(raw_datas).replace("]", "")
            # convert the raw data to a dictionary
            purch_lines = ast.literal_eval(raw_datas) 
            # return purch_lines
            

            ####### dodgy code START - never do this - im running out of time so okay for now  ######
            purch_lines.pop('submit_type')
            temp_purch_list = []
            purch_lines_new = []

            # Loop 1 - build the purchase qty 
            for temp in purch_lines:
                # split the individual form data 
                temp_char = temp.split('-') 
                temp_char.append(str(purch_lines[temp]))
                # build the temporary list
                if temp_char[0] == 'PURCHASE':
                    temp_dict = { 'id':  temp_char[1],
                                   'prod_code': temp_char[2],
                                   'purch_qty': temp_char[3],
                                   'receive_qty': '0'
                                }
                    temp_purch_list.append(temp_dict)

            # Loop 2 - add the receive qty 
            for temp in purch_lines:
               # split the individual form data 
                temp_char = temp.split('-') 
                temp_char.append(str(purch_lines[temp]))
                if temp_char[0] == 'RECEIVE':
                    for item in temp_purch_list:
                        if item['prod_code'] == temp_char[2]:
                            item['receive_qty'] = str(purch_lines[temp])
                            # return item 
                            purch_lines_new.append(item)

            ####### dodgy code END - never do this - im running out of time so okay for now  ######     

            # save current purchase
            # if submit_type == 'save_purchase':
            # loop all lines
            for purch_item in purch_lines_new:
                # check purchase detail exist
                purchase_detail = PurchaseDetail.query.filter_by(id=str(purch_item['id'])).first()
                if purchase_detail:
                    # check product exist
                    prod = Product.query.filter_by(code=purch_item['prod_code']).first()
                    if prod:
                        purchase_detail.quantity_purchase = int(purch_item['purch_qty'])
                        purchase_detail.quantity_receive = int(purch_item['receive_qty'])
            # throw success message 
            message = 'Changes has been saved!'

            if submit_type == 'start_purchase':
                purchase_header.status = 'In Transit'
                db.session.commit()
                receive_field_state = 'readonly="readonly"'
                purchase_field_state = 'readonly="readonly"'
                message = 'Purchase now in Transit, you cannot update quantity until you Receive the goods!'

            if submit_type == 'receive_purchase':
                purchase_header.status = 'Received'
                db.session.commit()
                receive_field_state = ''
                purchase_field_state = 'readonly="readonly"'
                message = 'Purchase received, please match the purchase quantity against the receive quantity!'

            if submit_type == 'export_purchase':
                message = " Sorry this module is not yet available! "
                css_class = 'alert-danger'

            if submit_type == 'apply_purchase':
                if purchase_header.status != 'Received':
                    message="Unable to apply purchase, please contact administrator!"
                    css_class='alert-danger'
                else:
                    purchase_header.status = 'New'
                    # save the quantity to product atble 
                    for purch_item in purch_lines_new:
                        # check purchase detail exist
                        purchase_detail = PurchaseDetail.query.filter_by(id=str(purch_item['id'])).first()
                        if purchase_detail:
                            # now save to the product able
                            prod = Product.query.filter_by(id=purchase_detail.product_id).first()
                            if prod:
                                prod.quantity = prod.quantity + purchase_detail.quantity_receive
                                purchase_detail.quantity_purchase = 0
                                purchase_detail.quantity_receive = 0
                    db.session.commit()
                    receive_field_state = ''
                    receive_field_state = 'readonly="readonly"'
                    message="Purchase complete!"
                    css_class='alert-success'


            return render_template('purchase.html', 
                purchase_header=purchase_header,
                message=message, 
                css_class=css_class,
                receive_field_state=receive_field_state,
                purchase_field_state=purchase_field_state
            )  

        temp_char = submit_type.split('-')
        if temp_char[0] == "DEL":
            if purchase_header.status == 'New':
                purch_detail = PurchaseDetail.query.filter_by(id=int(temp_char[1])).first()
                if purch_detail:
                    db.session.delete(purch_detail)
                    db.session.commit()
                    message = 'Line has been removed!'
                    css_class = 'alert-success'
            else:
                message = 'Remove not allowed!'
                css_class = 'alert-danger'

            receive_field_state = ''
            receive_field_state = 'readonly="readonly"'
            return render_template('purchase.html', 
                    purchase_header=purchase_header,
                    message=message, 
                    css_class=css_class,
                    receive_field_state=receive_field_state,
                    purchase_field_state=purchase_field_state)
    

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

        return render_template('changepassword.html',message=save_status, css_class=css_alert_class)
    
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
