#!/usr/bin/env python3
from flask import Flask, render_template, request
from flask import redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Country, FoodItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
from flask import json
from flask import make_response
import requests

app = Flask(__name__)


CLIENT_ID = json.loads(
    open('/var/www/FlaskApp/FlaskApp/client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('postgresql://catalog:catalog@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Authenticate using Google+ account
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('/var/www/FlaskApp/FlaskApp/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
                                            'Current user is'
                                            ' already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: '
    '150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception:
        return None


# Disconnect from Google+ account
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Display the food items from one country in JSON format
@app.route('/countries/<int:country_id>/JSON')
def showCountryFoodJSON(country_id):
    items = session.query(FoodItem).filter_by(
        country_id=country_id).all()
    return jsonify(FoodItems=[i.serialize for i in items])


# Display the individual food item in JSON format
@app.route('/countries/<int:country_id>/<int:item_id>/JSON')
def showCountryFoodItemJSON(country_id, item_id):
    item = session.query(FoodItem).filter_by(
        id=item_id).one()
    return jsonify(FoodItem=item.serialize)


# Home page that displays the 5 first food items
@app.route('/')
@app.route('/countries/')
def showAllCountries():
    countries = session.query(Country).all()
    fooditems = session.query(FoodItem).limit(5).all()
    if 'username' not in login_session:
        return render_template('publiccountries.html', countries=countries,
                               fooditems=fooditems)
    else:
        return render_template('countries.html', countries=countries,
                               fooditems=fooditems)


# Add new country
@app.route('/countries/new/', methods=['GET', 'POST'])
def newCountry():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCountry = Country(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCountry)
        session.commit()
        return redirect('/countries')
    else:
        return render_template('newcountry.html')


# Show all food items from one country
@app.route('/countries/<int:country_id>/')
def showCountryFood(country_id):
    country_to_show = session.query(Country).filter_by(id=country_id).one()
    creator = getUserInfo(country_to_show.user_id)
    fooditems = session.query(FoodItem).filter_by(
        country_id=country_to_show.id)
    if ('username' not in login_session or
            creator.id != login_session['user_id']):
        return render_template('publiccountryfood.html', fooditems=fooditems,
                               country_to_show=country_to_show)
    else:
        return render_template('countryfood.html', fooditems=fooditems,
                               country_to_show=country_to_show)


# Show individual food item information
@app.route('/countries/<int:country_id>/<int:item_id>/')
def showCountryFoodItem(country_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    countryFoodItem = session.query(FoodItem).filter_by(id=item_id).one()
    country = session.query(Country).filter_by(id=country_id).one()
    creator = getUserInfo(country.user_id)
    if ('username' not in login_session or
            creator.id != login_session['user_id']):
        return render_template('publicshowcountryfooditem.html',
                               country_id=country_id,
                               item_id=item_id,
                               item=countryFoodItem)
    else:
        return render_template('showcountryfooditem.html',
                               country_id=country_id,
                               item_id=item_id,
                               item=countryFoodItem)


# Add new food item
@app.route('/countries/<int:country_id>/new/', methods=['GET', 'POST'])
def newCountryFoodItem(country_id):
    if 'username' not in login_session:
        return redirect('/login')
    country = session.query(Country).filter_by(id=country_id).one()
    if login_session['user_id'] != country.user_id:
        return "<script>function myFunction() {alert('You are not authorized "
        "to add food items to this Country. Please add your own Country "
        "to add food items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        newCountryFoodItem = FoodItem(
            name=request.form['name'], description=request.form['description'],
            country_id=country_id, user_id=country.user_id)
        session.add(newCountryFoodItem)
        session.commit()
        return redirect(url_for('showCountryFood', country_id=country_id))
    else:
        return render_template('newcountryfood.html', country_id=country_id)


# Edit country information
@app.route('/countries/<int:country_id>/edit/', methods=['GET', 'POST'])
def editCountry(country_id):
    editedCountry = session.query(Country).filter_by(id=country_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedCountry.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized "
        "to edit this Country. Please add your own Country to "
        "edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedCountry.name = request.form['name']
        session.add(editedCountry)
        session.commit()
        flash("Country has been edited")
        return redirect(url_for('showCountryFood', country_id=country_id))
    else:
        return render_template(
            'editcountry.html', country_id=country_id, item=editedCountry)


# Edit food item information
@app.route('/countries/<int:country_id>/<int:item_id>/edit/',
           methods=['GET', 'POST'])
def editCountryFoodItem(country_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedCountryFoodItem = session.query(FoodItem).filter_by(id=item_id).one()
    country = session.query(Country).filter_by(id=country_id).one()
    if login_session['user_id'] != country.user_id:
        return "<script>function myFunction() {alert('You are not authorized "
        "to edit food items from this country. Please add your own country "
        "to edit food items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedCountryFoodItem.name = request.form['name']
        if request.form['description']:
            editedCountryFoodItem.description = request.form['description']
        session.add(editedCountryFoodItem)
        session.commit()
        flash("Food Item has been edited")
        return redirect(url_for('showCountryFood', country_id=country_id))
    else:
        return render_template(
            'editcountryfood.html', country_id=country_id,
            item_id=item_id, item=editedCountryFoodItem)


# Delete food item
@app.route('/countries/<int:country_id>/<int:item_id>/delete/',
           methods=['GET', 'POST'])
def deleteCountryFoodItem(country_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(FoodItem).filter_by(id=item_id).one()
    country = session.query(Country).filter_by(id=country_id).one()
    if login_session['user_id'] != country.user_id:
        return "<script>function myFunction() {alert('You are not authorized "
        "to delete food items from this country. Please add your own country "
        "to delete food items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("Food Item has been deleted")
        return redirect(url_for('showCountryFood', country_id=country_id))
    else:
        return render_template('deletecountryfood.html', item=itemToDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000, threaded=False)
