from jsonschema import validate
from jsonschema import exceptions as js_exceptions
from templates import exceptions

import yaml


class YamlValidator:

    def __init__(self, schema_path=None):
        self.schema = None
        schema_path = schema_path if schema_path else './schemas/nst.yaml'
        self.load_schema(schema_path)

    def validate(self, yaml_in):
        try:
            validate(yaml.load(yaml_in), self.schema)
        except js_exceptions.ValidationError as ve:
            message = 'Error validating YAML: {}'. format(ve.cause)
            raise exceptions.ValidationError(message)

    def load_schema(self, schema_path):
        with open(schema_path, 'r') as f:
            self.schema = f.read()
