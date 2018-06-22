from collections import namedtuple

from flask import Flask
from flask_cors import CORS
import json
import sys
import gunicorn.app.base

import elapid._admin as _admin
import elapid.jsonstructure as j

# Copied from http://docs.gunicorn.org/en/latest/custom.html
#
# WARNING: Unlike the code sample at the above link we delay the evaluation
# of the app argument, i.e.  we have 'self.application()' rather than
# 'self.application'.  Somehow it seems that if we start the app before the
# gunicorn server is started then there's a problem running anything that
# uses tensorflow.  I have no idea why, but it seems to be that way.
class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in self.options.items()
                       if key in self.cfg.settings and value is not None])
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application()

Decorators = namedtuple('Decorators', 'endpoint endpoint_with_form')

def api_main(structure_command_line, maker):
    revision_diff = _admin.git_revision_diff()

    command_line_json = json.loads(sys.argv[1])

    if not structure_command_line.validate(command_line_json):
        print("Invalid command line json")
    else:
        m = maker(command_line_json)

        create_your_app = m['endpoints']
        port = m['port']
        readme_md = m['README']
        make_revision_link = m['make_revision_link']

        def create_the_app():
            app = Flask(__name__)
            CORS(app)
            api_doc = {}

            def decorate(endpoint, structure_in, structure_out):
                def ret(f):
                    _admin.api_with_structure_in(app, api_doc, endpoint, structure_out, structure_in)(f)

                return ret

            def endpoint_with_form(endpoint, form_endpoint, form_files, structure_in, structure_out):
                def ret(f):
                    _admin.api_with_structure_in(app, api_doc, endpoint, structure_out, structure_in)(f)

                    def form():
                        yield '<form action="' + endpoint + '" method="post" enctype="multipart/form-data">'
                        for form_file in form_files:
                            yield '<p><input type="file" name="' + form_file + '"></p>'
                        yield '<p><input type="hidden" name="json_argument" value="{}"></p>'
                        yield '<p><input type="submit" value="Run"></p>'
                        yield '</form>'

                    if type(structure_in) == j.Empty:
                        form_ = '\n'.join(form())
                    else:
                        form_ = """
                        <p>I'm afraid I can't currently make a form
                        for the input structure that this endpoint
                        has.  Perhaps <a
                        href="https://github.com/tomjaguarpaw/elapid/issues">file
                        an issue</a>?
                        """

                    app.add_url_rule(rule=form_endpoint, endpoint=form_endpoint, view_func=lambda: form_, methods=['GET'])

                return ret

            @app.route('/', methods=['GET'])
            def _root(): return _admin.admin_links

            api = Decorators(endpoint=decorate,
                             endpoint_with_form=endpoint_with_form)

            create_your_app(api)

            _admin.setup_admin2(app, readme_md, revision_diff, api_doc, make_revision_link)

            return app

        options = {
            'bind': '%s:%s' % ('0.0.0.0', port),
            'accesslog': '-',
            # Conservatively setting workers to 1 in case we have
            # resources we can't share.  If you need multiprocessing this
            # should be increased, but we should also work out the
            # implications of that.
            'workers': 1
        }
        StandaloneApplication(create_the_app, options).run()
