import json


class AgentResponse:

    def __init__(self, status=None, message=None):
        self.response = {
            'status': status,
            'message': message,
            'outputs': {},
            'agent_info': {}
        }

    def set_status(self, status):
        self.response['status'] = status

    def set_message(self, message):
        self.response['message'] = message

    def set_outputs(self, name, value):
        self.response['outputs'][name] = value

    def set_agent_info(self, name, value):
        self.response['agent_info'][name] = value

    def __str__(self):
        return json.dumps(self.response)
