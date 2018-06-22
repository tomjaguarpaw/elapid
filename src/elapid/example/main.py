"""To run this program you may need to install dependencies, for
example

    pip3 install flask flask_cors py-gfm gunicorn

"""

README = """You can run this API server with JSON arguments whose structure
matches 'command_line_structure', for example

    PYTHONPATH=src python3 -m elapid.example.main '{"port": 7700, "value": 10}'

If you navigate to

    http://<server>:<port>/

then you will see the index page which helps you understand the API.
For experimentation you can use curl on the command line to contact
the API endpoints.  For example,

* `curl -X POST --form-string 'json_argument={}' http://<server>:<port>/hello_world`
* `curl -X POST --form-string 'json_argument=100' http://<server>:<port>/add_value`
* `curl -X POST --form 'file1=@<filename>' --form 'file2=@<filename>' --form-string 'json_argument={}' http://<server>:<port>/filenames`
* `curl -X POST --form 'input_file=@<filename>' --form-string 'json_argument={}' http://<server>:<port>/detect_faces`
"""

from elapid import api_main
import elapid.jsonstructure as j
from elapid.example.face_detector import ExampleFaceDetector

def create_endpoints(command_line_json):
    # Things that stay alive should be created here
    face_detector = ExampleFaceDetector(example_parameter="value")

    def endpoints(api):
        # Endpoint definitions live in here.
        #
        # The endpoint function names are completely irrelevant.  It's
        # probably most convenient to just make them all "_".

        @api.endpoint(endpoint='/hello_world',
                      structure_in=j.Empty(),
                      structure_out=j.String())
        def _(_json_in, _files):
            return {'success': "Hello world!"}

        @api.endpoint(endpoint='/add_value',
                      structure_in=j.Number(),
                      structure_out=j.String())
        def _(json_in, _files):
            the_sum = command_line_json["value"] + json_in
            return {'success': "The sum is %s" % the_sum }

        @api.endpoint(endpoint='/filenames',
                      structure_in=j.Empty(),
                      structure_out=j.Array(j.String()))
        def _(_json_in, files):
            return {'success': list(files.keys())}

        detect_faces_output_structure = \
            j.Array(j.AllOf({"x1": j.Number(), "y1": j.Number(),
                             "x2": j.Number(), "y2": j.Number()}))

        @api.endpoint_with_form(endpoint='/detect_faces',
                                form_endpoint='/form_detect_faces',
                                form_files=['input_file'],
                                structure_in=j.Empty(),
                                structure_out=detect_faces_output_structure)
        def _(_json_in, files):
            """Upload the image in a file upload called 'input_file'"""

            image_data = files["input_file"].read()

            list_of_faces = face_detector.detect_faces(image_data)
            list_of_faces_objects = [{"x1": x1, "y1": y1, "x2": x2, "y2": y2}
                                     for ((x1, y1), (x2, y2))
                                     in list_of_faces]

            return {'success': list_of_faces_objects}

    def make_revision_link(revision):
        # Change this to point to your application's repository
        return ("https://github.com/tomjaguarpaw/elapid/commit/%s" % revision)

    return {
        "port": command_line_json["port"],
        "endpoints": endpoints,
        "README": README,
        "make_revision_link": make_revision_link
    }

command_line_structure = j.AllOf({
    "port": j.Number(),
    "value": j.Number()
})

if __name__ == '__main__': api_main(command_line_structure, create_endpoints)
