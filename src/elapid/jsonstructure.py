"""Simple validators for JSON.  They are somewhat restrictive and
there are freeform JSON formats that you can't specify.  The benefit
is that they are very simple and precise.  It makes compatibility bugs
easy to track down.
"""

# TODO: These should produce nice error messages when validation fails.

class String:
    @staticmethod
    def validate(json):
        return isinstance(json, str)

    @staticmethod
    def help():
        yield "<string>"

class Number:
    @staticmethod
    def validate(json):
        return any([ type(json) == int
                   , isinstance(json, float)
                   ])

    @staticmethod
    def help():
        yield "<number>"

class Map:
    def __init__(self, of):
        self.of = of

    def validate(self, json):
        return isinstance(json, dict) \
               and all(self.of.validate(value)
                       for value
                       in json.values())

    def help(self):
        yield "{"
        yield '"<string>": '
        for line in self.of.help():
            yield '  ' + line
        yield "}"

class AllOf:
    def __init__(self, members):
        self.members = members

    def validate(self, json):
        if not isinstance(json, dict):
            return False
        elif not set(json.keys()) == set(self.members.keys()):
            return False
        else:
            for (field_name, field_value) in json.items():
                if not self.members[field_name].validate(field_value):
                    return False

            return True

    def help(self):
        yield "{ <all of>"
        for (field, schema) in self.members.items():
            yield '  "%s":' % field
            for field_help_line in schema.help():
                yield '        ' + field_help_line
        yield "}"

class OneOf:
    def __init__(self, options):
        self.options = options

    def validate(self, json):
        if not isinstance(json, dict):
            return False
        else:
            keys = list(json.keys())

            if len(keys) != 1:
                return False
            else:
                [field] = keys

                return field in (self.options.keys()) \
                       and self.options[field].validate(json[field])

    def help(self):
        yield "{ <one of>"
        for (field, schema) in self.options.items():
            yield '  "%s":' % field
            for field_help_line in schema.help():
                yield '        ' + field_help_line
        yield "}"

class Array:
    def __init__(self, of):
        self.of = of

    def validate(self, json):
        return isinstance(json, list) \
               and all(self.of.validate(element)
                       for element
                       in json)

    def help(self):
        yield "[ <array>"
        for of_help_line in self.of.help():
                yield '    ' + of_help_line
        yield "]"

class Bool:
    @staticmethod
    def validate(json):
        return isinstance(json, bool)

    @staticmethod
    def help():
        yield "<bool>"

class Empty:
    @staticmethod
    def validate(json):
        return json == {}

    @staticmethod
    def help():
        yield "{} (Yes, literally an empty record)"

def success_or_error(of):
    return OneOf({
        "success": of,
        "error": String()
    })
