from flask_restx import Api, Resource, fields
import os
from flask import jsonify
from api.src import dao
from api.src.dao import MongoDAO
from configurator import get_config
from bson import json_util
import json
from src.trainer import ModelTrainer
from src.data_preproccesor import get_train_test_data

def parse_json(data):
    return json.loads(json_util.dumps(data))


api = Api()
cfg = get_config()

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
            402: "Error while initializing model; \
            See description for more info",
            408: "Failed to reach DB"
        })
    def post(self):
        __type = api.payload["type"]
        __rawParams = api.payload["params"]

        try:
            classname = cfg.model[__type]
        except Exception as e:
            return {
                "status": "Failed",
                "message":
                "'type' error; Model type is unknown. Please, use 'linearSVC' or 'logreg'"
            }, 402

        try:
            __params = eval(__rawParams)
        except Exception as e:
            return {
                "status": "Failed",
                "message":
                "'params' error; Params must be a valid json or dict"
            }, 401

        try:
            dao = DAO(f"mongodb://{cfg.mongo.host}/{cfg.mongo.port}",
                  cfg.mongo.dbname,  cfg.mongo.models_collection)
            
        except Exception as e:
            return {
                "status": "Failed",
                "message": getattr(e, "message", repr(e))
            }, 408

        
        try:
            model_trainer = ModelTrainer(classname, cfg.model.tfidf, 
            model_params=__params, load_model=False, model_path=cfg.model[__type].model_path)
            X_train, X_test, y_train, y_test = get_train_test_data(cfg)
            model_trainer.fit(X_train, y_train)
            model_trainer.save_model(model_trainer.model_path)

            return {"status": "OK", "message": "Model created!"}, 201
        except Exception as e:
            raise
            return {
                "status": "Failed",
                "message": getattr(e, "message", repr(e))
            }, 402