import json
import os
import urllib.request
import re
import boto3

from feedgen.feed import FeedGenerator
from boto3.dynamodb.conditions import Key, Attr
from pcloud import PyCloud

BUCKET_NAME = os.environ['BUCKET_NAME']
PCLOUD_FOLDER_ID = os.environ['PCLOUD_FOLDER_ID']
PCLOUD_USERNAME = os.environ['PCLOUD_USERNAME']
PCLOUD_PASS = os.environ['PCLOUD_PASS']

s3 = boto3.resource('s3')
transcribe = boto3.client('transcribe')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('rpodcast-snippets-db')

def create_summary(text, n_sentences=4):
    #  https://stackoverflow.com/a/17124446
    res = ' '.join(re.split(r'(?<=[.:;])\s', text)[:n_sentences])
    res2 = res + '...' + '\n\n' + 'Listen to the rest of the snippet to find out more!'
    return res2


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then same as file_name
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


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

    # obtain all entries in database
    response = table.scan(
        FilterExpression=Attr('episode_int').gte(1)
    )

    # save object with the items themselves
    items = response['Items']
    #print(items)

    items_sorted = sorted(items, key = lambda i: i['episode_int'])

    # set up overall feed metadata
    fg = FeedGenerator()

    # general feed params
    fg.id('https://r-podcast.org')
    fg.title('Residual Snippets')
    fg.author( {'name':'Eric Nantz', 'email':'thercast@gmail.com'})
    fg.link(href='https://r-podcast.org', rel='alternate' )
    fg.logo('https://rpodcast-snippets-audio.s3.amazonaws.com/residual_snippets.png')
    fg.subtitle('Musings on R, data science, linux, and life')
    fg.link( href='https://r-podcast.org/rsnippets.xml', rel='self')
    fg.language('en')

    fg.load_extension('podcast')

    # podcast-specific params
    fg.podcast.itunes_category('Technology')
    fg.podcast.itunes_author('Eric Nantz')
    fg.podcast.itunes_explicit('no')
    fg.podcast.itunes_owner('Eric Nantz', 'thercast@gmail.com')
    fg.podcast.itunes_summary('R-Snippets is an informal, unedited, and free-flowing audio podcast from Eric Nantz.  If you enjoy hearing quick takes from a data scientist on their journey to blend innovative uses of open-source technology, contributing back to their brilliant communities, and juggling the curveballs life throws at them, this podcast is for you!')
    
    for x in range(len(items_sorted)):
        #print(items[x])
        fe = fg.add_entry()
        fe.title(items_sorted[x]['episode_title'])
        fe.author( {'name':'Eric Nantz', 'email':'thercast@gmail.com'} )
        fe.enclosure(url=items_sorted[x]['episode_url'], type = 'audio/mpeg')

        # process description before adding to feed
        ep_desc = create_summary(items_sorted[x]['episode_summary'])
        #fe.description(items_sorted[x]['episode_summary'])
        fe.description(ep_desc)

    # populate xml file for RSS feed    
    feed_string = fg.rss_str(pretty=True)
    #fg.rss_file('residual_snippets.xml', pretty=True)

    # upload to pcloud
    pc = PyCloud(PCLOUD_USERNAME, PCLOUD_PASS)
    pc.uploadfile(data = feed_string, filename='residual_snippets.xml', folderid=PCLOUD_FOLDER_ID)

    # upload to s3 bucket
    #success = upload_file('residual_snippets.xml', BUCKET_NAME, object_name = 'residual_snippets.xml')

