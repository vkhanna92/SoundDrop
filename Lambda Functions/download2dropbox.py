from __future__ import unicode_literals
import os
import boto3
import dropbox
from boto3.dynamodb.conditions import Key,Attr

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('CloudUsers')

def lambda_handler(event, context):
	# figure out what the object is
	bucket = 'soundsave'
	key = event['Records'][0]['s3']['object']['key'].replace('+', ' ')
	print (event['Records'][0])
	response = s3.head_object(Bucket=bucket, Key=key)
	phone_number = response['Metadata']['phone_number']

	# get the dropbox token
	users = table.query(
		IndexName='phoneNumber-index', KeyConditionExpression=Key('phoneNumber').eq(phone_number)
	)
	db_key = users['Items'][0]['accessKey']

	# download file
	file = boto3.resource('s3').Object(bucket, key).download_file('/tmp/' + str(key))
	
	# put into dropbox
	client = dropbox.Dropbox(db_key)
	f = open('/tmp/' + str(key), 'rb')
	r = client.files_upload(f.read(),'/Soundsave/' + key)

	# delete object
	s3.delete_object(
    Bucket=bucket,
    Key=key,  
	)
