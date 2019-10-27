import json
import os
import urllib.request

import boto3


BUCKET_NAME = os.environ['BUCKET_NAME']

s3 = boto3.resource('s3')
transcribe = boto3.client('transcribe')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('rpodcast-snippets-db')


def lambda_handler(event, context):
    # job_name will be the same as the key column (episode_id) in database
    job_name = event['detail']['TranscriptionJobName']
    print(job_name)
    job = transcribe.get_transcription_job(TranscriptionJobName=job_name)
    uri = job['TranscriptionJob']['Transcript']['TranscriptFileUri']
    print(uri)

    content = urllib.request.urlopen(uri).read().decode('UTF-8')

    print(json.dumps(content))

    data = json.loads(content)

    text = data['results']['transcripts'][0]['transcript']

    # update episode_summary in database for this record
    response = table.update_item(
        Key={
            'episode_id': job_name
        },
        UpdateExpression="set episode_summary = :r",
        ExpressionAttributeValues={
            ':r': text
        },
        ReturnValues="UPDATED_NEW"
    )
    
    # add text file with transcript to s3 bucket
    object = s3.Object(BUCKET_NAME, job_name + '-asrOutput.txt')
    object.put(Body=text)
