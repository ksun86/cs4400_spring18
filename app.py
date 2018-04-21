from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, SelectField, BooleanField, IntegerField, FloatField, SelectMultipleField, validators
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

propertyID = 54132

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
    username = StringField('Username', [validators.Length(min=3, max=25)])
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
    street = StringField('Street', [validators.Length(min=1, max=50)])
    city = StringField('City', [validators.Length(min=1, max=50)])
    zipCode = IntegerField('Zip Code', [validators.NumberRange(min=10000, max=99999)])
    size = FloatField('Size (in acres)', [validators.NumberRange(min=0.000001, max=10000)])
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
        street = form.street.data
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
        if tup['Type'] == 'ANIMAL':
            animalChoices.append(tup['Name'])
        elif tup['Type'] == 'FRUIT' or tup['Type'] == 'NUT':
            orchardChoices.append(tup['Name'])
        elif tup['Type'] == 'VEGETABLE' or tup['Type'] == 'FLOWER':
            gardenChoices.append(tup['Name'])

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
    # Create cursor
    cur = mysql.connection.cursor()

    # Get properties
    result = cur.execute("""SELECT Name, Street, City, Zip, Size, PropertyType, IsPublic, IsCommercial, ID, ApprovedBy, AVG(Rating) AS AverageRating, COUNT(Rating) AS NumVisits
                            FROM Property LEFT JOIN Visit ON ID = PropertyID
                            WHERE Owner = %s
                            GROUP BY ID
                            ORDER BY Name""", [session['username']])
    properties = cur.fetchall()

    # Close connection
    cur.close()

    return render_template('OwnerFunctionality.html', properties=properties)

#################################################################################


@app.route('/VisitorFunctionality')
@is_logged_in
def VisitorFunctionality():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get properties
    result = cur.execute("""SELECT Name, Street, City, Zip, Size, PropertyType, IsPublic, IsCommercial, ID, AVG(Rating) AS AverageRating, COUNT(Rating) AS NumVisits
                            FROM Property LEFT JOIN Visit ON ID = PropertyID
                            WHERE ApprovedBy IS NOT NULL AND IsPublic
                            GROUP BY ID
                            ORDER BY Name""")
    properties = cur.fetchall()

    # Close connection
    cur.close()

    return render_template('VisitorFunctionality.html', properties=properties)

@app.route('/OtherOwnersProperties')
@is_logged_in
def OtherOwnersProperties():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get properties
    result = cur.execute("""SELECT Name, Street, City, Zip, Size, PropertyType, IsPublic, IsCommercial, ID, AVG(Rating) AS AverageRating, COUNT(Rating) AS NumVisits
                            FROM Property LEFT JOIN Visit ON ID = PropertyID
                            WHERE ApprovedBy IS NOT NULL AND IsPublic AND NOT Owner = %s
                            GROUP BY ID
                            ORDER BY Name""", [session['username']])

    properties = cur.fetchall()

    # Close connection
    cur.close()

    return render_template('OtherOwnersProperties.html', properties=properties)

################################################################################

@app.route('/AdminFunctionality')
@is_logged_in
def AdminFunctionality():
    return render_template('AdminFunctionality.html')

@app.route('/ManageProperty/<string:ID>/<string:manageType>', methods=['GET','POST'])
@is_logged_in
def ManageProperty(ID, manageType):
    # Create cursor
    cur = mysql.connection.cursor()



    # Get property
    result = cur.execute("SELECT * FROM Property WHERE ID = %s", [ID])

    prop = cur.fetchone()

    cur.close()

    # Get form
    form = AddPropertyForm(request.form)

    # Populate property form fields
    form.propertyName.data = prop['Name']
    form.street.data = prop['Street']
    form.city.data = prop['City']
    form.zipCode.data = prop['Zip']
    form.size.data = prop['Size']
    form.propertyType.data = prop['PropertyType']
    form.isPublic.data = prop['IsPublic']
    form.isCommercial.data = prop['IsCommercial']
    session['propertyID'] = ID
    session['propertyType'] = prop['PropertyType']
    session['propertyName'] = prop['Name']

    if request.method == 'POST' and form.validate():
        propertyName = request.form['propertyName']
        street = request.form['street']
        city = request.form['city']
        zipCode = request.form['zipCode']
        size = request.form['size']
        try:
            request.form['isPublic']
            isPublic = True
        except:
            isPublic = False
        try:
            request.form['isCommercial']
            isCommercial = True
        except:
            isCommercial = False


        # Create Cursor
        cur = mysql.connection.cursor()


        if session['userType'] == 'OWNER':
            # Execute
            cur.execute ("""UPDATE Property SET Name=%s, Street=%s, City=%s, Zip=%s, Size=%s, IsPublic=%s, IsCommercial=%s, ApprovedBy=NULL
                            WHERE ID=%s""",(propertyName, street, city, zipCode, size, isPublic, isCommercial, ID))
        elif session['userType'] == 'ADMIN':
            # Execute
            cur.execute ("""UPDATE Property SET Name=%s, Street=%s, City=%s, Zip=%s, Size=%s, IsPublic=%s, IsCommercial=%s, ApprovedBy=%s
                            WHERE ID=%s""",(propertyName, street, city, zipCode, size, isPublic, isCommercial, session['username'], ID))

        cur.execute("""DELETE FROM Visit WHERE PropertyID=%s""",[ID])
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        return redirect(url_for('ManageProperty', ID=ID, manageType=manageType))

    return render_template('ManageProperty.html', form=form, property=prop)

@app.route('/ManageItems', methods=['GET', 'POST'])
@is_logged_in
def ManageItems():
    # Create cursor
    cur = mysql.connection.cursor()

    result = cur.execute("""SELECT ItemName FROM Has WHERE PropertyID = %s""", [session['propertyID']])
    items = cur.fetchall()

    result = cur.execute("SELECT Name, Type FROM FarmItem WHERE IsApproved AND Name NOT IN (SELECT ItemName FROM Has WHERE PropertyID = %s)", [session['propertyID']])
    allAvailable = cur.fetchall()

    animalChoices = []
    orchardChoices = []
    gardenChoices = []
    for tup in allAvailable:
        if tup['Type'] == 'ANIMAL':
            animalChoices.append(tup['Name'])
        elif tup['Type'] == 'FRUIT' or tup['Type'] == 'NUT':
            orchardChoices.append(tup['Name'])
        elif tup['Type'] == 'VEGETABLE' or tup['Type'] == 'FLOWER':
            gardenChoices.append(tup['Name'])

    if session['propertyType'] == 'FARM':
        available = [item for item in animalChoices + gardenChoices + orchardChoices]
    elif session['propertyType'] == 'GARDEN':
        available = [item for item in gardenChoices]
    elif session['propertyType'] == 'ORCHARD':
        available = [item for item in orchardChoices]

    cur.close()

    return render_template('ManageItems.html', items=items, available=available)

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

@app.route('/RemoveItem/<string:name>', methods=['POST'])
@is_logged_in
def RemoveItem(name):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM Has WHERE PropertyID = %s AND ItemName=%s", [session['propertyID'], name])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return redirect(url_for('ManageItems'))

@app.route('/AddItemProp', methods=['POST'])
@is_logged_in
def AddItemProp():
    item = request.form['item']
    if item == "":
        return redirect(url_for('ManageItems'))

    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("INSERT INTO Has(PropertyID, ItemName) VALUES(%s, %s)", [session['propertyID'], item])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return redirect(url_for('ManageItems'))

################################################################################

@app.route('/VisitorOverview')
@is_logged_in
def VisitorOverview():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
<<<<<<< HEAD
    result = cur.execute("SELECT Visit.Username, Email, COUNT(Rating) as NumVisits FROM User join Visit on User.Username = Visit.Username GROUP BY Username") 
=======
    result = cur.execute("SELECT Visit.Username, Email, COUNT(*) as NumVisits FROM User join Visit on User.Username = Visit.Username GROUP BY Username")
>>>>>>> ca9ef6dada7f1a101ac5f8d6908a06f708ddc27c

    visitors = cur.fetchall()

    # Close connection
    cur.close()

    return render_template('VisitorOverview.html', users=visitors)

@app.route('/DeleteVisitorAccount/<string:username>', methods=['POST'])
@is_logged_in
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
@is_logged_in
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

@app.route('/SearchUsers', methods=['POST'])
@is_logged_in
def SearchUsers():
    column = request.form['column']
    searchterm = request.form['searchterm']
    searchType = request.form['searchType']
    if searchterm == '' or column == '':
        return redirect(url_for(searchType))

    range = False
    if column in ['NumVisits', 'AverageRating']:
        if "-" in searchterm:
            range = True
            numvallist = searchterm.split("-")
            lower = float(numvallist[0])
            upper = float(numvallist[1])

    cur = mysql.connection.cursor()

    if searchType == "VisitorOverview":
        if range:
            result = cur.execute("""SELECT User.Username AS Username,  Email, COUNT(*) AS NumVisits
                                    FROM Visit JOIN User ON User.Username = Visit.Username
                                    WHERE UserType = 'VISITOR'
                                    GROUP BY Visit.Username
                                    HAVING {} BETWEEN {} AND {}
                                    """.format(column, lower, upper))
        else:
            result = cur.execute("""SELECT User.Username AS Username,  Email, COUNT(*) AS NumVisits
                                    FROM Visit JOIN User ON User.Username = Visit.Username
                                    WHERE UserType = 'VISITOR' AND User.{} = %s
                                    GROUP BY Visit.Username
                                    """.format(column), [searchterm])
    elif searchType == "OwnerOverview":
        if range:
            result = cur.execute("""SELECT User.Username AS Username,  Email, COUNT(*) AS NumProp
                                    FROM Property JOIN User ON User.Username = Property.Owner
                                    WHERE UserType = 'OWNER'
                                    GROUP BY Property.Owner
                                    HAVING {} BETWEEN {} AND {}
                                    ORDER BY Name""".format(column, lower, upper))
        else:
            result = cur.execute("""SELECT User.Username AS Username,  Email, COUNT(*) AS NumProp
                                FROM Property JOIN User ON User.Username = Property.Owner
                                WHERE UserType = 'OWNER' AND User.{} = %s
                                GROUP BY Property.Owner
                                """.format(column), [searchterm])


    users = cur.fetchall()

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return render_template('{}.html'.format(searchType), users=users)

@app.route('/OwnerOverview')
@is_logged_in
def OwnerOverview():
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT User.Username, Email, COUNT(*) as NumProp FROM User join Property on User.Username = Property.Owner GROUP BY Username")

    owners = cur.fetchall()

    # Close connection
    cur.close()

    return render_template('OwnerOverview.html', users=owners)

@app.route('/DeleteOwnerAccount/<string:username>', methods=['POST'])
@is_logged_in
def DeleteOwnerAccount(username):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM User WHERE Username = %s", [username])
    cur.execute("DELETE FROM Property WHERE Owner = %s", [username])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return redirect(url_for('OwnerOverview'))

################################################################################


@app.route('/SortBy/', methods=['POST'])
@is_logged_in
def SortBy():
    column = request.form['column']
    sortType = request.form['sortType']
    print(sortType)
    if column == '':
        return redirect(url_for(sortType))

    # Create cursor
    cur = mysql.connection.cursor()
    if sortType == "OwnerOverview":
        result = cur.execute("""SELECT User.Username, Email, COUNT(*) as NumProp
                            FROM User JOIN Property ON User.Username = Property.Owner
                            WHERE UserType = 'OWNER'
                            GROUP BY Property.Owner
                            ORDER BY {}""".format(column))
    elif sortType == "VisitorOverview":
        result = cur.execute("""SELECT User.Username, Email, COUNT(*) as NumVisits
                            FROM Visit JOIN User ON User.Username = Visit.Username
                            WHERE UserType = 'VISITOR'
                            GROUP BY Visit.Username
                            ORDER BY {}""".format(column))

    elif sortType == "ConfirmedProperties":
        result = cur.execute("""SELECT Name, Street, City, Zip, Size, PropertyType, IsPublic, IsCommercial, ID, ApprovedBy, AVG(Rating) AS AverageRating
                            FROM Property LEFT JOIN Visit ON ID = PropertyID
                            WHERE ApprovedBy IS NOT NULL
                            GROUP BY ID
                            ORDER BY {}""".format(column))
        properties = cur.fetchall()
        cur.close()

        return render_template('{}.html'.format(sortType), properties = properties)

    elif sortType == "UnconfirmedProperties":
        result = cur.execute("""SELECT *
                            FROM Property
                            WHERE ApprovedBy IS NOT NULL
                            GROUP BY ID
                            ORDER BY {}""".format(column))
        properties = cur.fetchall()
        cur.close()

        return render_template('{}.html'.format(sortType), properties = properties)

    elif sortType == "ApprovedItems":
        result = cur.execute("""SELECT *
                            FROM FarmItem
                            WHERE IsApproved
                            ORDER BY {}""".format(column))
        items = cur.fetchall()
        cur.close()

        return render_template('{}.html'.format(sortType), items = items)

    elif sortType == "PendingItems":
        result = cur.execute("""SELECT *
                            FROM FarmItem
                            WHERE NOT IsApproved
                            ORDER BY {}""".format(column))
        items = cur.fetchall()
        cur.close()

        return render_template('{}.html'.format(sortType), items = items)

    elif sortType == "OwnerFunctionality":
        result = cur.execute("""SELECT Name, Street, City, Zip, Size, PropertyType, IsPublic, IsCommercial, ID, ApprovedBy, AVG(Rating) AS AverageRating, COUNT(Rating) AS NumVisits
                            FROM Property LEFT JOIN Visit ON ID = PropertyID
                            WHERE Owner = %s
                            GROUP BY ID
                            ORDER BY {}""".format(column), [session['username']])
        properties = cur.fetchall()
        cur.close()
        return render_template('{}.html'.format(sortType), properties = properties)

    elif sortType == "VisitorFunctionality":
        result = cur.execute("""SELECT Name, Street, City, Zip, Size, PropertyType, IsPublic, IsCommercial, ID, AVG(Rating) AS AverageRating, COUNT(Rating) AS NumVisits
                            FROM Property LEFT JOIN Visit ON ID = PropertyID
                            WHERE ApprovedBy IS NOT NULL AND IsPublic
                            GROUP BY ID
                            ORDER BY {}""".format(column))
        properties = cur.fetchall()
        cur.close()
        return render_template('{}.html'.format(sortType), properties = properties)

    elif sortType == "OtherOwnersProperties":
        result = cur.execute("""SELECT Name, Street, City, Zip, Size, PropertyType, IsPublic, IsCommercial, ID, AVG(Rating) AS AverageRating, COUNT(Rating) AS NumVisits
                            FROM Property LEFT JOIN Visit ON ID = PropertyID
                            WHERE ApprovedBy IS NOT NULL AND IsPublic AND NOT Owner = %s
                            GROUP BY ID
                            ORDER BY {}""".format(column), [session['username']])
        properties = cur.fetchall()
        cur.close()
        return render_template('{}.html'.format(sortType), properties = properties)

    users = cur.fetchall()
    cur.close()

    return render_template('{}.html'.format(sortType), users = users)

################################################################################

@app.route('/ConfirmedProperties')
@is_logged_in
def ConfirmedProperties():

    # Create cursor
    cur = mysql.connection.cursor()

    # Execute for each type of column
    result = cur.execute("""SELECT Name, Street, City, Zip, Size, PropertyType, IsPublic, IsCommercial, ID, ApprovedBy, AVG(Rating) AS AverageRating
                            FROM Property LEFT JOIN Visit ON ID = PropertyID
                            WHERE ApprovedBy IS NOT NULL
                            GROUP BY ID
                            ORDER BY Name""")

    properties = cur.fetchall()

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return render_template('ConfirmedProperties.html', properties=properties)

@app.route('/UnconfirmedProperties')
@is_logged_in
def UnconfirmedProperties():

    # Create cursor
    cur = mysql.connection.cursor()

    # Execute for each type of column
    result = cur.execute("SELECT * FROM Property WHERE ApprovedBy IS NULL ORDER BY Name")

    properties = cur.fetchall()

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return render_template('UnconfirmedProperties.html', properties=properties)

@app.route('/SearchProperties', methods=['POST'])
def SearchProperties():
    column = request.form['column']
    searchterm = request.form['searchterm']
    searchType = request.form['searchType']
    if searchterm == '' or column == '':
        return redirect(url_for(searchType))

    if column in ['IsPublic', 'IsCommercial', 'IsApproved']:
        if searchterm.lower() in ['yes', 'true']:
            searchterm = 1
        else:
            searchterm = 0

    range = False
    if column in ['NumVisits', 'AverageRating']:
        if "-" in searchterm:
            range = True
            numvallist = searchterm.split("-")
            lower = float(numvallist[0])
            upper = float(numvallist[1])

    # Create cursor
    cur = mysql.connection.cursor()

    # Execute for each type of search
    if searchType == 'ConfirmedProperties':
        if range:
            result = cur.execute("""SELECT Name, Street, City, Zip, Size, PropertyType, IsPublic, IsCommercial, ID, ApprovedBy, AVG(Rating) AS AverageRating
                                    FROM Property LEFT JOIN Visit ON ID = PropertyID
                                    WHERE ApprovedBy IS NOT NULL
                                    GROUP BY ID
                                    HAVING {} BETWEEN {} AND {}
                                    ORDER BY Name""".format(column, lower, upper))
        else:
            result = cur.execute("""SELECT Name, Street, City, Zip, Size, PropertyType, IsPublic, IsCommercial, ID, ApprovedBy, AVG(Rating) AS AverageRating
                                    FROM Property LEFT JOIN Visit ON ID = PropertyID
                                    WHERE ApprovedBy IS NOT NULL AND {} = %s
                                    GROUP BY ID
                                    ORDER BY Name""".format(column), [searchterm])

    elif searchType == 'UnconfirmedProperties':
        if range:
            result = cur.execute("""SELECT * FROM Property
                                    WHERE ApprovedBy IS NULL
                                    HAVING {} BETWEEN {} AND {}
                                    ORDER BY Name """.format(column, lower, upper))
        else:
            result = cur.execute("""SELECT * FROM Property WHERE ApprovedBy IS NULL AND {} = %s ORDER BY Name""".format(column), [searchterm])

    elif searchType == 'VisitorFunctionality':
        if range:
            result = cur.execute("""SELECT Name, Street, City, Zip, Size, PropertyType, IsPublic, IsCommercial, ID, AVG(Rating) AS AverageRating, COUNT(Rating) AS NumVisits
                                    FROM Property LEFT JOIN Visit ON ID = PropertyID
                                    WHERE ApprovedBy IS NOT NULL AND IsPublic
                                    GROUP BY ID
                                    HAVING {} BETWEEN {} AND {}
                                    ORDER BY Name""".format(column, lower, upper))
        else:
            result = cur.execute("""SELECT Name, Street, City, Zip, Size, PropertyType, IsPublic, IsCommercial, ID, AVG(Rating) AS AverageRating, COUNT(Rating) AS NumVisits
                                    FROM Property LEFT JOIN Visit ON ID = PropertyID
                                    WHERE ApprovedBy IS NOT NULL AND IsPublic AND {} = %s
                                    GROUP BY ID
                                    ORDER BY Name""".format(column), [searchterm])

    elif searchType == 'OwnerFunctionality':
        if range:
            result = cur.execute("""SELECT Name, Street, City, Zip, Size, PropertyType, IsPublic, IsCommercial, ID, ApprovedBy, AVG(Rating) AS AverageRating, COUNT(Rating) AS NumVisits
                                    FROM Property LEFT JOIN Visit ON ID = PropertyID
                                    WHERE Owner = %s
                                    GROUP BY ID
                                    HAVING {} BETWEEN {} AND {}
                                    ORDER BY Name""".format(column, lower, upper), [session['username']])
        else:
            result = cur.execute("""SELECT Name, Street, City, Zip, Size, PropertyType, IsPublic, IsCommercial, ID, ApprovedBy, AVG(Rating) AS AverageRating, COUNT(Rating) AS NumVisits
                                FROM Property LEFT JOIN Visit ON ID = PropertyID
                                WHERE Owner = %s AND {} = %s
                                GROUP BY ID
                                ORDER BY Name""".format(column), [session['username'], searchterm])

    elif searchType == 'OtherOwnersProperties':
        if range:
            result = cur.execute("""SELECT Name, Street, City, Zip, Size, PropertyType, IsPublic, IsCommercial, ID, AVG(Rating) AS AverageRating, COUNT(Rating) AS NumVisits
                                    FROM Property LEFT JOIN Visit ON ID = PropertyID
                                    WHERE ApprovedBy IS NOT NULL AND IsPublic AND NOT Owner = %s AND {} = %s
                                    GROUP BY ID
                                    HAVING {} BETWEEN {} AND {}
                                    ORDER BY Name""".format(column, lower, upper), [session['username']])
        else:
            result = cur.execute("""SELECT Name, Street, City, Zip, Size, PropertyType, IsPublic, IsCommercial, ID, AVG(Rating) AS AverageRating, COUNT(Rating) AS NumVisits
                                FROM Property LEFT JOIN Visit ON ID = PropertyID
                                WHERE ApprovedBy IS NOT NULL AND IsPublic AND NOT Owner = %s AND {} = %s
                                GROUP BY ID
                                ORDER BY Name""".format(column), [session['username'], searchterm])

    properties = cur.fetchall()

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return render_template('{}.html'.format(searchType), properties=properties)

################################################################################

@app.route('/ApprovedItems')
@is_logged_in
def ApprovedItems():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM FarmItem WHERE IsApproved ORDER BY Name")

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
    result = cur.execute("SELECT * FROM FarmItem WHERE NOT IsApproved ORDER BY Name")

    items = cur.fetchall()

    # Close connection
    cur.close()

    return render_template('PendingItems.html', items=items)

@app.route('/AddItem', methods=['POST'])
def AddItem():
    itemType = request.form['type']
    name = request.form['name']
    approved = bool(request.form['approved'])

    if itemType == "" or name == "":
        if approved:
            return redirect(url_for('ApprovedItems'))
        else:
            return redirect(url_for('ManageItems'))

    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("INSERT INTO FarmItem(Name, IsApproved, Type) VALUES(%s, %s, %s)", [name, approved, itemType])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    if approved:
        return redirect(url_for('ApprovedItems'))
    else:
        return redirect(url_for('ManageItems'))

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
    cur.execute("UPDATE FarmItem SET IsApproved = TRUE WHERE Name = %s", [name])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return redirect(url_for('PendingItems'))

@app.route('/SearchItems', methods=['POST'])
def SearchItems():
    column = request.form['column']
    searchterm = request.form['searchterm']

    # Create cursor
    cur = mysql.connection.cursor()

    if searchterm == '':
        return redirect(url_for('ApprovedItems'))

    result = cur.execute("SELECT * FROM FarmItem WHERE {} = {} ORDER BY Name".format(column, searchterm))

    items = cur.fetchall()

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return render_template('ApprovedItems.html', items=items)

################################################################################

@app.route('/PropertyDetails/<string:ID>/')
@is_logged_in
def PropertyDetails(ID):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get properties
    result = cur.execute("""SELECT Name, Owner, Email, Street, City, Zip, Size, COUNT(Rating) AS NumVisits, AVG(Rating) AS AverageRating, PropertyType, IsPublic, IsCommercial, ID
                            FROM Property
                            JOIN User On Owner = User.Username
                            LEFT JOIN Visit ON Visit.PropertyID = ID
                            WHERE ID = %s
                            GROUP BY ID
                            ORDER BY Property.Name""", [ID])

    prop = cur.fetchone()

    result = cur.execute("""SELECT ItemName, Type
                            FROM Has Join Property ON Has.PropertyID = ID
                            JOIN FarmItem ON ItemName = FarmItem.Name
                            WHERE ID = %s""", [ID])
    items = cur.fetchall()
    crops = []
    animals = []
    for item in items:
        if item['Type'] == 'ANIMAL':
            animals.append(item['ItemName'])
        else:
            crops.append(item['ItemName'])

    animals = ', '.join(animals)
    crops = ', '.join(crops)

    numvisit= cur.execute("""SELECT * from Visit WHERE Username= %s AND PropertyID=%s""", [session['username'], ID])

    if numvisit > 0:
        logged = True
    else:
        logged = False


    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return render_template('PropertyDetails.html', property=prop, animals=animals, crops=crops, logged=logged)

@app.route('/VisitorHistory')
@is_logged_in
def VisitorHistory():
    # Create cursor
    cur = mysql.connection.cursor()

    result = cur.execute("""SELECT Name, date(substring(VisitDate from 1 for 10)) as VisitDate, Rating FROM Visit JOIN Property ON PropertyID = ID WHERE Username = %s;""", [session['username']])

    visits = cur.fetchall()

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()
    return render_template('VisitorHistory.html', visits=visits)

@app.route('/LogVisit<string:ID>', methods=['POST'])
@is_logged_in
def LogVisit(ID):
    rating = int(request.form['rating'])
    if rating == 0:
        return redirect(url_for('PropertyDetails', ID=ID))

    # Create cursor
    cur = mysql.connection.cursor()

    result = cur.execute("INSERT INTO Visit(Username, PropertyID, VisitDate, Rating) VALUES(%s, %s, CURRENT_TIMESTAMP, %s)", [session['username'], ID, rating])
    
    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    return redirect(url_for('PropertyDetails', ID=ID))

@app.route('/UnlogVisit<string:ID>', methods=['POST'])
@is_logged_in
def UnlogVisit(ID):
    # Create cursor
    cur = mysql.connection.cursor()

    result = cur.execute("DELETE FROM Visit WHERE Username=%s AND PropertyID=%s", [session['username'], ID])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()
    return redirect(url_for('PropertyDetails', ID=ID))


################################################################################

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
<<<<<<< HEAD
=======


# SELECT Property.Name, User.Username, Email, Street, City, Zip, Size, COUNT(Rating) AS NumVisits, AVG(Rating) AS AverageRating, PropertyType, IsPublic, IsCommercial, ID, FarmItem.Name
# FROM Property
# JOIN User On Owner = User.Username
# LEFT JOIN Visit ON Visit.PropertyID = ID
# LEFT JOIN Has ON Has.PropertyID = ID
# JOIN FarmItem ON ItemName = FarmItem.Name
# GROUP BY ID
# ORDER BY Property.Name

# Select Property.Name, FarmItem.Name
# from Has Join Property ON Has.PropertyID = ID
# JOIN FarmItem ON ItemName = FarmItem.Name
>>>>>>> ca9ef6dada7f1a101ac5f8d6908a06f708ddc27c
