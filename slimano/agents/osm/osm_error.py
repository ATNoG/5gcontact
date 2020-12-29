import json


class OsmError:

    def __init__(self, message=None):
        self.response = {
            'message': message
        }

    def set_message(self, message):
        self.response['message'] = message

    def __str__(self):
        return json.dumps(self.response)
