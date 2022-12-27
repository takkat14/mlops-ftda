from flask import Flask
from flask_restx import Resource, Api, reqparse, fields
from src.data_preproccesor import get_train_test_data
import src.trainer
import os
from hydra import initialize, compose
from hydra.utils import to_absolute_path


def get_config():
    initialize(version_base=None, config_path="./configs")
    cfg = compose("config.yaml")
    return cfg


app = Flask(__name__)
cfg = get_config()

app.config["BUNDLE_ERRORS"] = True
api = Api(app)

model_add = api.model(
    "Model.add.input", {
        "name":
        fields.String(
            required=True,
            title="Model name",
            description="Used as a key in local models storage; Must be unique;"
        ),
        "type":
        fields.String(required=True,
                      title="Model type",
                      description="Must be 'logreg' or 'linearSVC';"),
        "params":
        fields.String(
            required=True,
            title="Model params",
            description="Params to use in model init; Must be valid dict;",
            default="{}")
    })



@api.route("/models/list")
class ModelList(Resource):
    @api.doc(responses={200: "Success"})
    def get(self):
        models = os.listdir("models")
        return {"models": models}, 200


@app.route("/")
def hello():
    return "<h1 style='color:blue'>Hello There!</h1>"


@app.route("/download")
def testing_download():
    get_train_test_data(cfg)


@app.route("/models/list")
def list_available_models():
    return os.listdir(to_absolute_path("models"))


@app.route("/models/add")
def train():
    X_train, X_test, y_train, y_test = get_train_test_data(cfg)


if __name__ == "__main__":
    app.run(host=cfg.flask.host, port=cfg.flask.port, debug=True)
