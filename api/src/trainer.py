from typing import Iterable, Optional
import numpy as np
from sklearn.pipeline import make_pipeline
import joblib
from api.src.dao import MinioDAO, MongoDAO, MongoError
from omegaconf import DictConfig
import bson
import time
from hydra.utils import instantiate
import tempfile


# Стырила из гиста:
# https://gist.github.com/ramhiser/28a4161de35b670a3e3b8a4dcb664bb0
def step_fullname(o):
    return o.__module__ + "." + o.__class__.__name__


class ModelTrainer():
    def __init__(self, model_class,  # classname sklearn.base.BaseEstimator,
                 vectorizer,  # sklearn.feature_extraction.text.TfidfVectorizer
                 model_params: dict,
                 common_cfg: DictConfig,
                 load_model=False,
                 model_obj=None,
                 model_type="linearSVC",
                 logger=None,
                 ) -> None:
        """ Object of this class trains your model

        Args:
            model_class (class of sklearn.base.BaseEstimator): classname
            hyperparameters (dict): dictionary of hyperparameters for model
        """
        self.common_cfg = common_cfg
        if load_model and model_obj is None:
            raise AttributeError("No model object provided to load from")

        self.params = model_params
        if load_model:
            self.pipeline = joblib.load(model_obj)
            self.params = self.pipeline.get_params()
        else:
            self.model = instantiate(model_class, **self.params)
            self.pipeline = make_pipeline(instantiate(vectorizer), self.model)
        if logger:
            self.logger = logger
            self.logger.warning("Made everything")
        self.model_path_template = common_cfg[model_type].model_path_template
        self.model_type = model_type

    def fit(self, train_data: np.ndarray, train_target: np.ndarray) -> None:
        """ fit model

        Args:
            train_data (numpy.ndarray, numpy.ndarray): train feature table
            train_target (numpy.array): _description_
        """
        if len(train_data.shape) > 1:
            _train_data = train_data.reshape(-1,)
        else:
            _train_data = train_data
        self.pipeline.fit(_train_data, train_target)

    def predict(self, test_data: np.ndarray) -> None:
        """predict on trained model

        Args:
            test_data (np.ndarray): prediction feature table
        """
        return self.pipeline.predict(test_data)

    def score(self, test_data: Iterable, ground_truth: Iterable) -> dict:
        if len(test_data.shape) > 1:  # type: ignore
            _test_data = test_data.reshape(-1,)  # type: ignore
        else:
            _test_data = test_data
        return {
            "accuracy": self.pipeline.score(_test_data, ground_truth)
        }

    def get_model_params(self):
        """ Getter of params

        Returns:
            dict: dict of hyperparameters
        """
        steps_obj = {'steps': []}
        for name, md in self.pipeline.steps:
            normal_params = {}
            params = md.get_params()
            for param in params:
                val = params[param]
                if not isinstance(val, str) or \
                   not isinstance(val, float) or not isinstance(val, int):
                    normal_params[param] = str(val)
                else:
                    normal_params[param] = val
            steps_obj['steps'].append({
                'name': name,
                'class_name': str(step_fullname(md)),
                'params': normal_params
            })

        return steps_obj

    def get_model(self):
        """Getter of model

        Returns:
            sklearn.base.BaseEstimator: init model
        """
        return self.pipeline

    def save_model(self, idx: Optional[str] = None, 
                   train_score=None, test_score=None):
        """_summary_

        Args:
            idx (str, optional): _description_. Defaults to None.

        Raises:
            MongoError: _description_
        """
        is_created = False if idx is not None else True
        _id = str(bson.ObjectId()) if is_created else idx
        path = self.model_path_template.format(_id)

        bucket = self.common_cfg.minio.models_bucket
        minio_dao = MinioDAO(host=self.common_cfg.minio.host,
                             port=self.common_cfg.minio.server_port,
                             user=self.common_cfg.minio.root_user,
                             password=self.common_cfg.minio.root_password,
                             bucket=bucket)

        with tempfile.NamedTemporaryFile() as fp:
            joblib.dump(self.pipeline, fp.name)
            minio_dao.save_to_bucket(bucket, path, fp.name)
        mongo_cfg = self.common_cfg.mongo
        mongo_dao = MongoDAO(mongo_cfg.host, mongo_cfg.port, mongo_cfg.dbname,
                             mongo_cfg.models_collection)

        found = mongo_dao.find_by_id(_id)
        createdTimeS = found["createdTimeS"] if found else time.time()

        metadata = {
            "minio_bucket": bucket,
            "minio_path": path,
            "model_type": self.model_type,
            "params": self.get_model_params(),
            "createdTimeS": createdTimeS,
            "updatedTimeS": time.time(),
            "train_score": train_score,
            "test_score": test_score
        }
        self.logger.warning(str(metadata))
        if mongo_dao.upsert(_id, metadata) is None:  # type: ignore
            raise MongoError(f"Upsert is failed for {_id}")
        return _id
