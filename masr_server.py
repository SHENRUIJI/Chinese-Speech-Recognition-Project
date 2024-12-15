__author__ = 'yangjiuyue'
__mtime__ = '20241215'

# -*- encoding: utf-8 -*-
import os
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import beamdecode

app = Flask(__name__, template_folder="templates", static_folder="static", static_url_path="/static")
CORS(app, resources=r'/*', supports_credentials=True)  # Support for cross-domain access


@app.route("/masr/recognize", methods=["POST"])
def recognize():
    try:
        f = request.files["audio"]
        file_name = f.filename.replace('"', '').strip()
        fpath = os.path.join('save_audio', file_name)
        f.save(fpath)
        text = beamdecode.predict(fpath)
        return jsonify({'recognize text': text, 'code': 200, 'message': '成功'})
    except Exception:
        return jsonify({'recognize text': '', 'code': 600, 'message': '识别过程有误！'})


@app.route('/')
def home():
    return render_template("index.html")


if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run()
