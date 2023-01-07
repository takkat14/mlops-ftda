from flask import Flask
from flask_restx import Resource, Api, reqparse, fields
from src.data_preproccesor import get_train_test_data
import src.trainer
import os
from hydra import initialize, compose
from hydra.utils import to_absolute_path

# TODO: let's think about asyncronious behaviour


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

@api.route("/models/add")
class ModelAdd(Resource):
    @api.expect(model_add)
    @api.doc(
        responses={
            201: "Success",
            401: "'params' error; Params must be a valid json or dict",
            402:
            "Error while initializing model; See description for more info",
            403: "Model with a given name already exists",
            408: "Failed to reach DB"
        })
    def post(self):
        __name = api.payload["name"]
        __type = api.payload["type"]
        __rawParams = api.payload["params"]

        try:
            __params = eval(__rawParams)
        except Exception as e:
            return {
                "status": "Failed",
                "message":
                "'params' error; Params must be a valid json or dict"
            }, 401

        try:
            __modelsList = get_existing_models()
        except Exception as e:
            return {
                "status": "Failed",
                "message": getattr(e, "message", repr(e))
            }, 408

        if __name not in __modelsList:
            try:
                __model = Model(model_type=__type, model_args=__params)
                __weights = BytesIO()
                pickle.dump(__model, __weights)
                __weights.seek(0)

                engine_postgres = create_engine(POSTGRES_CONN_STRING)
                engine_postgres.execution_options(autocommit=True).execute(
                    f"""
                    INSERT INTO public.models ("modelName", "modelType", "modelParams", "weights")
                    VALUES (%s,%s,%s,%s);
                    """,
                    (__name, __type, __rawParams, psycopg2.Binary(__weights.read()))
                )
                engine_postgres.dispose()

                return {"status": "OK", "message": "Model created!"}, 201
            except Exception as e:
                raise
                return {
                    "status": "Failed",
                    "message": getattr(e, "message", repr(e))
                }, 402
        else:
            return {
                "status": "Failed",
                "message": "Model with a given name already exists"
            }, 403



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


# @app.route("/models/add")
# def train():
#     X_train, X_test, y_train, y_test = get_train_test_data(cfg)
#     return 200


if __name__ == "__main__":
    app.run(host=cfg.flask.host, port=cfg.flask.port, debug=True)
