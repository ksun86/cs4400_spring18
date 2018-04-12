from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, SelectField, BooleanField, IntegerField, SelectMultipleField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import enum

app = Flask(__name__)


app.config['MYSQL_HOST'] = 'academic-mysql.cc.gatech.edu'
app.config['MYSQL_USER'] = 'cs4400_team_73'
app.config['MYSQL_PASSWORD'] = '9pRZGQZH'
app.config['MYSQL_DB'] = 'cs4400_team_73'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

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

################################################################################

# Register Form Class
class VisitorRegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.Length(min=8, max=50),
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

################################################################################
# User Register
@app.route('/VisitorRegister', methods=['GET', 'POST'])
def VisitorRegister():
    form = VisitorRegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(username, email, password, usertype) VALUES(%s, %s, %s, %s)", (username, email, password, 'VISITOR'))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('visitorfunctionality'))
    return render_template('VisitorRegister.html', form=form)

################################################################################


# Register Form Class
class OwnerRegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.Length(min=8, max=50),
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

    propertyname = StringField('Property Name', [validators.Length(min=1, max=100)])
    streetaddress = StringField('Address', [validators.Length(min=1, max=50)])
    city = StringField('City', [validators.Length(min=1, max=50)])
    zipcode = IntegerField('Zip Code', [validators.NumberRange(min=10000, max=99999)])
    size = IntegerField('Size (in acres)', [validators.NumberRange(min=1, max=10000)])
    propertytype = SelectField('Property Type',
        [validators.NoneOf('', message='Please select a property type')],
        choices=[('', ''), ('FARM', 'Farm'), ('GARDEN', 'Garden'), ('ORCHARD', 'Orchard')] # (value passed to db, value shown to user)
    )

    animals = SelectMultipleField('Which animals will your property have (Hold CTRL and click to select multiple)', choices=[('dog','dog')])
    crops = SelectMultipleField('Which crops will your property have (Hold CTRL and click to select multiple)', choices=[('apple','apple')])
    public = BooleanField('If your property is public, check the box below:')
    commercial = BooleanField('If your property is commercial, check the box below:')

################################################################################
# User Register
@app.route('/OwnerRegister', methods=['GET', 'POST'])
def OwnerRegister():
    form = OwnerRegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        # Create cursor
        cur = mysql.connection.cursor()

        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        propertyname = form.propertyname.data
        streetaddress = form.propertytype.data
        city = form.city.data
        zipcode = form.zipcode.data
        size = form.size.data
        propertytype = form.propertytype.data

        # achoices = ['dog','cat','zebra']
        # cchoices = ['apple','orange','banana']
        # form.animals.choices = [(animal,animal) for animal in achoices]
        # form.crops.choices = [(crop,crop) for crop in cchoices]
        animals = form.animals.data
        crops = form.crops.data
        public = form.public.data
        commercial = form.commercial.data


        # Execute query
        cur.execute("INSERT INTO users(username, email, password, usertype) VALUES(%s, %s, %s, %s)",
         (username, email, password, 'OWNER'))
# property property(id, name, size, IsCommercial, IsPublic, street, city, zip, propertytype, owner, approvedby)
        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('ownerfunctionality'))
    return render_template('OwnerRegister.html', form=form)

#################################################################################


@app.route('/ownerfunctionality')
def ownerfunctionality():
    return render_template('ownerfunctionality.html')

@app.route('/adminfunctionality')
def adminfunctionality():
    return render_template('adminfunctionality.html')

@app.route('/visitorfunctionality')
def visitorfunctionality():
    return render_template('visitorfunctionality.html')

################################################################################

@app.route('/manageproperty')
def manageproperty():
    return render_template('manageproperty.html')

@app.route('/addproperty')
def addproperty():
    return render_template('addproperty.html')

################################################################################

@app.route('/otherownersproperties')
def otherownersproperties():
    return render_template('otherownersproperties.html')

@app.route('/visitoroverview')
def visitoroverview():
    return render_template('visitoroverview.html')

@app.route('/owneroverview')
def owneroverview():
    return render_template('owneroverview.html')

################################################################################

@app.route('/confirmedproperties')
def confirmedproperties():
    return render_template('confirmedproperties.html')

@app.route('/unconfirmedproperties')
def unconfirmedproperties():
    return render_template('unconfirmedproperties.html')

################################################################################

@app.route('/approvedcrops')
def approvedcrops():
    return render_template('approvedcrops.html')

@app.route('/pendingcrops')
def pendingcrops():
    return render_template('pendingcrops.html')

################################################################################

@app.route('/propertydetails')
def propertydetails():
    return render_template('propertydetails.html')

@app.route('/visitorhistory')
def visitorhistory():
    return render_template('visitorhistory.html')

################################################################################

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)