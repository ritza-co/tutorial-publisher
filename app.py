import os
import random
import string
import subprocess

from flask import Flask, request
from flask import send_from_directory
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'md', 'markdown'}

app = Flask(__name__)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def publish_tutorial():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        fle = request.files['file']
        if fle.filename == '':
            return redirect(request.url)
        if fle and allowed_file(fle.filename):
            filename = secure_filename(fle.filename)
            save_name = ''.join(random.sample(string.ascii_letters, 6))
            out_noex = os.path.join("/tmp/uploads", save_name)
            out_md = out_noex + ".md"
            out_html = out_noex + ".html"
            out_html_final = out_noex + "f" + ".html"

            assets_path = os.path.join(os.getcwd(), "assets")
            pandoc_filter = os.path.join(assets_path, "fix-pre-code.lua")

            fle.save(out_md)

            title = ""
            metadescription = ""
            try:
                # try find a reasonable title and metadescription from the 
                # markdown content
                with open(out_md) as f:
                    head = [next(f) for x in range(10)]
                    head = [x for x in head if len(x) > 2]

                    title = head[0].replace("#", "").strip()
                    metadescription = ' '.join(head[1:3])[:150]
            except Exception as e:
                print(e)

            try:
                output = subprocess.check_output([
                    'pandoc',
                    out_md,
                    '--no-highlight',
                    '-f', 'markdown-auto_identifiers-citations',
                    '-t', 'html',
                    '--lua-filter', pandoc_filter,
                    '-o', out_html
                    ])
            except subprocess.CalledProcessError as e:
                print(e.output)

            try:
                # open the templates to pre-pend and append to the file
                template_pre = os.path.join(assets_path, "template_pre.html")
                template_post = os.path.join(assets_path, "template_post.html")
                with open(template_pre, encoding="utf-8") as f:
                    pre = f.read()
                    pre = pre.replace("{title}", title)
                    pre = pre.replace("{metadescription}", metadescription)
                with open(template_post, encoding="utf-8") as f:
                    post = f.read()

                with open("/tmp/uploads/{}.html".format(save_name), encoding="utf-8") as f:
                    content = f.read()
                complete = pre + content + post
                with open(out_html_final, "w", encoding="utf-8") as f:
                    f.write(complete)

                return send_from_directory("/tmp/uploads/", save_name + "f" + ".html" , as_attachment=True)

            except Exception as e:
                print(e)
                return "Sorry :( something went wrong."

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <p>Upload a markdown file and get a beautiful HTML file with code highlighting in return</p>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

if __name__ == "__main__":
    app.run("0.0.0.0")
