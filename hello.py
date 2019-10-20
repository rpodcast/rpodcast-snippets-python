import os
import os.path
import glob
import logging
from pydub import AudioSegment

import boto3
from botocore.exceptions import ClientError

def get_s3_keys(bucket):
    s_3 = boto3.client('s3')
    """Get a list of keys in an S3 bucket."""
    keys = []
    resp = s_3.list_objects_v2(Bucket=bucket)
    for obj in resp['Contents']:
        file_name, file_extension  = os.path.splitext(obj['Key'])
        if file_extension == ".mp3":
            keys.append(obj['Key'])
    return keys

def list_bucket_objects(bucket_name):
    """List the objects in an Amazon S3 bucket

    :param bucket_name: string
    :return: List of bucket objects. If error, return None.
    """

    # Retrieve the list of bucket objects
    s_3 = boto3.client('s3')
    try:
        response = s_3.list_objects_v2(Bucket=bucket_name)
    except ClientError as e:
        # AllAccessDisabled error == bucket not found
        logging.error(e)
        return None

    # Only return the contents if we found some keys
    if response['KeyCount'] > 0:
        return response['Contents']

    return None

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


music_dir = '/home/eric/rpodcast_code/rpodcast-snippets-python/ogg_source/'  # Path where the videos are located
#print(os.listdir(music_dir))
my_files = os.listdir(music_dir)
test_bucket_name = 'rpodcast-snippets-audio'

s3_files = get_s3_keys(test_bucket_name)

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s: %(asctime)s: %(message)s')

os.chdir(music_dir)
for oggfile in my_files:
    if oggfile.endswith(".ogg"):
        mp3_filename = os.path.splitext(os.path.basename(oggfile))[0] + '.mp3'
        if os.path.exists(mp3_filename):
            print("file already exists!")
        else:
            print("converting file now")
            AudioSegment.from_file(oggfile).export(mp3_filename, format='mp3')
        # check if file exists in current s3 bucket list
        if (mp3_filename in s3_files):
            print("file already exists in s3")
        else:
            success = upload_file(mp3_filename, test_bucket_name)
            if success:
                logging.info(f'Added {mp3_filename} to {test_bucket_name}')


msg = "Hello World"
print(msg)