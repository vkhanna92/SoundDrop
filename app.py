from flask import Flask
from flask import render_template, request, redirect
from info import APP_KEY, APP_SECRET, REDIRECT_URI
import requests as r

app = Flask(__name__)

@app.route("/")
def home():
    return render_template('home.html',
                          app_key=APP_KEY,
                          redirect_uri=REDIRECT_URI,
                          logged_in=False)


@app.route("/profile")
def profile():
    if request.args.get('code'):
        code = request.args.get('code')
        
        data = {
            'code': code,
            'grant_type': 'authorization_code',
            'client_id': APP_KEY,
            'client_secret': APP_SECRET,
            'redirect_uri': REDIRECT_URI
        }
        resp = r.post('https://api.dropboxapi.com/oauth2/token', data=data)
       
        access_token = resp.json()['access_token']
        account_id = resp.json()['account_id']

        phone_number = None
        
        return render_template('profile.html',
                                account_id=account_id,
                                phone_number=phone_number)
    else:
        return redirect('/error')

@app.route("/save")
def save():
    phone_number = request.args.get('number')
    account_id = request.args.get('account_id')

    if phone_number:

        return render_template('profile.html',
                                saved=True,
                                account_id=account_id,
                                phone_number=phone_number)
    else:
        return render_template('profile.html',
                                error=True,
                                account_id=account_id)

@app.route('/error')
def error():
  return render_template('error.html')