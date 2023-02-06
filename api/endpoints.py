from flask_restx import Api, Resource, fields

from api.src.dao import MongoDAO
from configurator import get_config
from bson import json_util
import json
from api.src.trainer import ModelTrainer
from api.src.data_preproccesor import get_train_test_data
from logger import create_logger


def parse_json(data):
    return json.loads(json_util.dumps(data))


api = Api()
cfg = get_config()
logger = create_logger()




@api.route("/models/list")
class ModelList(Resource):
    @api.doc(responses={201: "Success"})
    def get(self):
        dao = MongoDAO(cfg.mongo.host, cfg.mongo.port,
                       cfg.mongo.dbname,  cfg.mongo.models_collection)
        models = dao.list_documents()
        result = list(models)
        dao.shutdown()
        return parse_json(result), 201


model_add = api.model(
    "Model.add.input", {
        "type":
        fields.String(required=True,
                      title="Model type",
                      description="Must be 'logreg' or 'linearSVC';",
                      default="linearSVC",
                      ),
        "params":
        fields.String(
            required=True,
            title="Model params",
            description="Params to use in model init; Must be valid dict;",
            default="{'C': 0.5}")
    })


@api.route("/models/add")
class ModelAdd(Resource):
    @api.expect(model_add)
    @api.doc(
        responses={
            201: "Success",
            400: "Unable to init model",
            401: "Model fitting issue",
            404: "Unable to get data",
            408: "Failed to reach DB"
        })
    def post(self):
        __type = api.payload["type"]
        __rawParams = api.payload["params"]

        try:
            classname = cfg[__type].model
            vectorizer = cfg[__type].tfidf
            print(cfg)
        except Exception as e:
            return {
                "status": "Failed",
                "message": getattr(e, "message", repr(e))
            }, 400

        try:
            __params = eval(__rawParams)
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Bad request. Params should be valid dict. Original message: " + getattr(e, "message", repr(e))
            }, 400

        try:
            model_trainer = ModelTrainer(classname, vectorizer,
                                         model_params=__params,
                                         load_model=False,
                                         model_path=None,
                                         common_cfg=cfg,
                                         logger=logger)
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Unable to init trainer. Original message: " + getattr(e, "message", repr(e))
            }, 401
        
        try:
            X_train, X_test, y_train, y_test = get_train_test_data(cfg)
            model_trainer.fit(X_train.values, y_train)
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Error occured while fitting. Original message: " +
                getattr(e, "message", repr(e))
            }, 401
        try:
            _id = model_trainer.save_model(model_trainer.model_path)
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Error occured while saving. Original message: " +
                getattr(e, "message", repr(e))
            }, 408

        test_score = model_trainer.score(X_test.values, y_test)
        train_score = model_trainer.score(X_train.values, y_train)
        return {"status": "OK",
                "message": f"""Model created!
                Test accuracy is {test_score["accuracy"]}!
                Train accuracy is {train_score["accuracy"]}!
                Model _id is {_id}
                """}, 201
