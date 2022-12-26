# Here you can find anything related to data downloading and processing

import gdown  # Don't know better way to download dataset
import typing
import zipfile
import logging
from hydra import initialize, compose
import pandas as pd
from sklearn.model_selection import train_test_split


def get_config():
    initialize(version_base=None, config_path="../configs")
    cfg = compose("config.yaml")
    return cfg


class DataLoader():
    cfg = get_config()

    def __init__(self, path: str = None, ) -> None:
        """
        Initialize a DataLoader class
        :param path: str -- link of Google Drive file
        """
        self.cfg.in_path = path

    @classmethod
    def download(cls, unzip: bool = False) -> None:
        """
        Download dataset
        :param unzip: bool -- whether to unzip file or not
        """
        try:
            path = cls.cfg.out_path if not cls.cfg.is_zip else cls.cfg.zip_path
            gdown.download(output=path, url=cls.cfg.in_path, fuzzy=True)
        except BaseException as err:
            logging.error(
                f"Unable to download from {cls.cfg.in_path}, caught error", err)

        if cls.cfg.is_zip and unzip:
            cls._unzip()

    @classmethod
    def _unzip(cls) -> None:
        """
        Unzip file
        """
        try:
            with zipfile.ZipFile(cls.cfg.zip_path) as z:
                z.extractall()
        except BaseException as err:
            logging.error(f"Unable to unzip file {cls.cfg.zip_path}", err)


class TrainDataPreprocessor():
    def __init__(self, path: str) -> None:
        self.path = path

    def prepare_data(self, train_size: float = 0.75, seed=0XDEAD) -> typing.Tuple(pd.DataFrame, pd.DataFrame, pd.Series, pd.Series):

        df = pd.read_csv(self.path)

        df.fillna("", inplace=True)

        if "title" not in df.keys():
            raise AttributeError("Not found 'title' in dataset columns")

        if "description" not in df.keys():
            raise AttributeError("Not found 'description' in dataset columns")
            
        if "Category" not in df.keys():
            raise AttributeError("Not found 'Category' in dataset columns")

        df['title&description'] = df['title'].str[:] + \
            ' \\\n' + df['description'].str[:]

        X_train, X_test, y_train, y_test = train_test_split(
            df[['title&description']], df['Category'], train_size=train_size, random_state=seed)
        return X_train, X_test, y_train, y_test
