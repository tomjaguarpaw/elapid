import subprocess
from flask import jsonify
import flask
import json
import markdown
from mdx_gfm import PartialGithubFlavoredMarkdownExtension

from elapid.jsonstructure import success_or_error

def git_revision_diff():
    """Look up the git revision we are currently at, and the diff state of
    the repository.  This helps us keep track of what code our long
    running processes are running on.
    """

    "Get the git revision and diff in the current working directory"
    process = subprocess.Popen(["git", "rev-parse", "--verify", "HEAD"],
                                   stdout=subprocess.PIPE)
    (stdout, _) = process.communicate()
    revision = stdout.decode('ascii')

    process = subprocess.Popen(["git", "diff"],
                                   stdout=subprocess.PIPE)
    (stdout, _) = process.communicate()
    diff = stdout.decode('ascii')

    return (revision, diff)

def api_with_structure_in(app, api_doc, endpoint, structure, structure_in):
    """Creates an endpoint that reads a JSON argument out of the POST
    variable `json_argument` and validates its input and output.  The
    input should validate against `structure_in` and the output should
    validate against `success_or_error(structure)`.

    Using these validators is somewhat more restrictive than allowing
    freeform JSON, but when communicating over remote connections it's
    very handy to be precise about what you accept and emit.  It makes
    compatibility bugs easy to track down.
    """
    def ret(f):
        doc = f.__doc__ if f.__doc__ is not None else ""

        api_doc[endpoint] = (doc
                             + "\n\n"
                             + "* Input JSON in POST variable `json_argument`\n"
                             + "\n"
                             + "```\n"
                             + "\n".join(structure_in.help())
                             + "\n"
                             + "```\n"
                             + "\n"
                             + "* Output\n"
                             + "\n"
                             + "```\n"
                             + "\n".join(success_or_error(structure).help())
                             + "\n"
                             + "```")

        def jsonify_f():
            try:
                if 'json_argument' not in flask.request.form:
                    raise ValueError("The json_argument argument was missing in the request")
                json_in_as_string = flask.request.form['json_argument']
                json_in_as_object = json.loads(json_in_as_string)
                if not structure_in.validate(json_in_as_object):
                    return jsonify({"error": "json input did not validate " + str(json_in_as_object)})
                json_as_object = f(json_in_as_object, flask.request.files)
            except ValueError as e:
                return jsonify({"error": '\n'.join(e.args)})

            if success_or_error(structure).validate(json_as_object):
                return jsonify(json_as_object)
            else:
                return jsonify({"error": "json output did not validate " + str(json_as_object)})

        app.add_url_rule(rule=endpoint, endpoint=endpoint, view_func=jsonify_f, methods=['POST'])

    return ret

def setup_admin2(app, readme_md, revision_diff, api_doc, make_revision_link, forms):
    add_readme(app, md_, readme_md)
    add_git(app, md_, revision_diff, make_revision_link)
    add_api_doc(app, md_, api_doc)
    add_forms(app, forms)

def add_forms(app, forms):
    def lines():
        yield "<ul>"
        for (form_endpoint, endpoint) in forms:
            yield '<li><a href="%s">%s</a> (%s)</li>' % (form_endpoint, form_endpoint, endpoint)
        yield "</ul>"

    content = '\n'.join(lines())

    @app.route('/forms', methods=['GET'])
    def _(): return content

def add_api_doc(app, md, api_doc):
    def lines():
        yield "Make a POST request to\n"
        for (endpoint, doc) in api_doc.items():
            yield "## `%s`\n\n" % endpoint
            for line in doc.split('\n'):
                yield "%s" % line
            yield "\n\n"

    content = md.convert('\n'.join(lines()))

    @app.route('/API', methods=['GET'])
    def _API():
        return content

def add_git(app, md, revision_diff, make_revision_link):
    git_html = (md.convert(make_git_md(revision_diff, make_revision_link))
                + "\n(NB The revision and diff were calculated at startup but"
                + " there is still a potential race condition!)")

    @app.route('/git')
    def _git():
        return git_html

def add_readme(app, md, readme_md):
    @app.route('/README')
    def _README():
        return md.convert(readme_md)

def make_git_md(revision_diff, make_revision_link):
    (revision, diff) = revision_diff

    if diff == "":
        diff_message = "`git diff` was empty"
    else:
        diff_lines = ''.join("    %s\n" % line for line in diff.split('\n'))
        diff_message = "`git diff` was\n\n%s\n\n" % diff_lines

    revision_link = make_revision_link(revision)

    source = ("Server seems to be running at git commit [%s](%s).\n\n%s"
              % (revision, revision_link, diff_message))

    return source

md_ = markdown.Markdown(extensions=[PartialGithubFlavoredMarkdownExtension()])

admin_links = md_.convert("See\n\n"
                          + "* [API](/API)\n\n"
                          + "* [README](/README)\n\n"
                          + "* [git](/git)\n"
                          + "* [forms](/forms)\n")
