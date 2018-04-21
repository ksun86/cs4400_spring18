from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, SelectField, BooleanField, IntegerField, SelectMultipleField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import enum

app = Flask(__name__)

# mysql -u cs4400_team_73 -p
app.config['MYSQL_HOST'] = 'academic-mysql.cc.gatech.edu'
app.config['MYSQL_USER'] = 'cs4400_team_73'
app.config['MYSQL_PASSWORD'] = '9pRZGQZH'
app.config['MYSQL_DB'] = 'cs4400_team_73'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

propertyID = 0

################################################################################

@app.route('/', methods=['GET', 'POST'])
def Login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        passwordCandidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM User WHERE Username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['Password']
            userType = data['UserType']

            # Compare Passwords
            print(type(password))
            print(type(passwordCandidate))
            if sha256_crypt.verify(passwordCandidate, password):
                # Passed
                session['loggedIn'] = True
                session['username'] = username
                session['userType'] = userType

                flash('You are now logged in', 'success')
                if userType == "OWNER" :
                    return redirect(url_for('OwnerFunctionality'))
                if userType == "VISITOR" :
                    return redirect(url_for('VisitorFunctionality'))
                if userType == "ADMIN" :
                    return redirect(url_for('AdminFunctionality'))
            else:
                error = 'Invalid password'

                return render_template('Login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'

            return render_template('Login.html', error=error)
    return render_template('Login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'loggedIn' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('Login'))
    return wrap

@app.route('/Logout')
@is_logged_in
def Logout():
    session.clear()
    return redirect(url_for('Login'))

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
@app.route('/UserRegistration/<string:userType>', methods=['GET', 'POST'])
def Register(userType):
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO User(Username, Email, Password, UserType) VALUES(%s, %s, %s, %s)",
            (username, email, password, userType))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        session['loggedIn'] = True
        session['username'] = username
        session['userType'] = userType

        if userType == 'VISITOR':
            return redirect(url_for('VisitorFunctionality'))
        elif userType == 'OWNER':
            return redirect(url_for('AddProperty'))
    return render_template('UserRegistration.html', form=form)

################################################################################
# Add Property Form Class
class AddPropertyForm(Form):
    propertyName = StringField('Property Name', [validators.Length(min=1, max=100)])
    address = StringField('Address', [validators.Length(min=1, max=50)])
    city = StringField('City', [validators.Length(min=1, max=50)])
    zipCode = IntegerField('Zip Code', [validators.NumberRange(min=10000, max=99999)])
    size = IntegerField('Size (in acres)', [validators.NumberRange(min=1, max=10000)])
    propertyType = SelectField('Property Type',
        [validators.NoneOf('', message='Please select a property type')],
        choices=[('', ''), ('FARM', 'Farm'), ('GARDEN', 'Garden'), ('ORCHARD', 'Orchard')] # (value passed to db, value shown to user)
    )
    isPublic = BooleanField('If your property is public, check the box below:')
    isCommercial = BooleanField('If your property is commercial, check the box below:')

################################################################################
# Add Property
@app.route('/AddProperty', methods=['GET', 'POST'])
@is_logged_in
def AddProperty():
    form = AddPropertyForm(request.form)
    if request.method == 'POST' and form.validate():

        propertyName = form.propertyName.data
        address = form.address.data
        city = form.city.data
        zipCode = form.zipCode.data
        size = form.size.data
        propertyType = form.propertyType.data
        isPublic = form.isPublic.data
        isCommercial = form.isCommercial.data

        session['propertyType'] = propertyType
        global propertyID
        propertyID += 1
        session['propertyID'] = propertyID

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO Property(ID, Name, Size, IsCommercial, IsPublic, Street, City, Zip, PropertyType, Owner) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (propertyID, propertyName, size, isCommercial, isPublic, address, city, zipCode, propertyType, session['username']))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        return redirect(url_for('AddItems'))
    return render_template('AddProperty.html', form=form)

#################################################################################
# Add Items Form Class
class AddItemsForm(Form):
    crops = SelectMultipleField('Crops (Hold CTRL and click to select multiple)', choices=[('','')])
    animals = SelectMultipleField('Animals (Hold CTRL and click to select multiple)', choices=[('','')])

#################################################################################
# User Registration
@app.route('/AddItems', methods=['GET', 'POST'])
@is_logged_in
def AddItems():
    # Create cursor
    cur = mysql.connection.cursor()

    # Create cursor
    cur = mysql.connection.cursor()

    cur.execute("SELECT Name, Type FROM FarmItem WHERE IsApproved")

    data = cur.fetchall()
    form = AddItemsForm(request.form)
    animalChoices = []
    orchardChoices = []
    gardenChoices = []
    for tup in data:
        if tup['type'] == 'ANIMAL':
            animalChoices.append(tup['name'])
        elif tup['type'] == 'FRUIT' or tup['type'] == 'NUT':
            orchardChoices.append(tup['name'])
        elif tup['type'] == 'VEGETABLE' or tup['type'] == 'FLOWER':
            gardenChoices.append(tup['name'])

    if session['propertyType'] == 'FARM':
        form.animals.choices = [(animal,animal) for animal in animalChoices]
        form.crops.choices = [(crop,crop) for crop in gardenChoices + orchardChoices]
    elif session['propertyType'] == 'GARDEN':
        form.crops.choices = [(crop,crop) for crop in gardenChoices]
    elif session['propertyType'] == 'ORCHARD':
        form.crops.choices = [(crop,crop) for crop in orchardChoices]

    if request.method == 'POST' and form.validate():
        items = form.animals.data + form.crops.data

        # Execute query
        for item in items:
            cur.execute("INSERT INTO Has(PropertyID, ItemName) VALUES(%s, %s)",
                (session['propertyID'], item))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        return redirect(url_for('OwnerFunctionality'))
    return render_template('AddItems.html', form=form)
#################################################################################

@app.route('/OwnerFunctionality')
@is_logged_in
def OwnerFunctionality():
    return render_template('OwnerFunctionality.html')

@app.route('/AdminFunctionality')
@is_logged_in
def AdminFunctionality():
    return render_template('AdminFunctionality.html')

#################################################################################




#################################################################################

@app.route('/VisitorFunctionality')
@is_logged_in
def VisitorFunctionality():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM Property WHERE NOT ApprovedBy = null") # approved by must have some value

    properties = cur.fetchall()

    # Close connection
    cur.close()

    return render_template('VisitorFunctionality.html', properties=properties)

################################################################################

@app.route('/ManageProperty')
@is_logged_in
def ManageProperty():
    return render_template('ManageProperty.html')

################################################################################

@app.route('/DeleteProperty/<string:ID>', methods=['POST'])
@is_logged_in
def DeleteProperty(ID):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM Property WHERE ID = %s", [ID])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    if session['UserType'] == 'ADMIN':
        return redirect(url_for('AdminFunctionality'))
    elif session['UserType'] == 'OWNER':
        return redirect(url_for('OwnerFunctionality'))

################################################################################

@app.route('/OtherOwnersProperties')
@is_logged_in
def OtherOwnersProperties():
    return render_template('OtherOwnersProperties.html')

@app.route('/VisitorOverview')
@is_logged_in
def VisitorOverview():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT Visit.Username, Email, COUNT(*) as LogVisits FROM User join Visit on User.Username = Visit.Username GROUP BY Username") 

    visitors = cur.fetchall()

    # Close connection
    cur.close()

    return render_template('VisitorOverview.html', visitors=visitors)

@app.route('/DeleteVisitorAccount/<string:username>', methods=['POST'])
def DeleteVisitorAccount(username):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM User WHERE Username = %s", [username])
    cur.execute("DELETE FROM Visit WHERE Username = %s", [username])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return redirect(url_for('VisitorOverview'))

@app.route('/DeleteLogHistory/<string:username>', methods=['POST'])
def DeleteLogHistory(username):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM Visit WHERE Username = %s", [username])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return redirect(url_for('VisitorOverview'))

# @app.route('/SearchByEmail/<string:email>', methods=['POST'])
# def SearchByEmail(username):
#     # Create cursor
#     cur = mysql.connection.cursor()

#     # Execute
#     cur.execute("DELETE FROM Visit WHERE Username = %s", [username])

#     # Commit to DB
#     mysql.connection.commit()

#     #Close connection
#     cur.close()

#     return redirect(url_for('VisitorOverview'))




@app.route('/OwnerOverview')
@is_logged_in
def OwnerOverview():
    return render_template('OwnerOverview.html')

################################################################################

@app.route('/ConfirmedProperties')
@is_logged_in
def ConfirmedProperties():
    return render_template('ConfirmedProperties.html')

@app.route('/UnconfirmedProperties')
@is_logged_in
def UnconfirmedProperties():
    return render_template('UnconfirmedProperties.html')

################################################################################

@app.route('/ApprovedItems')
@is_logged_in
def ApprovedItems():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM FarmItem WHERE IsApproved")

    items = cur.fetchall()

    # Close connection
    cur.close()

    return render_template('ApprovedItems.html', items=items)

@app.route('/PendingItems')
@is_logged_in
def PendingItems():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM FarmItem WHERE NOT IsApproved")

    items = cur.fetchall()

    # Close connection
    cur.close()

    return render_template('PendingItems.html', items=items)

@app.route('/AddItem', methods=['POST'])
def AddItem():
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM FarmItem WHERE Name = %s", [name])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return redirect(url_for('ApprovedItems'))

@app.route('/DeleteItem/<string:name>', methods=['POST'])
def DeleteItem(name):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM FarmItem WHERE Name = %s", [name])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return redirect(url_for('ApprovedItems'))

@app.route('/ApproveItem/<string:name>', methods=['POST'])
def ApproveItem(name):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM FarmItem WHERE Name = %s", [name])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return redirect(url_for('PendingItems'))

################################################################################

@app.route('/PropertyDetails/<string:ID>/')
@is_logged_in
def PropertyDetails(ID):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    result = cur.execute("SELECT * FROM Property WHERE ID = %s", [ID])

    prop = cur.fetchone()

    return render_template('PropertyDetails.html', property=prop)

@app.route('/VisitorHistory')
@is_logged_in
def VisitorHistory():
    return render_template('VisitorHistory.html')

################################################################################

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)