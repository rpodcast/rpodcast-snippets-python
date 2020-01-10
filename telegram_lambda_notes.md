Following along the blog post on creating a lambda-powered telegram bot: https://dev.to/nqcm/-building-a-telegram-bot-with-aws-api-gateway-and-aws-lambda-27fg

- invoke url: Obtain from API gateway interface

establishing webhook:

```
https://api.telegram.org/bot<your-bot-token>/setWebHook?url=<your-API-invoke-URL
```

Example json from bot when sending voice message to api gateway and lambda:

```json
{'update_id': 105627327, 'message': {'message_id': 6, 'from': {'id': <user_id>, 'is_bot': False, 'first_name': 'Eric', 'last_name': 'N', 'username': 'Rpodcast', 'language_code': 'en'}, 'chat': {'id': <user_id>, 'first_name': 'Eric', 'last_name': 'N', 'username': 'Rpodcast', 'type': 'private'}, 'date': 1578626473, 'voice': {'duration': 6, 'mime_type': 'audio/ogg', 'file_id': 'AwADAQAD2wADFQ7BRLdMDhPy5AcGFgQ', 'file_unique_id': 'AgAD2wADFQ7BRA', 'file_size': 11893}}}
```

The key parts are the `file_id`  in the `voice` portion.  Goal is to grab that file and put it in an s3 bucket

JSON response from calling `getFile` API endpoint based on file id:

```json
{'ok': True, 'result': {'file_id': 'AwADAQAD3AADFQ7BRB3KLyG3YLtVFgQ', 'file_unique_id': 'AgAD3AADFQ7BRA', 'file_size': 12501, 'file_path': 'voice/file_6.oga'}}
```

Forwarding the message to the actual residual snippets channel:

* I got it working, but the key step is to make sure the bot is added as an admin to the residual snippets channel first!
