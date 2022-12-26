import typing
import sklearn
import numpy as np
from sklearn.preprocessing import make_pipeline


class ModelTrainer():
    def __init__(self, model_class: sklearn.base.BaseEstimator,
                 vectorizer: sklearn.feature_extraction.text.TfidfVectorizer, 
                 model_params: dict) -> None:
        """_summary_

        Args:
            model_class (class of sklearn.base.BaseEstimator): sklearn BaseEstimator-like class
            hyperparameters (dict): dictionary of hyperparameters for model
        """
        self.vectorizer = vectorizer
        self.params = model_params
        self.model = model_class(**self.model_params)
        self.pipeline = make_pipeline(self.vectorizer, self.model)

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
