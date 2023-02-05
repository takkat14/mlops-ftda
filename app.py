from flask import Flask
from flask_restx import Resource, Api, reqparse, fields
from api.src.data_preproccesor import get_train_test_data
import os
from api.endpoints import api, cfg


app = Flask(__name__)

app.config["BUNDLE_ERRORS"] = True
api.init_app(app)


if __name__ == "__main__":
    app.run(host=cfg.flask.host, port=cfg.flask.port, debug=True)
