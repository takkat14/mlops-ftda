from flask_restx import Api, Resource, fields

from api.src.dao import MinioDAO, MongoDAO
from configurator import get_config
from bson import json_util
import json
from api.src.trainer import ModelTrainer
from api.src.data_preproccesor import get_train_test_data
from logger import create_logger
import numpy as np


def parse_json(data):
    return json.loads(json_util.dumps(data))


api = Api(version='1.0', title="MLOps sucker",
          description="takkat's fancy MLOps API")
logger = create_logger()
cfg = get_config()
logger.warning(cfg)


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


model_predict = api.model(
    "Model.predict.input", {
        "text":
        fields.String(required=True,
                      title="Input text",
                      description="Text in Russian to predict on;",
                      default="Продается отличный гараж!!!",
                      ),
    })


@api.route("/models/add")
class ModelAdd(Resource):
    @api.expect(model_add)
    @api.doc(
        responses={
            201: "Success",
            400: "Unable to init model",
            401: "Model fitting/scoring issue",
            404: "Unable to get data",
            408: "Failed to reach DB"
        })
    def post(self):
        __type = api.payload["type"]  # type:ignore
        __rawParams = api.payload["params"]  # type:ignore

        try:
            classname = cfg[__type].model
            vectorizer = cfg[__type].tfidf
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
                "message": "Bad request. Params should be valid dict. \
                Original message: "
                + getattr(e, "message", repr(e))
            }, 400

        try:
            model_trainer = ModelTrainer(classname, vectorizer,
                                         model_params=__params,
                                         load_model=False,
                                         model_obj=None,
                                         common_cfg=cfg,
                                         logger=logger)
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Unable to init trainer. Original message: "
                + getattr(e, "message", repr(e))
            }, 401

        try:
            X_train, X_test, y_train, y_test = get_train_test_data(cfg)
            model_trainer.fit(X_train.values, y_train)  # type:ignore
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Error occured while fitting. Original message: " +
                getattr(e, "message", repr(e))
            }, 401

        try:
            test_score = model_trainer.score(X_test.values, y_test)  # type:ignore
            train_score = model_trainer.score(X_train.values, y_train)  # type:ignore
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Error occured while scoring. Original message: " +
                getattr(e, "message", repr(e))
            }, 401

        try:
            _id = model_trainer.save_model(None,
                                           train_score, test_score)
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Error occured while saving. Original message: " +
                getattr(e, "message", repr(e))
            }, 408

        return {"status": "OK",
                "message": "Model created!",
                "test_accuracy": test_score["accuracy"],
                "train_accurcy": train_score["accuracy"],
                "model_id": _id,
                }, 201


@api.route("/models/<_id>/remove")
@api.doc(params={'_id': 'Model ID'})
class ModelRemove(Resource):
    @api.doc(
        responses={
            201: "Success",
            404: "Unable to get data by ID",
            401: "Unable to handle object in DB",
            408: "Failed to reach DB"
        })
    def post(self, _id):
        try:
            mongo_cfg = cfg.mongo
            mongo_dao = MongoDAO(mongo_cfg.host, mongo_cfg.port,
                                 mongo_cfg.dbname,
                                 mongo_cfg.models_collection)
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Error occured while DB reaching. Original message: " +
                getattr(e, "message", repr(e))
            }, 408

        try:
            doc = mongo_dao.find_by_id(_id)
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Error occured while Mongo reaching. Original message: " +
                getattr(e, "message", repr(e))
            }, 408
        if doc is None:
            return {
                "status": "Failed",
                "message": "Not found any model by provided ID"
            }, 404

        try:
            bucket = cfg.minio.models_bucket
            minio_cfg = cfg.minio
            minio_dao = MinioDAO(host=minio_cfg.host,
                                 port=minio_cfg.server_port,
                                 user=minio_cfg.root_user,
                                 password=minio_cfg.root_password,
                                 bucket=bucket)
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Error occured while MinIO reaching. \
                Original message: " +
                getattr(e, "message", repr(e))
            }, 408

        try:
            minio_dao.remove_from_bucket(bucket=bucket, path_in_bucket=doc["minio_path"])
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Error occured while removing from MinIO. \
                Original message: " +
                getattr(e, "message", repr(e))
            }, 401

        try:
            mongo_dao.remove_by_id(_id)
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Error occured while removing from Mongo. \
                Original message: " +
                getattr(e, "message", repr(e))
            }, 401

        return {
            "status": "OK",
            "message": "Model succesfully removed!",
        }, 201


@api.route("/models/<_id>/predict")
@api.doc(params={'_id': 'Model ID'})
class ModelPredict(Resource):
    @api.expect(model_predict)
    @api.doc(
        responses={
            201: "Success",
            400: "Unable to init model",
            401: "Model prediction issue",
            404: "Unable to get data",
            408: "Failed to reach DB"
        })
    def post(self, _id):
        text = api.payload["text"]  # type:ignore
        try:
            mongo_cfg = cfg.mongo
            mongo_dao = MongoDAO(mongo_cfg.host, mongo_cfg.port,
                                 mongo_cfg.dbname,
                                 mongo_cfg.models_collection)
            doc = mongo_dao.find_by_id(_id)
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Error occured while Mongo reaching. \
                 Original message: " +
                getattr(e, "message", repr(e))
            }, 408
        if doc is None:
            return {
                "status": "Failed",
                "message": "Not found any model by provided ID"
            }, 404
        try:
            # Можно, конечно, достать из монги все,
            # Я просто люблю страдать
            model_cfg = cfg[doc["model_type"]]
            classname = model_cfg.model
            vectorizer = model_cfg.tfidf
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Error occured while config init. \
                 Original message: " +
                getattr(e, "message", repr(e))
            }, 400

        try:
            bucket = cfg.minio.models_bucket
            minio_cfg = cfg.minio
            minio_dao = MinioDAO(host=minio_cfg.host,
                                 port=minio_cfg.server_port,
                                 user=minio_cfg.root_user,
                                 password=minio_cfg.root_password,
                                 bucket=bucket)
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Error occured while MinIO reaching. \
                Original message: " +
                getattr(e, "message", repr(e))
            }, 408

        try:
            obj = minio_dao.get_from_bucket(bucket=bucket, path_in_bucket=doc["minio_path"])
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Error occured while getting model from MinIO. \
                Original message: " +
                getattr(e, "message", repr(e))
            }, 404

        try:
            model_trainer = ModelTrainer(classname, vectorizer,
                                         model_params=None,
                                         load_model=True,
                                         model_obj=obj,
                                         common_cfg=cfg,
                                         logger=logger)
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Unable to init trainer. Original message: "
                + getattr(e, "message", repr(e))
            }, 400
        try:
            prediction = model_trainer.predict(np.array([text]))
        except Exception as e:
            return {
                "status": "Failed",
                "message": "Unable to predict for text. Original message: "
                + getattr(e, "message", repr(e))
            }, 401
        if len(prediction) < 1:
            return {
                "status": "Failed",
                "message": "Model made no predictions"
            }, 401
        return {
            "status": "OK",
            "message": "Model succesfully predicted!",
            "prediction": str(prediction[0]),
        }, 201
