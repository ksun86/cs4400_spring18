from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

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

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
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
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('VisitorRegister.html', form=form)

#################################################################################


# Register Form Class
class OwnerRegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])

    confirm = PasswordField('Confirm Password')
    propertytype = StringField('Property Type', [validators.Length(min=1, max=50)])

################################################################################
# User Register
@app.route('/OwnerRegister', methods=['GET', 'POST'])
def OwnerRegister():
    form = OwnerRegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        propertytype = form.propertytype.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password, propertytype) VALUES(%s, %s, %s, %s, %s)",
         (name, email, username, password, propertytype))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('OwnerRegister.html', form=form)

#################################################################################

@app.route('/ownerregistration')
def ownerregistration():
    return render_template('ownerregistration.html')

@app.route('/visitorregistration')
def visitorregistration():
    return render_template('visitorregistration.html')

################################################################################

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