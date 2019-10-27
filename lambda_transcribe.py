import boto3
import os

s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')


def lambda_handler(event, context):

    for record in event['Records']:
        source_bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        # form the clean job name
        mybase = os.path.basename(key)
        jobname = os.path.splitext(mybase)[0]
        object_url = "https://s3.amazonaws.com/{0}/{1}".format(
            source_bucket, key)
        response = transcribe.start_transcription_job(
            #TranscriptionJobName='MyTranscriptionJob',
            TranscriptionJobName=jobname,
            Media={'MediaFileUri': object_url},
            MediaFormat='mp3',
            LanguageCode='en-US'
        )
        print(response)