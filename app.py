from flask import Flask
from flask_restx import Resource, Api, reqparse, fields
from src.data_preproccesor import get_train_test_data
import os
from hydra import initialize, compose
from hydra.utils import to_absolute_path
from api import api

def get_config():
    initialize(version_base=None, config_path="./configs")
    cfg = compose("config.yaml")
    return cfg


app = Flask(__name__)
cfg = get_config()

app.config["BUNDLE_ERRORS"] = True
api.init_app(app)



if __name__ == "__main__":
    app.run(host=cfg.flask.host, port=cfg.flask.port, debug=True)
