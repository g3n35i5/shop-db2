from shopdb.models import *
from shopdb.api import bcrypt


def insert_dev_data(db):
    # Insert default ranks
    ranks = [
        {'name': 'Contender', 'debt_limit': 0},
        {'name': 'Member', 'debt_limit': -2000},
        {'name': 'Alumni', 'debt_limit': -1000}
    ]
    for rank in ranks:
        rank = Rank(name=rank['name'], debt_limit=rank['debt_limit'])
        db.session.add(rank)
    db.session.commit()

    # Insert admin
    user = User(
        firstname='John',
        lastname='Doe',
        password=bcrypt.generate_password_hash('1234'))
    db.session.add(user)
    au = AdminUpdate(user_id=1, admin_id=1, is_admin=True)
    db.session.add(au)
    user.verify(admin_id=1, rank_id=2)
    db.session.add(user)

    # Insert all default users. Two of them have a password defined.
    usernames = [
        {'firstname': 'Andree', 'lastname': 'Owings', 'password': '1234'},
        {'firstname': 'Milan', 'lastname': 'Glazier', 'password': '1234'},
        {'firstname': 'Hiroko', 'lastname': 'Trinh'},
        {'firstname': 'Malia', 'lastname': 'Constance'},
        {'firstname': 'Rob', 'lastname': 'Hydrick'}
    ]
    for index, user in enumerate(usernames):
        firstname = user['firstname']
        lastname = user['lastname']
        password = None
        if 'password' in user:
            password = user['password']
        user = User(
            firstname=firstname,
            lastname=lastname,
            password=password)
        db.session.add(user)

    db.session.commit()

    # Verify the first three users
    verifications = [
        {'user_id': 2, 'rank_id': 1},
        {'user_id': 3, 'rank_id': 2},
        {'user_id': 4, 'rank_id': 3}
    ]
    for verification in verifications:
        user = User.query.filter_by(id=verification['user_id']).first()
        user.verify(admin_id=1, rank_id=verification['rank_id'])

    db.session.commit()

    # Insert default products
    products = [
        {'name': 'Water', 'price': 100},
        {'name': 'Pizza', 'price': 300},
        {'name': 'Coca Cola', 'price': 150},
        {'name': 'Cookies', 'price': 50},
        {'name': 'Tea', 'price': 20},
        {'name': 'Coffee', 'price': 25}
    ]
    for item in products:
        product = Product(name=item['name'], created_by=1)
        db.session.add(product)
        db.session.flush()  # This is needed so that the product has its id
        product.set_price(price=int(item['price']), admin_id=1)

    db.session.commit()

    # Insert default purchases
    purchases = [
        {'user_id': 1, 'product_id': 3, 'amount': 12},
        {'user_id': 2, 'product_id': 5, 'amount': 13},
        {'user_id': 3, 'product_id': 3, 'amount': 15},
        {'user_id': 3, 'product_id': 2, 'amount': 3},
        {'user_id': 1, 'product_id': 2, 'amount': 9},
        {'user_id': 2, 'product_id': 4, 'amount': 7},
        {'user_id': 3, 'product_id': 6, 'amount': 1}
    ]

    for purchase in purchases:
        purchase = Purchase(
            user_id=purchase['user_id'],
            product_id=purchase['product_id'],
            amount=purchase['amount'])
        db.session.add(purchase)

    db.session.commit()

    # Insert default tags
    tags = ['Food', 'Drinks', 'Sweets', 'Coffee']
    for name in tags:
        tag = Tag(name=name, created_by=1)
        db.session.add(tag)
    db.session.commit()

    # Insert default replenishmentcollections
    product1 = Product.query.filter_by(id=1).first()
    product2 = Product.query.filter_by(id=2).first()
    product3 = Product.query.filter_by(id=3).first()
    rc1 = ReplenishmentCollection(admin_id=1, revoked=False, comment='Foo')
    rc2 = ReplenishmentCollection(admin_id=2, revoked=False, comment='Foo')
    for r in [rc1, rc2]:
        db.session.add(r)
    db.session.flush()
    rep1 = Replenishment(replcoll_id=rc1.id, product_id=product1.id,
                         amount=10, total_price=10 * product1.price)
    rep2 = Replenishment(replcoll_id=rc1.id, product_id=product2.id,
                         amount=20, total_price=20 * product2.price)
    rep3 = Replenishment(replcoll_id=rc2.id, product_id=product3.id,
                         amount=5, total_price=5 * product3.price)
    rep4 = Replenishment(replcoll_id=rc2.id, product_id=product1.id,
                         amount=10, total_price=10 * product1.price)
    for r in [rep1, rep2, rep3, rep4]:
        db.session.add(r)
    db.session.commit()