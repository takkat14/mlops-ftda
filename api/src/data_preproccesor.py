# Here you can find anything related to data downloading and processing

import gdown  # Don't know better way to download dataset
from typing import List
import zipfile
import logging
import pandas as pd
from sklearn.model_selection import train_test_split
from omegaconf import DictConfig
from hydra.utils import to_absolute_path
import os
import numpy as np
from dao import MinioDAO


def get_train_test_data(cfg: DictConfig) -> List[np.ndarray]:
    minio_dao = MinioDAO(cfg.minio.host, cfg.minio.root_user,
                         cfg.minio.root_password, cfg.minio.server.port,
                         cfg.minio.datasets_bucket)
    data = minio_dao.get_from_bucket(cfg.minio.datasets_bucket,
                                     cfg.minio.minio_path)
    if data is None:
        out_path = to_absolute_path(cfg.dataset.out_path)
        if not os.path.exists(out_path):
            loader = DataLoader(cfg)
            loader.download()
        minio_dao.save_to_bucket(cfg.minio.datasets_bucket,
                                 cfg.minio.minio_path, out_path)

    s3_path = minio_dao.get_full_path(cfg.minio.datasets_bucket,
                                      cfg.minio.minio_path)
    preprocessor = TrainDataPreprocessor(s3_path)
    return preprocessor.prepare_data(cfg.dataset.train_size, cfg.dataset.seed)


class DataLoader():

    def __init__(self, cfg: DictConfig) -> None:
        """
        Initialize a DataLoader class
        :param path: str -- link of Google Drive file
        """
        self.cfg = cfg

    def download(self) -> None:
        """
        Download dataset
        :param unzip: bool -- whether to unzip file or not
        """
        try:
            path = self.cfg.dataset.out_path if not self.cfg.dataset.is_zip \
                                                else self.cfg.dataset.zip_path
            gdown.download(
                output=path, id=self.cfg.dataset.in_path)
        except BaseException as err:
            logging.error(
                f"Unable to download from {self.cfg.dataset.in_path},\
                 caught error", err)

        if self.cfg.dataset.is_zip:
            self._unzip()

    def _unzip(self) -> None:
        """
        Unzip file
        """
        out_dir = self.cfg.dataset.out_dir
        zip_path = self.cfg.dataset.zip_path
        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                target_file = ""
                for filename in z.namelist():
                    if filename.endswith(".csv") and \
                       not filename.startswith("__MACOSX"):  # cringe
                        target_file = filename
                print(target_file)
                z.extractall(path=out_dir)

        except BaseException as err:
            logging.error(f"Unable to unzip file {zip_path}", err)
            raise err
        os.rename(os.path.join(out_dir, target_file),
                  self.cfg.dataset.out_path)


class TrainDataPreprocessor():
    def __init__(self, path: str) -> None:
        self.path = path

    def prepare_data(self,
                     train_size: float = 0.75,
                     seed=0XDEAD) -> List[np.ndarray]:

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

        return train_test_split(df[['title&description']],
                                df['Category'],
                                train_size=train_size,
                                random_state=seed)  # type:ignore
