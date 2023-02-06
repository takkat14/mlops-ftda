from typing import Iterable, Optional
import numpy as np
from sklearn.pipeline import make_pipeline
import joblib
from dao import MinioDAO, MongoDAO, MongoError
from omegaconf import DictConfig
import bson
import time


class ModelTrainer():
    def __init__(self, model_class,  # classname sklearn.base.BaseEstimator,
                 vectorizer,  # sklearn.feature_extraction.text.TfidfVectorizer
                 model_params: dict,
                 common_cfg: DictConfig,
                 load_model=False,
                 model_path=None,
                 model_type="linearSVC"
                 ) -> None:
        """ Object of this class trains your model

        Args:
            model_class (class of sklearn.base.BaseEstimator): classname
            hyperparameters (dict): dictionary of hyperparameters for model
        """
        self.common_cfg = common_cfg
        if load_model and model_path is None:
            raise AttributeError("No model path provided to load from")

        self.model_path = model_path
        self.params = model_params
        if load_model:
            self.pipeline = joblib.load(model_path)
        else:
            self.model = model_class(**self.params)
            self.pipeline = make_pipeline(vectorizer(), self.model)
        self.model_path_template = common_cfg.model[model_type].model_path_template
        self.model_type = model_type

    def fit(self, train_data: np.ndarray, train_target: np.ndarray) -> None:
        """ fit model

        Args:
            train_data (numpy.ndarray, numpy.ndarray): train feature table
            train_target (numpy.array): _description_
        """
        self.pipeline.fit(train_data, train_target)

    def predict(self, test_data: np.ndarray) -> None:
        """predict on trained model

        Args:
            test_data (np.ndarray): prediction feature table
        """
        return self.pipeline.predict(test_data)

    def score(self, test_data: Iterable, ground_truth: Iterable) -> dict:
        return {
            "accuracy": self.pipeline.score(test_data, ground_truth)
        }

    def get_model_params(self):
        """ Getter of params

        Returns:
            dict: dict of hyperparameters
        """
        return self.pipeline.get_params()

    def get_model(self):
        """Getter of model

        Returns:
            sklearn.base.BaseEstimator: init model
        """
        return self.pipeline

    def save_model(self, idx: Optional[str] = None):
        """_summary_

        Args:
            idx (str, optional): _description_. Defaults to None.

        Raises:
            MongoError: _description_
        """
        is_created = False if idx is None else True
        _id = str(bson.ObjectId()) if is_created else idx
        path = self.model_path_template.format(_id)
        
        joblib.dump(self.pipeline, path)

        bucket = self.common_cfg.minio.models_bucket
        minio_dao = MinioDAO(host=self.common_cfg.minio.host,
                             port=self.common_cfg.minio.port,
                             user=self.common_cfg.minio.root_user,
                             password=self.common_cfg.minio.root_password,
                             bucket=bucket)

        minio_dao.save_to_bucket(bucket, path, path)
        mongo_cfg = self.common_cfg.mongo
        mongo_dao = MongoDAO(mongo_cfg.host, mongo_cfg.port, mongo_cfg.dbname,
                             mongo_cfg.models_collection)

        found = mongo_dao.find_by_id(_id)
        createdTimeS = found["createdTimeS"] if found else time.time()

        metadata = {
            "minio_path": f"{bucket}/{path}",
            "model_type": self.model_type,
            "params": self.get_model_params(),
            "createdTimeS": createdTimeS,
            "updatedTimeS": time.time(),
        }
        if mongo_dao.upsert(_id, metadata) is None:
            raise MongoError(f"Upsert is failed for {_id}")

