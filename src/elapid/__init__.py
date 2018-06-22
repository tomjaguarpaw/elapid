from collections import namedtuple

from flask import Flask
from flask_cors import CORS
import json
import sys
import gunicorn.app.base

import elapid._admin as _admin

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

Decorators = namedtuple('Decorators', 'endpoint')

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

            @app.route('/', methods=['GET'])
            def _root(): return _admin.admin_links

            api = Decorators(endpoint=decorate)

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
