from app import db, User, Product, AdjustmentHeader, AdjustmentDetail, PurchaseHeader

db.create_all()

dev_user = User(username='dev', password='dev')
# print(dev_user.password)    
dev_user.hash_password(password=dev_user.password)
# print(dev_user.password, dev_user.check_password(password='devx'))
db.session.add(dev_user)
db.session.commit()

# kopiko = Product(code='KPKB',name='Kopiko Black', quantity=0)
# db.session.add(kopiko)
# db.session.commit()

adjustment = AdjustmentHeader(description='Stock Adjustment')
db.session.add(adjustment)
db.session.commit()

# adjustment_detail = AdjustmentDetail(quantity_adjust=10, adjustment_reference=adjustment, adjustment_detail=kopiko)
# db.session.add(adjustment_detail)
# db.session.commit()

purchase = PurchaseHeader(description='Stock Adjustment')
db.session.add(purchase)
db.session.commit()

# # get the values
# get_adjustment = AdjustmentHeader.query.filter_by(id=1).first()

# print(get_adjustment.description)
# print(get_adjustment.adjustment_details[0].quantity_adjust)
# print(get_adjustment.adjustment_details[0].adjustment_detail.code)
# print(get_adjustment.adjustment_details[0].adjustment_detail.name)