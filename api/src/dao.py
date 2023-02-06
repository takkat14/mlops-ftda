import pymongo
import bson
import minio
from minio.error import S3Error
from typing import Iterable, Optional, Any


class MongoError(Exception):
    def __init__(self, message):
        super().__init__(message)


class MinioError(Exception):
    def __init__(self, message):
        super().__init__(message)


class MongoDAO:

    def __init__(self, host: str, port: str, db: str, collection: str) -> None:
        """
        Basic class for data access in MongoDB.
        Args:
            address (str):  Mongo cluster address.
                            Example: mongodb://localhost:27017/
            db (str): Database name
            collection (str): Collection to access
        """
        self.address = f"mongodb://{host}/{port}",
        self.client = pymongo.MongoClient(self.address)
        self.db = self.client[db]
        self.collection = self.db[collection]

    def with_collection(self, collection: str) -> None:
        self.collection = self.db[collection]

    def find_by_id(self, _id: Any[str, None]) -> Optional[Any]:
        # Exception handling here
        if _id is None:
            return None
        return self.collection.find_one({"_id": bson.ObjectId(_id)})

    def remove_by_id(self, _id: str) -> None:
        self.collection.delete_one({"_id": bson.ObjectId(_id)})

    def _add(self, _id: str, document: dict) -> str:
        document["_id"] = bson.ObjectId(_id)
        new_item = self.collection.insert_one(document=document)
        return str(new_item.inserted_id)

    def _update(self, _id: str, new_document: dict):
        # Handle not found
        return self.collection.update_one({_id: bson.ObjectId(_id)},
                                          {"$set": new_document}).upserted_id

    # Я в курсе, что монга сама умеет в upsert, но не хочу
    def upsert(self, _id: str, document: dict):
        if self.find_by_id(_id) is None:
            return self._add(_id, document)
        return self._update(_id, document)

    def shutdown(self):
        self.client.close()

    def list_documents(self, limit=100):
        return self.collection.find(limit=limit)


class MinioDAO:
    def __init__(self, host: str, user: str, password: str,
                 port: str, bucket: str) -> None:

        self.host = host
        self.client = minio.Minio(f"{host}/{port}",
                                  access_key=user, secret_key=password)
        if not self.client.bucket_exists(bucket_name=bucket):
            self.client.make_bucket(bucket_name=bucket)
        self.port = port

    def list_bucket_items(self, bucket: str) -> Iterable[Any]:
        try:
            return self.client.list_objects(bucket_name=bucket)
        except S3Error as e:
            raise e

    def save_to_bucket(self, bucket: str, path_in_bucket: str,
                       path_to_save_from: str):
        return self.client.fput_object(bucket_name=bucket,
                                       object_name=path_in_bucket,
                                       file_path=path_to_save_from)

    def remove_from_bucket(self, bucket: str, path_in_bucket: str) -> None:
        self.client.remove_object(bucket_name=bucket,
                                  object_name=path_in_bucket)

    def get_from_bucket(self, bucket: str, path_in_bucket: str):
        response = None
        try:
            response = self.client.get_object(bucket_name=bucket,
                                              object_name=path_in_bucket)
        finally:
            if response is not None:
                response.close()
                response.release_conn()
        return response

    def get_full_path(self, bucket: str, path_in_bucket: str):
        if self.get_from_bucket(bucket, path_in_bucket) is None:
            raise MinioError(f"Not found {bucket}/{path_in_bucket}")
        return f"{self.host}/{self.port}/{bucket}/{path_in_bucket}"
