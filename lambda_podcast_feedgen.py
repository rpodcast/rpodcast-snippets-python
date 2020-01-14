import json
import os
import urllib.request
import re
import boto3
import decimal

from boto3.dynamodb.conditions import Key, Attr
from pcloud import PyCloud
from feedgen.feed import FeedGenerator


BUCKET_NAME = os.environ['BUCKET_NAME']
PCLOUD_FOLDER_ID = os.environ['PCLOUD_FOLDER_ID']
PCLOUD_USERNAME = os.environ['PCLOUD_USERNAME']
PCLOUD_PASS = os.environ['PCLOUD_PASS']
TABLE_ID = os.environ['TABLE_ID']
RSS_URL = os.environ['RSS_URL']
LOGO_URL = os.environ['LOGO_URL']

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_ID)

def create_summary(text, n_sentences=8):
    #  https://stackoverflow.com/a/17124446
    res = ' '.join(re.split(r'(?<=[.:;])\s', text)[:n_sentences])
    res2 = res + '...' + '\n\n' + 'Listen to the rest of the snippet to find out more!'
    return res2

def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return int(obj)
    raise TypeError

def lambda_handler(event, context):
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
    fg.logo(LOGO_URL)
    fg.subtitle('Musings on R, data science, linux, and life')
    fg.link( href=RSS_URL, rel='self')
    fg.language('en')

    fg.load_extension('podcast')

    # podcast-specific params
    fg.podcast.itunes_category('Technology')
    fg.podcast.itunes_author('Eric Nantz')
    fg.podcast.itunes_explicit('no')
    fg.podcast.itunes_owner('Eric Nantz', 'thercast@gmail.com')
    fg.podcast.itunes_summary('Residual Snippets is an informal, unedited, and free-flowing audio podcast from Eric Nantz.  If you enjoy hearing quick takes from a data scientist on their journey to blend innovative uses of open-source technology, contributing back to their brilliant communities, and juggling the curveballs life throws at them, this podcast is for you!')
    
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
    fg.rss_file('/tmp/residual_snippets.xml', pretty=True)
    
    # upload xml feed to pcloud and s3
    pc = PyCloud(PCLOUD_USERNAME, PCLOUD_PASS)
    pc.uploadfile(data = feed_string, filename='residual_snippets.xml', folderid=PCLOUD_FOLDER_ID)

    #upload_file("/tmp/residual_snippets.xml", BUCKET_NAME, object_name = 'residual_snippets.xml')
    s3_client.upload_file("/tmp/residual_snippets.xml", BUCKET_NAME, 'residual_snippets.xml')
    
    # create export of dynamodb and upload to s3
    # obtain all entries in database
    response2 = table.scan(
        FilterExpression=Attr('episode_int').gte(1)
    )

    # save object with the items themselves
    items2 = response2['Items']

    items2_sorted = sorted(items2, key = lambda i: i['episode_int'])

    db_export = "/tmp/dbexport.json"
    f = open(db_export, "w")
    f.write(json.dumps(items2_sorted, indent=2, default=decimal_default))
    f.close()
    
    # upload to s3 bucket
    success = s3_client.upload_file(db_export, BUCKET_NAME, 'dbexport.json')
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
