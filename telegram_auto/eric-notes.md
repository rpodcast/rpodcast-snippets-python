Things I did to get this to work:
* Set up a MQTT server on digital ocean using these instructions: https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-the-mosquitto-mqtt-messaging-broker-on-ubuntu-18-04
* Clone this repo to my nuc
* There is a typo in the maintainer's instructions.  The path should be `/opt/tel2mqtt` and not `/opt/telegram2mqtt`.
* Create a local dir for the produced audio files: `/extra/appdata/telegrambot/conf
* I first built the container interactively with this command: `docker run -e PUID=1000 -e PGID=1000 -v /extra/appdata/telegrambot/conf:/opt/tel2mqtt/conf --rm -it telegrambot:latest`
* In telegram I started a text chat with my bot `rpodcast_bot` and checked the console output.  I found that my user ID is `Rpodcast` and the integer ID is `AAAAAAAA`.  I then updated the `config.yml` file to have this at the end for the allowed users block.  Once I got the ID, I stopped the container.

```
10/13/2019 03:44:47 AM - DEBUG - Processing Update: {'message': {'delete_chat_photo': False, 'new_chat_photo': [], 'from': {'username': u'Rpodcast', 'first_name': u'Eric', 'last_name': u'N', 'is_bot': False, 'language_code': u'en', 'id': AAAAAAAA}, 'text': u'Hello there', 'caption_entities': [], 'entities': [], 'channel_chat_created': False, 'new_chat_members': [], 'supergroup_chat_created': False, 'chat': {'username': u'Rpodcast', 'first_name': u'Eric', 'last_name': u'N', 'type': u'private', 'id': AAAAAAAA}, 'photo': [], 'date': 1570938287, 'group_chat_created': False, 'message_id': 3}, 'update_id': BBBBBBBB}
```

* Copy the updated config file to the local area: `/extra/appdata/telegrambot/conf/config.yml`
* Create a `docker-compose.yml` file with following contents:

```
# meant to be run on the intel nuc nas
version: '2.1'

services:
  telegrambot:
    build: .
    container_name: telegrambot
    user: "1000:1000"
    volumes:
      - /extra/appdata/telegrambot/conf:/opt/tel2mqtt/conf
    restart:
      always

```

Commands to build and start container:

```
docker-compose -f docker-compose.yml build
docker-compose -f docker-compose.yml up -d

# to check logs
docker-compose -f docker-compose.yml logs
```

Commands to stop and remove images (needed if I refresh the compose file):

```
docker-compose -f docker-compose.yml stop
docker-compose -f docker-compose.yml rm
```

* Try doing a voice message to the bot and verify that a `.ogg` file is produced in the `/extra/appdata/telegrambot/conf/www` directory.

