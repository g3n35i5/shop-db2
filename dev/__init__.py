from shopdb.models import *
from shopdb.api import bcrypt
import random


def insert_dev_data(db):
    # Insert admin
    user = User(
        firstname='John',
        lastname='Doe',
        username='admin',
        email='john.doe@example.com',
        password=bcrypt.generate_password_hash('1234'))
    db.session.add(user)
    au = AdminUpdate(user_id=1, admin_id=1, is_admin=True)
    db.session.add(au)
    user.verify(admin_id=1)
    db.session.add(user)

    # Insert all random users
    usernames = open('./dev/usernames.txt', 'r').read().splitlines()
    for index, name in enumerate(usernames):
        firstname = name.split(',')[1]
        lastname = name.split(',')[0]
        username = 'random_{0:02d}'.format(index + 2)
        email = firstname.lower() + '.' + lastname.lower() + '@example.com'
        password = b'1234'
        user = User(
            firstname=firstname,
            lastname=lastname,
            username=username,
            email=email,
            password=password)
        db.session.add(user)

    db.session.commit()

    # Verify all users except id 1, 3, 5 and 7
    ids = range(1, 51)
    ids = [i for i in ids if i not in [1, 3, 5, 7]]
    for id in ids:
        user = User.query.filter_by(id=id).first()
        user.verify(admin_id=1)

    db.session.commit()

    # Insert default products
    products = open('./dev/products.txt', 'r').read().splitlines()
    for item in products:
        product = Product(name=item.split(',')[0], created_by=1)
        db.session.add(product)
        db.session.flush()  # This is needed so that the product has its id
        product.set_price(price=int(item.split(',')[1]), admin_id=1)

    db.session.commit()
    # Insert default purchases
    ids = open('./dev/purchases.txt', 'r').read().splitlines()
    for user_id in ids:
        purchase = Purchase(
            user_id=int(user_id),
            product_id=random.randint(1, 6),
            amount=random.randint(1, 10))
        db.session.add(purchase)

    db.session.commit()
