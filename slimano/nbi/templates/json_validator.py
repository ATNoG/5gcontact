import re
import json

from jsonschema import validate
from jsonschema import exceptions as js_exceptions
from templates import exceptions
from os import listdir
from os.path import isfile, join


class JsonValidator:

    def __init__(self, schema_path=None):
        self.schema_path = schema_path if schema_path else './templates/schemas/'

    def validate_nst(self, json_in):
        schema = self._load_schema(self.schema_path, 'nst')
        try:
            validate(json_in, schema)
        except js_exceptions.ValidationError as ve:
            message = 'Error validating JSON: {}'. format(ve.cause)
            raise exceptions.ValidationError(message)

    def validate_nsi(self, json_in):
        schema = self._load_schema(self.schema_path, 'nsi')
        try:
            validate(json_in, schema)
        except js_exceptions.ValidationError as ve:
            message = 'Error validating JSON: {}'. format(ve.cause)
            raise exceptions.ValidationError(message)

    def validate_nfvo(self, json_in):
        schema = self._load_schema(self.schema_path, 'nfvo')
        try:
            validate(json_in, schema)
        except js_exceptions.ValidationError as ve:
            message = 'Error validating JSON: {}'. format(ve.cause)
            raise exceptions.ValidationError(message)

    @staticmethod
    def _load_schema(schema_path, str_part):
        file_path = schema_path
        path_files = [f for f in listdir(schema_path) if isfile(join(schema_path, f))]
        for file in path_files:
            matches = re.findall('.*{}.*'.format(str_part), file)
            if matches and len(matches) > 0:
                file_path = '{}{}'.format(file_path, file)

        with open(file_path, 'r') as f:
            schema = f.read()
        return json.loads(schema)
