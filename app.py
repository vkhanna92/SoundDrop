from flask import Flask
from flask import render_template, request, redirect
import boto3
from boto3.dynamodb.conditions import Key
from info import APP_KEY, APP_SECRET, REDIRECT_URI,TOPIC_ARN
import requests as r
from twilio.twiml.messaging_response import MessagingResponse
import re

app = Flask(__name__)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('CloudUsers')

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
        response = table.get_item(
            Key={
                'accountId': account_id
            }
        )
        phone_number = None
        if 'Item' in response:
            try:
                phone_number = response['Item']['phoneNumber']
            except KeyError:
                phone_number = None
            table.update_item(
                Key={
                    'accountId': account_id
                },
                UpdateExpression='SET accessKey = :key' ,
                ExpressionAttributeValues={
                    ':key': access_token
                }
            )
        else:
            table.put_item(
                Item={
                    'accountId' : account_id,
                    'accessKey' : access_token
                }
            )

        return render_template('profile.html',
                                account_id=account_id,
                                phone_number=phone_number)
    else:
        return redirect('/error')

@app.route("/save")
def save():
    phone_number = request.args.get('number')
    account_id = request.args.get('account_id')
    print(str(account_id))
    print(type(phone_number))
    if phone_number:
        table.update_item(
            Key={
                'accountId' : str(account_id)
            },
            UpdateExpression='SET phoneNumber = :number' ,
            ExpressionAttributeValues={
                ':number' : phone_number
            }
        )

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

@app.route("/download", methods=['POST'])
def incoming():
  phone_number = request.values.get('From', None)
  
  resp = MessagingResponse()
  response = table.query(
    IndexName='phoneNumber-index',
    KeyConditionExpression=Key('phoneNumber').eq(phone_number)
  )
  if len(response['Items']) == 0:
    resp.message('This is an unregistered or corrupted number!')
    return str(resp)
  
  url = request.values.get('Body', None)
  
  if not re.search(r'soundcloud\.com\/.+\/.+$', url):
    resp.message('This is not a valid link!')
    return str(resp)
  
  client = boto3.client("sns")
  r = client.publish(
      TopicArn=TOPIC_ARN,
      Message='string',
      MessageAttributes={
          'url': {
            'DataType': 'String',
            'StringValue': str(url)
          },
          'phoneNumber': {
            'DataType': 'String',
            'StringValue': str(response['Items'][0]['phoneNumber'])
          }
      }
  )
  resp.message('Attempting to download!')
  return str(resp)