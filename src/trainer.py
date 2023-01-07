import typing
import sklearn
import sklearn.feature_extraction
import numpy as np
from sklearn.pipeline import make_pipeline
import joblib


class ModelTrainer():
    def __init__(self, model_class: sklearn.base.BaseEstimator,
                 vectorizer: sklearn.feature_extraction.text.TfidfVectorizer,
                 model_params: dict,
                 load_model = False,
                 model_path=None,
                 ) -> None:
        """ Object of this class trains your model

        Args:
            model_class (class of sklearn.base.BaseEstimator): sklearn BaseEstimator-like class
            hyperparameters (dict): dictionary of hyperparameters for model
        """
        if load_model and model_path is None:
            raise AttributeError("No model path provided to load from")

        self.model_path = model_path
        self.params = model_params
        if load_model:
            self.pipeline = joblib.load(model_path)
        else:
            self.model = model_class(**self.model_params)
            self.pipeline = make_pipeline(vectorizer(), self.model)



    def fit(self, train_data: np.ndarray, train_target: np.array) -> None:
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

    def score(self, test_data: typing.Iterable, ground_truth: typing.Iterable) -> typing.DefaultDict():
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

    def save_model(self, path: str):
        joblib.dump(self.pipeline, path)
