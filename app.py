from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, SelectField, BooleanField, IntegerField, SelectMultipleField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import enum

app = Flask(__name__)


app.config['MYSQL_HOST'] = 'academic-mysql.cc.gatech.edu'
# mysql -u cs4400_team_73 -p
app.config['MYSQL_USER'] = 'cs4400_team_73'
app.config['MYSQL_PASSWORD'] = '9pRZGQZH'
app.config['MYSQL_DB'] = 'cs4400_team_73'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

propertyid = 0

@app.route('/test')
def test():
    return render_template('AddNewProperty.html')
################################################################################

# class USERTYPE(enum.Enum):
#     visitor = "VISITOR"
#     owner = "OWNER"
#     admin = "ADMIN"

# ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f

################################################################################

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']
            usertype = data['usertype']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username
                session['usertype'] = usertype

                flash('You are now logged in', 'success')
                if usertype == "OWNER" :
                    return redirect(url_for('ownerfunctionality'))
                if usertype == "VISITOR" :
                    return redirect(url_for('visitorfunctionality'))
                if usertype == "ADMIN" :
                    return redirect(url_for('adminfunctionality'))
            else:
                error = 'Invalid password'

                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'

            return render_template('login.html', error=error)

    return render_template('login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    return redirect(url_for('login'))

################################################################################
# User Registration Form Class
class RegisterForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.Length(min=8, max=50),
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

################################################################################
# User Registration
@app.route('/registration/<string:utype>', methods=['GET', 'POST'])
def Register(utype):
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(username, email, password, usertype) VALUES(%s, %s, %s, %s)",
            (username, email, password, utype.upper()))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        session['logged_in'] = True
        session['username'] = username

        if utype == 'visitor':
            return redirect(url_for('visitorfunctionality'))
        elif utype == 'owner':
            return redirect(url_for('addproperty'))
    return render_template('registration.html', form=form)

################################################################################
# Add Property Form Class
class AddPropertyForm(Form):
    propertyname = StringField('Property Name', [validators.Length(min=1, max=100)])
    streetaddress = StringField('Address', [validators.Length(min=1, max=50)])
    city = StringField('City', [validators.Length(min=1, max=50)])
    zipcode = IntegerField('Zip Code', [validators.NumberRange(min=10000, max=99999)])
    size = IntegerField('Size (in acres)', [validators.NumberRange(min=1, max=10000)])
    propertytype = SelectField('Property Type',
        [validators.NoneOf('', message='Please select a property type')],
        choices=[('', ''), ('FARM', 'Farm'), ('GARDEN', 'Garden'), ('ORCHARD', 'Orchard')] # (value passed to db, value shown to user)
    )
    public = BooleanField('If your property is public, check the box below:')
    commercial = BooleanField('If your property is commercial, check the box below:')

################################################################################
# Add Property
@app.route('/addproperty', methods=['GET', 'POST'])
@is_logged_in
def addproperty():
    form = AddPropertyForm(request.form)
    if request.method == 'POST' and form.validate():

        propertyname = form.propertyname.data
        streetaddress = form.propertytype.data
        city = form.city.data
        zipcode = form.zipcode.data
        size = form.size.data
        propertytype = form.propertytype.data
        public = form.public.data
        commercial = form.commercial.data

        session['propertytype'] = propertytype
        global propertyid
        propertyid += 1
        session['propertyid'] = propertyid

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO property(id, name, size, IsCommercial, IsPublic, street, city, zip, propertytype, owner) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (propertyid, propertyname, size, commercial, public, streetaddress, city, zipcode, propertytype, session['username']))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        return redirect(url_for('additems'))
    return render_template('addproperty.html', form=form)

#################################################################################
# Add Items Form Class
class AddItemsForm(Form):
    crops = SelectMultipleField('Crops (Hold CTRL and click to select multiple)', choices=[('','')])
    animals = SelectMultipleField('Animals (Hold CTRL and click to select multiple)', choices=[('','')])

#################################################################################
# User Registration
@app.route('/additems', methods=['GET', 'POST'])
@is_logged_in
def additems():
    # Create cursor
    cur = mysql.connection.cursor()

    # Create cursor
    cur = mysql.connection.cursor()

    cur.execute("SELECT name, type FROM farmitem WHERE IsApproved")

    data = cur.fetchall()
    form = AddItemsForm(request.form)
    animalchoices = []
    orchardchoices = []
    gardenchoices = []
    for tup in data:
        if tup['type'] == 'ANIMAL':
            animalchoices.append(tup['name'])
        elif tup['type'] == 'FRUIT':
            orchardchoices.append(tup['name'])
        elif tup['type'] == 'NUT':
            orchardchoices.append(tup['name'])
        elif tup['type'] == 'VEGETABLE':
            gardenchoices.append(tup['name'])
        elif tup['type'] == 'FLOWER':
            gardenchoices.append(tup['name'])

    if session['propertytype'] == 'FARM':
        form.animals.choices = [(animal,animal) for animal in animalchoices]
        form.crops.choices = [(crop,crop) for crop in gardenchoices + orchardchoices]
    elif session['propertytype'] == 'GARDEN':
        form.crops.choices = [(crop,crop) for crop in gardenchoices]
    elif session['propertytype'] == 'ORCHARD':
        form.crops.choices = [(crop,crop) for crop in orchardchoices]

    if request.method == 'POST' and form.validate():
        items = form.animals.data + form.crops.data

        # Execute query
        for item in items:
            cur.execute("INSERT INTO has(propertyid, itemname) VALUES(%s, %s)",
                (session['propertyid'], item))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        return redirect(url_for('ownerfunctionality'))
    return render_template('additems.html', form=form)
#################################################################################

@app.route('/ownerfunctionality')
@is_logged_in
def ownerfunctionality():
    return render_template('ownerfunctionality.html')

@app.route('/adminfunctionality')
@is_logged_in
def adminfunctionality():
    return render_template('adminfunctionality.html')

@app.route('/visitorfunctionality')
@is_logged_in
def visitorfunctionality():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM property WHERE NOT approvedby = null") # approved by must have some value

    properties = cur.fetchall()

    return render_template('visitorfunctionality.html', properties=properties)

    # Close connection
    cur.close()

################################################################################

@app.route('/manageproperty')
@is_logged_in
def manageproperty():
    return render_template('manageproperty.html')

################################################################################

@app.route('/otherownersproperties')
@is_logged_in
def otherownersproperties():
    return render_template('otherownersproperties.html')

@app.route('/visitoroverview')
@is_logged_in
def visitoroverview():
    return render_template('visitoroverview.html')

@app.route('/owneroverview')
@is_logged_in
def owneroverview():
    return render_template('owneroverview.html')

################################################################################

@app.route('/confirmedproperties')
@is_logged_in
def confirmedproperties():
    return render_template('confirmedproperties.html')

@app.route('/unconfirmedproperties')
@is_logged_in
def unconfirmedproperties():
    return render_template('unconfirmedproperties.html')

################################################################################

@app.route('/approvedcrops')
@is_logged_in
def approvedcrops():
    return render_template('approvedcrops.html')

@app.route('/pendingcrops')
@is_logged_in
def pendingcrops():
    return render_template('pendingcrops.html')

################################################################################

@app.route('/propertydetails')
@is_logged_in
def propertydetails():
    return render_template('propertydetails.html')

@app.route('/visitorhistory')
@is_logged_in
def visitorhistory():
    return render_template('visitorhistory.html')

################################################################################

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)