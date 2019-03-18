# shop-db2
This is the documentation for shop-db.

## Table of content

1.  [About shop.db](#about-shopdb)
2.  [Dependencies](#dependencies)
3.  [Getting started](#getting-started)
4.  [Development](#development)
5.  [Backups](#backups)
6.  [Unittests](#unittests)
7.  [Models](#models)


### About shop.db

We created shop.db in order to offer a simple way to manage purchases and
user interactions in a small community. Over time, the project grew bigger
and bigger and we decided to make it as flexible as possible, so that i can be
used for more applications than our small shop service. Even if the development
of shop.db has not progressed far enough to be called finished, we want to
share the project so anyone can contribute and make shop.db better. In the
following part, you can find a basic documentation for this project.

shop.db can be used as a standalone backend and can be accessed via it's API.
Because this is not an elegant way to use this application, we developed the
shop.db frontend, which can be found in it's own repository:
[shop-db-frontend](INSERT_LINK "Frontend for shop-db").
Furthermore, the complete administration is carried out via the specially
developed [shop-db-admin](INSERT_LINK "Admin tool for shop-db") interface.

### Dependencies

In order to use shop-db, you need to install the following main dependencies:
  1. Python 3.7
  2. Python 3.7 Virtual Environment
  3. pip3
  4. git
  5. nginx

```bash
$ sudo apt install python3.7 python3-venv python3-pip git nginx
```

### Getting started

Add an account for shop-db called shopdb_user. Since this account is only for
running shop-db the extra arguments of -r is added to create a system
account without creating a home directory:

```bash
$ sudo useradd -r shopdb_user
```

Next we will create a directory for the installation of shop-db and change
the owner to the shopdb_user account:

```bash
$ cd /srv
$ sudo git clone https://github.com/g3n35i5/shop-db2
$ sudo chown -R shopdb_user:shopdb_user shop-db2
```

Now the Nginx server must be configured. Nginx installs a test site in this
location that we wont't need, so let's remove it:

```bash
$ sudo rm /etc/nginx/sites-enabled/default
```

Below you can see the Nginx configuration file for shop-db, which goes in
/etc/nginx/sites-enabled/shop-db:

```nginx
server {
    # listen on port 80 (http)
    listen 80;
    server_name shopdb;
    location / {
        # redirect any requests to the same URL but on https
        return 301 https://$host$request_uri;
    }
}
server {
    # listen on port 443 (https)
    listen 443 ssl;
    server_name shopdb;

    # location of the SSL certificates
    ssl_certificate <PATH_TO_THE_CERTS>/cert.pem;
    ssl_certificate_key <PATH_TO_THE_CERTS>/key.pem;

    # write access and error logs to /var/log
    access_log /var/log/shop-db_access.log;
    error_log /var/log/shop-db_error.log;

    location / {
        # forward application requests to the gunicorn server
        proxy_pass http://localhost:<THE_PORT_IN_THE_CONFIGURATION>;
        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Next up is to create and change to a virtual environment for shop-db. This
will be done as the shopdb_user account:
```bash
$ sudo su -s /bin/bash shopdb_user
$ cd /srv/shop-db2
$ python3.7 -m venv .
$ source bin/activate
```

Once you have activated the virtual environment you will notice the prompt
change and then you can install the required python modules:

```bash
(shop-db) $ pip3.7 install -r requirements.txt
```

Now the configuration file of shop-db2 has to be adjusted.
Copy the `configuration.example.py` to the `configuration.py` file:
```bash
(shop-db) $ cp configuration.example.py configuration.py
```

The most important change is the SECRET_KEY. This is later responsible for
salting the user passwords and must be kept secret under all circumstances.
Change this SECRET_KEY in the file `configuration.py`. You can do this with a
normal text editor or with the command `sed`:

```bash
(shop-db) $ sed -i 's/YouWillNeverGuess/YOURBETTERSUPERSECRETKEY/g' configuration.py
```

The first user (and at the same time the first administrator) as well as the
default ranks are created using the `setupdb.py` script. Please look at the
file and check whether the default settings for the ranks meet your
requirements.

If you are satisfied with them, you can now initialize the database:

```bash
(shop-db) $ python3.7 ./setupdb.py
```

Ready? Almost. To start shop-db, you only have to type:

```bash
(shop-db) $ python3.7 ./wsgi.py
```

However, so that the backend does not have to be started manually every time, it
is advisable to run shop-db as a systemd service:

```bash
(shop-db) $ exit # To switch back to the root user
$ sudo nano /etc/systemd/system/shop-db2@shopdb_user.service
```

The file must have the following content:

```
[Unit]
Description=shop-db2
After=network-online.target

[Service]
Type=simple
User=%i
ExecStart=/srv/shop-db2/bin/python3.7 /srv/shop-db2/wsgi.py

[Install]
WantedBy=multi-user.target
```

You need to reload systemd to make the daemon aware of the new configuration:

```bash
$ sudo systemctl --system daemon-reload
```

To have shop-db start automatically at boot, enable the service:

```bash
$ sudo systemctl enable shop-db2@shopdb_user
```

To disable the automatic start, use this command:

```bash
$ sudo systemctl disable shop-db2@shopdb_user
```

To start shop-db now, use this command:

```bash
$ sudo systemctl start shop-db2@shopdb_user
```


### Development
You want to start shop-db in developer mode and participate in the project?
Great! The command

```bash
$ python3.7 ./shopdb.py --mode development
```

starts shop-db for you in developer mode. This means that a temporary database
is created in memory with default data defined in the dev folder. Your
production database will not be used in this mode, but you should make sure
you have a backup in case something goes wrong.


### Backups
To create backups from the database, you can use the `backup.py` script in the
root directory of shop-db. To do this regularly, either a service or a
crobjob can be used.

##### Option 1: systemd service
Create two files with the following content:

`/etc/systemd/system/shop-db-backup.service`:
```
[Unit]
Description=shop-db2 backup service

[Service]
Type=oneshot
ExecStart=/srv/shop-db2/bin/python3.7 /srv/shop-db2/backup.py
```

`/etc/systemd/system/shop-db-backup.timer`:
```
[Unit]
Description=Timer for the shop-db2 backup service.

[Timer]
OnCalendar=00/3

[Install]
WantedBy=timers.target
```

Reload the services and start the backup service by typing
```bash
$ systemctl daemon-reload
$ systemctl start shop-db2-backup.timer
```

If you want to check your timer and the states of the backups, you can use
```bash
$ systemctl list-timers --all
```

##### Option 2: cronjob
Create the following cronob:
```bash
0 */3 * * * /srv/shop-db2/backup.py
```

### Unittests
Currently, most of the core features of shop-db are covered with the
corresponding unittests. In order to execute them you can use the command

```bash
$ python3 -m coverage run test.py
```

If you want to check the test coverage, type

```bash
$ python3.7 -m coverage html
```
to generate the html preview and open a web server in the newly created
directory `htmlcov`

```bash
$ cd htmlcov
$ python3.7 -m http.server
```

### Models
This section covers the models used in shop-db. They are defined in
.shopdb/models.py

#### User

In order to interact with the database one needs some sort of user account
which stores personal data, privileges and that can be referenced by other
parts of the application. Therefor we use the User table. Anyone who can reach
the shop-db application can create a user. After creating User through
registering, one has to be verified by an admin to be able to use ones account.
This prevents unauthorized use of the application. In addition a user can be an
admin, has a rank, a credit to buy products and a list of favorite products.

| NAME | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The user id is unique and is used to identify the user in the application. It is created automatically with the a new user.
| creation_date | *DateTime* | This is the date and time the user was created. It is created automatically with the new user. It is not modified when user properties are updated.
| firstname | *String(32)* | This is the users firstname. It is used to identify the user in the frontend. It does not have to be unique. It can be updated and changed after the users creation.
| lastname | *String(32)* | This is the users lastname. It is used to identify the user in the frontend. It does not have to be unique. It can be updated and changed after the users creation.
| password | *String(256)* | This is the password hash which is used to verify the users password when he logs in. It is automatically created from the password passed when creating or updating the user. The password itself is not stored in the database.
| is_verified | *Boolean* | To prevent unauthorized access, each user has to be verified from an admin before he can carry out further actions. This column states whether the user is verified (True) or not (False).
| purchases | *relationship* | This represents all the purchases the user has made.

#### UserVerification

When a user is verified, a UserVerification entry is made. It is used to
separate information about the verification from the user. As a result a user
cant be verified twice and the verification date of a user can be called. A
UserVerification can only be made by an admin.

| NAME | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The UserVerification id is unique and is used for identification in the application. It is created automatically with a new UserVerification.
| timestamp | *DateTime* | This is the date and time the UserVerification was created. It is created automatically with the new UserVerification. It is not modified when updated.
| admin_id | *Integer* | This is the id of the admin who made this UserVerification.
| user_id | *Integer* | This is the id of the user the admin made this UserVerification for.

#### AdminUpdate

A lot of functionalities in the application require a user with admin rights.
The first user in database can make himself an admin. Every other user has to
be made admin by another admin. The admin rights can also be revoked. For every
change in a users admin rights, an AdminUpdate entry is made. The Admin update
table is used to verify whether the user is an admin by checking the is_admin
field in the latest entry related to the user.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The AdminUpdate id is unique and is used for identification in the application. It is created automatically with a new AdminUpdate.
| timestamp | *DateTime* | This is the date and time the AdminUpdate was created. It is created automatically with the new AdminUpdate.
| user_id | *Integer* | This is the id of the user whose admin status was updated.
| admin_id | *Integer* | This is the id of the admin who performed the update.
| is_admin | *Boolean* | Specifies whether the corresponding user is an admin (True) after the update or not (False).

#### Uploads

An admin can upload an image of a product to the application which is then
shown in the frontend. The UPLOAD_FOLDER can be set in configuration.py. There,
one can also specify the MAX_CONTENT_LENGTH and the valid file types via the
VALID_EXTENSIONS property. Through the uploads id, a product can be linked to
the Upload and the image.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The Upload id is unique and is used for identification in the application. It is created automatically with a new Upload.
| timestamp | *DateTime* | This is the date and time the Upload was created. It is created automatically with the new Upload.
| admin_id | *Integer* | This is the id of the admin who performed the Upload.
| filename | *String(64)* | This is the filename of the image that has been uploaded. It is saved in the UPLOAD_FOLDER and created automatically with the new Upload.

#### Rank

Depending on the rank, a User has can have different dept limits to his credit.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The Rank id is unique and is used for Identification in the application. It is created automatically with a new Rank.
| name | *String(32)* | The Rank name is unique and is used for identification in the frontend.
| dept_limit | *Integer* | This specifies the dept limit a user with given Rank can have in his credit.

### RankUpdate

When a user is verified, he has to be assigned a rank. Afterwards, the rank can
always be updated by an admin. Each time a users rank is set or changed, a
RankUpdate entry is made. To determine a users current rank, the rank_id field
is checked for the latest entry related to the user.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The RankUpdate id is unique and is used for identification in the application. It is created automatically with a new RankUpdate.
| timestamp | *DateTime* | This is the date and time the RankUpdate was created. It is created automatically with the new RankUpdate.
| user_id | *Integer* | This is the id of the user whose rank was updated.
| admin_id | *Integer* | This is the id of the who performed the update.
| rank_id | *Integer* | This is the id of the rank the user was updated to.

#### Product

Each item that can be sold through the application has to be a product. A
product can only be created by an admin. A product can have an image which is
shown in the frontend to identify it. In addition, each product has a price and
a pricehistory. Furthermore tags are used to group products into categories.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The Product id is unique and is used for identification in the application. It is created automatically with a new Product.
| creation_date | *DateTime* | This is the date and time the Product was created. It is created automatically with the new Product.
| created_by | *Integer* | This is the id of the admin who created the product.
| name | *String(64)* | This is the name of the product used to identify it in the frontend. It has to be unique.
| barcode | *String(32)* | This saves the data represented by the products barcode. This entry is optional, but it has to be unique.
| active | *Boolean* | This indicates whether the product is active (True) and therefor available in the frontend or not (False). If not specified further, it will automatically be set to True.
| countable | *Boolean* | This indicates whether the product is countable (True) like a chocolate bar or not countable (False) like coffee powder. If not specified further, it will automatically be set to True.
| revocable | *Boolean* | This indicates whether the product is revocable (True) or not (False). If not specified further, it will automatically be set to True.
| image_upload_id | *Integer* | This is the id of the Upload with the products picture. This entry is optional.

#### ProductPrice

After a product was created, an admin has to set the products price, which he
can always update. Therefor, a ProductPrice entry is made. The products price
can then be determined by checking the price field of the latest entry related
to the product. In Addition, a pricehistory can be determined by listing the
id, timestamp and price of all entries related to the product.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The ProductPrice id is unique and is used for identification in the application. It is created automatically with a new ProductPrice.
| timestamp | *DateTime* | This is the date and time the Product was created. It is created automatically with the new Product.
| product_id | *Integer* | This is the id of the product whose price was set/changed.
| admin_id | *Integer* | This is the id of the admin who made this change in the products price.
| price | *Integer* | This is what the product price was set to.

#### Tag

A Tag can be assigned to each product. They help to sort products into
categories in the frontend. All products with the same tag are listed in the
same category.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The Tag id is unique and is used for identification in the application. It is created automatically with a new Tag.
| created_by | *Integer* | This is the id of the admin who created the Tag.
| name | *String(24)* | This is the name of the Tag used to identify it in the frontend. It has to be unique.

#### product_tag_assignments

If a tag is added or removed from the product, a product_tag_assignments entry
is made or the corresponding entry is deleted. A product can have more than one
tag. The products tags can be determined by listing all tags from all entries
related to the product.

| Name | TYPE | Explanation
| --- | --- | --- |
| product_id | *Integer* | The id of the product the tag was assigned to.
| tag_id | *Integer* | The id of the tag that was assigned to the product.


#### Purchase

When a user buys a product, a Purchase entry is made. The user has to be
verified and the product has to be active. If the purchased product is
revocable, the purchase can be revoked, even more than once. So in addition, a
revokehistory for the purchase can be called. The price of the purchase is
calculated by multiplying the amount with the productprice. All prices of
purchases the user has made, which are not revoked, are added and withdrawn
from the users credit. Through adding the amounts a user has bought a specific
product, a list of the users favorite products can be created.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The Purchase id is unique and is used for identification in the application. It is created automatically with a new Purchase.
| timestamp | *DateTime* | This is the date and time the Product was created. It is created automatically with the new Product.
| user_id | *Integer* | This is the id of the user who made the purchase. The user has to be verified.
| product_id | *Integer* | This is the id of the product that has been purchased. The product has to be active
| productprice | *Integer* | This is the productprice when the purchase was made. It is determined automatically from the ProductPrice table when the purchase is created.
| amount | *Integer* | This describes the quantity in which the product was purchased. Even products which are not countable are sold in discreet amounts.
| revoked | *Boolean* | This indicates whether the Purchase is revoked (True) or not (False). If not specified further, it will automatically be set to False. The product has to be revocable.

#### PurchaseRevoke

If a purchase is revoked or re-revoked, a PurchaseRevoke entry is made. It is
used to determine the revokehistory of a purchase by listing the id, timestamp
and revoked field of each entry related to the purchase.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The PurchaseRevoke id is unique and is used for identification in the application. It is created automatically with a new PurchaseRevoke.
| timestamp | *DateTime* | This is the date and time the PurchaseRevoke was created. It is created automatically with the new PurchaseRevoke.
| purchase_id | *Integer* |This is the id of the purchase the revoke was changed for.
| revoked | *Boolean* | This indicates whether the Purchase is revoked (True) or not (False). The product has to be revocable.

#### ReplenishmentCollection

When an admin fills up the products by buying them at an external supplier with
the communities money, he creates a ReplenishmentCollection entry. A
replenishmentcollection can be revoked, even more than once. So in addition, a
revokehistory for the replenishmentcollection can be called. When creating, the
admin has to pass a list of all single replenishments the
replenishmentcollection consists of. The price of a replenishmentcollection is
the sum of the total_price of all related non-revoked replenishments. This
price can be used to give an overview of the communities finances.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The ReplenishmentCollection id is unique and is used for identification in the application. It is created automatically with a new ReplenishmentCollection.
| timestamp | *DateTime* | This is the date and time the ReplenishmentCollection was created. It is created automatically with the new ReplenishmentCollection.
| admin_id | *Integer* | This is the id of the admin who made the ReplenishmentCollection.
| revoked | *Boolean* | This indicates whether the ReplenishmentCollection is revoked (True) or not (False). If not specified further, it will automatically be set to False.
| comment | *String(64)* | This is a short comment where the admin explains what he bought and why.

#### ReplenishmentCollectionRevoke

If a replenishmentcollection is revoked or re-revoked by an admin, a
ReplenishmentCollectionRevoke entry is made. It is used to determine the
revokehistory of a replenishmentcollection by listing the id, timestamp and
revoked field of each entry related to the replenishmentcollection.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The ReplenishmentCollectionRevoke id is unique and is used for identification in the application. It is created automatically with a new ReplenishmentCollectionRevoke.
| timestamp | *DateTime* | This is the date and time the ReplenishmentCollectionRevoke was created. It is created automatically with the new ReplenishmentCollectionRevoke.
| admin_id | *Integer* | This is the id of the admin who changed the revoke status.
| replcoll_id | *Integer* | This is the id of the replenishmentcollection where the revoked status has been changed.
| revoked | *Boolean* | This indicates whether the ReplenishmentCollection is revoked (True) or not (False).

#### Replenishment

A replenishment is a fill up of a single product and always has to be part of a
replenishmentcollection. It can be revoked. If all replenishments of a
replenishmentcollection are revoked, the replenishmentcollection is revoked
automatically. In this case, the replenishmentcollection can only be rerevoked
by rerevoking a replenishment. When rerevoking the replenishmentcollection, the
replenishments stay revoked. If not revoked, the replenishments total_price is
added to the price of the related replenishmentcollection.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The Replenishment id is unique and is used for identification in the application. It is created automatically with a new Replenishment.
| replcoll_id | *Integer* | This is the id of the replenishmentcollection this replenishment belongs to.
| product_id | *Integer* | This is the id of the product which is being refilled with this replenishment.
| amount | *Integer* | This describes the quantity in which the product is refilled.
| total_price | *Integer* |This is the price paid by the admin to an external seller, such as a supermarket, for this replenishment.

#### Deposit

If a user transfers money to the community, an admin has to create a deposit
for him. A deposit can be revoked, even more than once. So in addition, a
revokehistory for the deposit can be called. The amounts of all deposits
related to the user, which are not revoked, are added to the users credit.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The Deposit id is unique and is used for identification in the application. It is created automatically with a new Deposit.
| timestamp | *DateTime* | This is the date and time the Deposit was created. It is created automatically with the new Deposit.
| user_id | *Integer* | This is the id of the user the deposit was made for.
| admin_id | *Integer* | This is the id of the admin who made the deposit.
| amount | *Integer* | This describes the amount (in cents) of the deposit. This is the money the user transferred to the community.
| comment | *String(64)* | This is a short comment where the admin explains what he did and why.
| revoked | *Boolean* | This indicates whether the Deposit is revoked (True) or not (False). If not specified further, it will automatically be set to False.

#### DepositRevoke

When an admin revokes or re-revokes a deposit, a DepositRevoke entry is made. It
is used to determine the revokehistory of a deposit by listing the id, timestamp
and revoked field of each entry related to the purchase.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The DepositRevoke id is unique and is used for identification in the application. It is created automatically with a new DepositRevoke.
| timestamp | *DateTime* | This is the date and time the DepositRevoke was created. It is created automatically with the new DepositRevoke.
| admin_id | *Integer* | This is the id of the admin who changed the revoke status.
| deposit_id | *Integer* | This is the id of the deposit where the revoked status has been changed.
| revoked | *Boolean* | This indicates whether the Deposit is revoked (True) or not (False).

#### Refunds

When a user buys things for the community with his own money, which can not
directly be linked to a product and no replenishment can be made, an admin has
to make a refund for him. An example would be cleaning agent. A refund
can be revoked, even more than once. So in addition, a revokehistory for the
refund can be called. The total_price of all refunds related to the user, which
are not revoked, are added to the users credit.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The Refund id is unique and is used for identification in the application. It is created automatically with a new Refund.
| timestamp | *DateTime* | This is the date and time the Refund was created. It is created automatically with the new Refund.
| user_id | *Integer* | This is the id of the user the Refund was made for.
| admin_id | *Integer* | This is the id of the admin who made the Refund.
| total_price | *Integer* | This describes the amount (in cents) of the refund.
| comment | *String(64)* | This is a short comment where the admin explains what he did and why.
| revoked | *Boolean* | This indicates whether the Refund is revoked (True) or not (False). If not specified further, it will automatically be set to False.

#### RefundRevoke

When an admin revokes or re-revokes a refund, a RefundRevoke entry is made. It
is used to determine the revokehistory of a refund by listing the id, timestamp
and revoked field of each entry related to the refund.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The RefundsRevoke id is unique and is used for identification in the application. It is created automatically with a new RefundsRevoke.
| timestamp | *DateTime* | This is the date and time the RefundsRevoke was created. It is created automatically with the new RefundsRevoke.
| admin_id | *Integer* | This is the id of the admin who changed the revoke status.
| refund_id | *Integer* | This is the id of the refund where the revoked status has been changed.
| revoked | *Boolean* | This indicates whether the Refund is revoked (True) or not (False).

#### Payoff

When an admin buys things for the community with the communities money and the
products can not directly be linked to a product like coffee beans, he has to
make a payoff. A payoff can be revoked, even more than once. So in addition, a
revokehistory for the payoff can be called. The total_price can be used to
give an overview of the communities finances.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The Payoff id is unique and is used for identification in the application. It is created automatically with a new Payoff.
| timestamp | *DateTime* | This is the date and time the Payoff was created. It is created automatically with the new Payoff.
| user_id | *Integer* | This is the id of the user the Payoff was made for.
| admin_id | *Integer* | This is the id of the admin who made the Payoff.
| total_price | *Integer* | This describes the amount (in cents) of the Payoff.
| comment | *String(64)* | This is a short comment where the admin explains what he did and why.
| revoked | *Boolean* | This indicates whether the Payoff is revoked (True) or not (False). If not specified further, it will automatically be set to False.

#### PayoffRevoke

When an admin revokes or re-revokes a payoff, a PayoffRevoke entry is made. It
is used to determine the revokehistory of a deposit by listing the id, timestamp
and revoked field of each entry related to the payoff.

| Name | TYPE | Explanation
| --- | --- | --- |
| id | *Integer* | The PayoffRevoke id is unique and is used for identification in the application. It is created automatically with a new PayoffRevoke.
| timestamp | *DateTime* | This is the date and time the PayoffRevoke was created. It is created automatically with the new PayoffRevoke.
| admin_id | *Integer* | This is the id of the admin who changed the revoke status.
| refund_id | *Integer* | This is the id of the refund where the revoked status has been changed.
| revoked | *Boolean* | This indicates whether the PayoffRevoke is revoked (True) or not (False).
