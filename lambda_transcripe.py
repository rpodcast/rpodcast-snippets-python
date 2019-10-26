import boto3
from boto3 import resource

s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')

# The boto3 dynamoDB resource
dynamodb_resource = resource('dynamodb', region_name='us-east-1')

#arn:aws:dynamodb:us-east-1:318551790320:table/rpodcast-snippets-db/stream/2019-10-26T15:56:11.585

def lambda_handler(event, context):

    for record in event['Records']:
        print('hi')

