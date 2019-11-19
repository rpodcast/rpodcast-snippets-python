# -*- coding: utf-8 -*-
#################################################
## Telegram Audio/Voice 2 MQTT/Home Assistant  ##
#################################################

from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater
from pydub import AudioSegment
import paho.mqtt.client as mqtt
from threading import Thread
from Queue import Queue

import logging, time, sys, yaml, os, os.path, re
import SimpleHTTPServer, SocketServer
import boto3
from botocore.exceptions import ClientError
from boto3 import resource
from boto3.dynamodb.conditions import Key

# The boto3 dynamoDB resource
dynamodb_resource = resource('dynamodb', region_name='us-east-1')

def get_table_metadata(table_name):
    """
    Get some metadata about chosen table.
    """
    table = dynamodb_resource.Table(table_name)

    return {
        'num_items': table.item_count,
        'primary_key_name': table.key_schema[0],
        'status': table.table_status,
        'bytes_size': table.table_size_bytes,
        'global_secondary_indices': table.global_secondary_indexes
    }

def add_item(table_name, col_dict):
    """
    Add one item (row) to table. col_dict is a dictionary {col_name: value}.
    """
    table = dynamodb_resource.Table(table_name)
    response = table.put_item(Item=col_dict)

    return response

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

def upload_file(file_name, bucket, object_name=None, ExtraArgs=None):
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
        if ExtraArgs:
            response = s3_client.upload_file(file_name, bucket, object_name, ExtraArgs=ExtraArgs)
        else:
            response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


path_matcher = re.compile(r'\$\{([^}^{]+)\}')
def path_constructor(loader, node):
  ''' Extract the matched value, expand env variable, and replace the match '''
  value = node.value
  match = path_matcher.match(value)
  env_var = match.group()[2:-1]
  return os.environ.get(env_var) + value[match.end():]

yaml.add_implicit_resolver('!path', path_matcher)
yaml.add_constructor('!path', path_constructor)

# Change Working directory to Script directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


# Callback for an established MQTT broker connection
def mqtt_connect(broker, userdata, flags, rc):
    logging.info("MQTT: Connected with the broker...")

# MQTT Publisher Thread
class MQTTPublisher(object):
    def __init__(self, myqueue):
        self.myqueue = myqueue
        thread3 = Thread(target=self.run, args=())
        thread3.daemon = True  # Daemonize thread
        thread3.start()  # Start the execution

    def run(self):
        while True:
            if not self.myqueue.empty():
                payload = self.myqueue.get()
                # Adding "New" Flag to payload!
                payload["new"] = "true"
                # reformatting payload dict to str
                str_payload = repr(payload).replace("\'", "\"").replace("u\"", "\"")
                logging.info("--- Publishing MQTT Message ---")
                logging.info("Payload: " + str_payload)
                broker.publish(cfg["mqtt"]["topic"], payload=str_payload, qos=0, retain=True)
                time.sleep(payload["duration"] + 1.5)
                logging.info("--- Publishing MQTT Reset Payload ---")
                broker.publish(cfg["mqtt"]["topic"], payload="{\"new\": \"false\"}", qos=0, retain=True)
                time.sleep(0.5)
            else:
                time.sleep(0.2)

# Simple HTTP Server
class HttpServer(object):
    def __init__(self, port=8000):
        self.port = port
        thread1 = Thread(target=self.run, args=())
        thread1.daemon = True  # Daemonize thread
        thread1.start()  # Start the execution

    def run(self):
        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        Handler.extensions_map.update({
            '.webapp': 'application/x-web-app-manifest+json',
        })
        self.httpd = SocketServer.TCPServer(("", self.port), Handler)
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()

# Telegram Bot
class TelegramBot(object):
    def __init__(self, token, queue, web_port, web_domain):
        self.token = token
        self.myqueue = queue
        self.web_port = web_port
        self.web_name = web_domain
        thread2 = Thread(target=self.run, args=())
        thread2.daemon = True  # Daemonize thread
        thread2.start()  # Start the execution

    def start(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")

    def text(self, bot, update):
        # Add User ID translation
        user_id = update.message.from_user.id
        self.myqueue.put({"type" : "text",
                          "user" : str(user_id),
                          "content" : update.message.text,
                          "duration" : 0})

    def voice(self, bot, update):
        user_id = update.message.from_user.id
        message_id = update.message.message_id
        chat_id = update.message.chat_id
        test_bucket_name = 'rpodcast-snippets-audio'
        s3_files = get_s3_keys(test_bucket_name)
        n_files = len(s3_files)

        # define episode index 
        episode_int = n_files + 1
        episode_index = str(episode_int).zfill(3)
        episode_title = "R-Podcast Snippet #" + episode_index
        episode_summary = "R-Podcast Snippet {episode_index} recorded by Eric Nantz. I wish I could give an actual description, but Eric's bot wrote this summary!".format(episode_index = episode_index)
        episode_timestamp = time.strftime("%Y-%m-%d_%H-%M")


        if cfg["allowed_contacts"] and (user_id in cfg["allowed_contacts"].keys()):
            username = cfg["allowed_contacts"][user_id]
            # Downloading Voice
            newfile = bot.get_file(update.message.voice.file_id)

            # generate file with episode index +1 over the current list of available files
            #filename = time.strftime("%Y-%m-%d_%H-%M") + '_' + str(user_id) + '.ogg'
            filename_main = 'rsnippet' + episode_index + '_' + time.strftime("%Y-%m-%d_%H-%M")
            ogg_filename = filename_main + '.ogg'
            mp3_filename = filename_main + '.mp3'
            #mp3_filename = os.path.splitext(os.path.basename(filename))[0] + '.mp3'
            newfile.download(ogg_filename)
            fileurl = "http://" + self.web_name + ":{}/".format(str(self.web_port)) + ogg_filename

            # assemble URL for item in amazon bucket
            s3_url = "https://" + test_bucket_name + ".s3.amazonaws.com/source/" + mp3_filename

            #bot.send_message(chat_id="@rpodcast_snips", text="I got the voice message!")
            bot.forward_message(chat_id="@rpodcast_snips", from_chat_id = chat_id, message_id = message_id)

            # convert to mp3
            # first obtain the length of the segment in milliseconds
            audio = AudioSegment.from_file(ogg_filename)
            episode_ms = len(audio)
            AudioSegment.from_file(ogg_filename).export(mp3_filename, format='mp3')

            # upload to s3
            if (mp3_filename in s3_files):
                logging.info("File already exists in s3")
            else:
                success = upload_file(
                    mp3_filename, test_bucket_name, object_name = 'source/' + mp3_filename,
                    ExtraArgs={
                        'ACL': 'public-read',
                        'ContentType': 'audio/mpeg'
                    }
                )       
                if success:
                    logging.info("Added file to s3")
                    # TODO: add to dynamo db table
                    episode_dict = {
                        'episode_id': filename_main,
                        'episode_int': episode_int,
                        'episode_index': episode_index,
                        'episode_title': episode_title,
                        'episode_summary': episode_summary,
                        'episode_timestamp': episode_timestamp,
                        'episode_ms': episode_ms,
                        'episode_url': s3_url
                    }
                    dbsuccess = add_item(table_name = 'rpodcast-snippets-db', col_dict = episode_dict)
                    if dbsuccess:
                        logging.info("Added entry to dynamodb")

            
            # update mqtt
            self.myqueue.put({"type": "voice",
                              "message_id": message_id,
                              "user": username,
                              "content": fileurl,
                              "duration": int(update.message.voice.duration)})
        else:
            logging.info("Voice Message rejected from user_id: {}".format(user_id))

    def run(self):
        #logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
        self.updater = Updater(token=self.token)
        self.dispatcher = self.updater.dispatcher

        # Handler Define
        start_handler = CommandHandler('start', self.start)
        log_handler = MessageHandler(Filters.text, self.text)
        voice_handler = MessageHandler(Filters.voice, self.voice)

        # Handler Registry
        self.dispatcher.add_handler(start_handler)
        self.dispatcher.add_handler(log_handler)
        self.dispatcher.add_handler(voice_handler)

        # Start Main Routine
        self.updater.start_polling()

    def shutdown(self):
        self.updater.stop()

def main(argv):
    # ADD gobals: other background tasks, contacts dict
    global broker
    global cfg

    # Config Parser
    try:
        f = open('conf/config.yaml', 'r')
    except IOError:
        print("Can't open config file!")
        sys.exit(1)
    else:
        with f:
            cfg = yaml.safe_load(f)

    #with open("conf/config.yaml", 'r') as ymlfile:
    #    cfg = yaml.load(ymlfile)


    log_level = logging.INFO  # Deault logging level
    if cfg["other"]["loglevel"] == 1:
        log_level = logging.ERROR
    elif cfg["other"]["loglevel"] == 2:
        log_level = logging.WARN
    elif cfg["other"]["loglevel"] == 3:
        log_level = logging.INFO
    elif cfg["other"]["loglevel"] >= 4:
        log_level = logging.DEBUG

    root = logging.getLogger()
    root.setLevel(log_level)
    # A more docker-friendly approach is to output to stdout
    logging.basicConfig(stream=sys.stdout, format="%(asctime)s - %(levelname)s - %(message)s",
                        datefmt="%m/%d/%Y %I:%M:%S %p", level=log_level)

    # Log startup messages and our configuration parameters
    logging.info("------------------------")
    logging.info("Starting up...")
    logging.info("--- MQTT Broker Configuration ---")
    logging.info("Domain: " + cfg["mqtt"]["domain"])
    logging.info("Port: " + str(cfg["mqtt"]["port"]))
    logging.info("Protocol: " + cfg["mqtt"]["protocol"])
    logging.info("Username: " + cfg["mqtt"]["username"])
    logging.info("Keepalive Interval: " + str(cfg["mqtt"]["keepalive"]))
    logging.info("Status Topic: " + cfg["mqtt"]["topic"])
    logging.info("--- Webserver Configuration ---")
    logging.info("Domain: " + cfg["webserver"]["domain"])
    logging.info("Port: " + str(cfg["webserver"]["port"]))
    logging.info("--- Telegram Configuration ---")
    logging.info("API Token: " + cfg["telegram"]["api-token"])


    try:
        # Handle mqtt connection and callbacks
        broker = mqtt.Client(client_id="", clean_session=True, userdata=None, protocol=eval("mqtt." + cfg["mqtt"]["protocol"]))
        broker.username_pw_set(cfg["mqtt"]["username"], password=cfg["mqtt"]["password"])
        broker.on_connect = mqtt_connect
        #broker.on_message = mqtt_message #Callback for Message Receiving, not used atm
        broker.connect(cfg["mqtt"]["domain"], cfg["mqtt"]["port"], cfg["mqtt"]["keepalive"])

        myqueue = Queue()


        #Creating and changing to downloader/webserver directory
        workdir = "conf/web/"
        if not os.path.exists(workdir):
            os.makedirs(workdir)
        os.chdir(workdir)

        # Start Webserver Thread
        myweb = HttpServer(port=cfg["webserver"]["port"])
        # Start Telegram Bot Thread
        bot = TelegramBot(cfg["telegram"]["api-token"], myqueue, cfg["webserver"]["port"], cfg["webserver"]["domain"])

        #Start Publisher Thread
        publish = MQTTPublisher(myqueue)

    except Exception, e:
        logging.critical("Exception: " + str(e))
        sys.exit(1)

    # Main work loop
    try:
        rc = broker.loop_start()
        if rc:
            logging.warn("Warning: " + str(rc))
        while True:
            time.sleep(1)
        broker.loop_stop()
    except Exception, e:
        logging.critical("Exception: " + str(e))
        sys.exit(1)


# Get things started
if __name__ == '__main__':
    main(sys.argv[1:])
