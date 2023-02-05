from typing import Iterable
import numpy as np
from sklearn.pipeline import make_pipeline
import joblib
from dao import MinioDAO, MongoDAO


class ModelTrainer():
    def __init__(self, model_class,  # classname sklearn.base.BaseEstimator,
                 vectorizer,  # sklearn.feature_extraction.text.TfidfVectorizer
                 model_params: dict,
                 common_cfg: dict,
                 load_model=False,
                 model_path=None,
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

    def save_model(self, bucket: str, path: str):
        joblib.dump(self.pipeline, path)
        minio_dao = MinioDAO(self.common_cfg.minio.host,
                            self.common_cfg.minio.root_user, )
