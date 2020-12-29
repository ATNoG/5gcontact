import json


class EngineResponse:

    def __init__(self, status=None, message=None):
        self.response = {
            'status': status,
            'message': message,
            'modules_info': {}
        }

    def set_status(self, status):
        self.response['status'] = status

    def set_message(self, message):
        self.response['message'] = message

    def set_modules_info(self, module_info):
        self.response['modules_info'].append(module_info)

    def get_response(self, in_json=False):
        return self.response if not in_json else json.dumps(self.response)
    
    def __str__(self):
        return json.dumps(self.response)
