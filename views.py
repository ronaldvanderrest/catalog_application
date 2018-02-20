from flask import Flask, render_template, request, redirect, jsonify, \
    url_for, flash
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)


# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/catalog.json/')
def catalogJSON():
    """sends back all categories and items in json format"""
    categories = session.query(Category).all()
    items = session.query(Item).all()
    return jsonify(
        Category=[i.serialize for i in categories],
        Item=[item.serialize for item in items])


@app.route('/categories.json/')
def categoriesJSON():
    """sends back all categories in json format"""
    categories = session.query(Category).all()
    return jsonify(Category=[i.serialize for i in categories])


@app.route('/items.json/')
def itemsJSON():
    """sends back all items in json format"""
    items = session.query(Item).all()
    return jsonify(Item=[item.serialize for item in items])


@app.route('/login/')
def showLogin():
    """directs to the login page"""
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    """oauth2 for facebook"""
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']

    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)

    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.12/me"
    '''
        Due to the formatting for the result from the server token exchange we
        have to split the token first on commas and select the first index
        which gives us the key : value for the server access token then we
        split it on colons to pull out the actual token value and replace the
        remaining quotes with nothing so that it can be used directly in the
        graph api calls
    '''

    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.12/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.12/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
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
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;\
        -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


# User Helper Functions
def createUser(login_session):
    """create a new user in the database"""
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    """get the information of the user"""
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    """get the id of the user"""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/fbdisconnect/')
def fbdisconnect():
    """disconnect facebook login"""
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/')
@app.route('/catalog/')
def showCatalog():
    """show the homepage (depending on whether the requestor has logged in)"""
    categories = session.query(Category).all()
    items = session.query(Item).order_by(desc(Item.id)).limit(10)
    if 'username' not in login_session:
        return render_template(
                                'publiccatalog.html', categories=categories,
                                items=items
                                )
    else:
        return render_template(
                                'catalog.html', categories=categories,
                                items=items
                                )


@app.route('/catalog/newitem/', methods=['GET', 'POST'])
def newItem():
    """On a GET request show the new itempage (depending on whether the
    requestor has logged in). On a POST request, create the new item in the
    database.
    """
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItemCat_id = session.query(Category).filter_by(
            name=request.form['category']).one()
        newItem = Item(
            title=request.form['title'],
            description=request.form['description'], cat_id=newItemCat_id.id,
            user_id=login_session['user_id'])
        session.add(newItem)
        flash('New Item %s Successfully Created' % newItem.title)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        categories = session.query(Category).all()
        return render_template('newitem.html', categories=categories)


@app.route('/catalog/<int:cat_id>/items/')
def redirectUrlShowItemsInCategory(cat_id):
    """redirect to a url that has the name of the category to prevent url's
    with id's
    """
    category = session.query(Category).filter_by(id=cat_id).one()
    return redirect(url_for(
        'showItemsInCategory', category_name=category.name))


@app.route('/catalog/<category_name>/items/')
def showItemsInCategory(category_name):
    """show specific items on a category"""
    category = session.query(Category).filter_by(name=category_name).one()
    categories = session.query(Category).all()
    items = session.query(Item).filter_by(cat_id=category.id).all()
    if 'username' not in login_session:
        return render_template(
            'publicitems.html', category=category, categories=categories,
            items=items)
    else:
        return render_template(
            'items.html', category=category, categories=categories,
            items=items)


@app.route('/catalog/<int:cat_id>/<item_name>')
def redirectUrlShowItem(cat_id, item_name):
    """redirect to a url that has the name of the category and item
    to prevent url's with id's
    """
    category = session.query(Category).filter_by(id=cat_id).one()
    return redirect(url_for(
        'showItem', category_name=category.name, item_name=item_name))


@app.route('/catalog/<category_name>/<item_name>/')
def showItem(category_name, item_name):
    """show the itempage (depending on whether the requestor has logged in)"""
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(
        title=item_name, cat_id=category.id).first()
    if 'username' not in login_session:
        return render_template(
            'publicitemdetails.html', category=category, item=item)
    else:
        return render_template(
            'itemdetails.html', category=category, item=item)


@app.route(
    '/catalog/<category_name>/<item_name>/edit/', methods=['GET', 'POST'])
def editItem(category_name, item_name):
    """On a GET request load the edit page (if user has logged in). On a POST
    request, check if the requestor has the same user_id as the item. Then
    update the item in the database
    """
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(
        title=item_name, cat_id=category.id).first()
    itemcategory = session.query(Category).filter_by(id=item.cat_id).first()
    if item.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized" \
            " to edit this Item. Please create your own Item in order to " \
            "edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['title']:
            item.title = request.form['title']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['category']:
            editItemCat_id = session.query(Category).filter_by(
                name=request.form['category']).one()
            item.cat_id = editItemCat_id.id
        session.add(item)
        session.commit()
        flash('Item successfully edited')
        # to make sure to get new cat_id before setting name again for the
        # redirect
        itemcategory = session.query(Category).filter_by(
            id=item.cat_id).first()
        return redirect(url_for(
            'showItem', category_name=itemcategory.name, item_name=item.title))
    else:
        return render_template(
            'edititem.html', categories=categories, item=item,
            itemcategory=itemcategory)


@app.route(
    '/catalog/<category_name>/<item_name>/delete/', methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
    """On a GET request load the delete page (if user has logged in). On a POST
    request, check if the requestor has the same user_id as the item. Then
    delete the item in the database
    """
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(
        title=item_name, cat_id=category.id).first()
    if item.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not " \
            "authorized to edit this Item. Please create your own Item in " \
            "order to edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash('Item successfully deleted')
        return redirect(url_for(
            'showItemsInCategory', category_name=category_name))
    else:
        categories = session.query(Category).all()
        itemcategory = session.query(Category).filter_by(
            id=item.cat_id).first()
    return render_template(
        'deleteitem.html', categories=categories, item=item,
        itemcategory=itemcategory)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        # if login_session['provider'] == 'google':
        #     gdisconnect()
        #     del login_session['gplus_id']
        #     del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCatalog'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
