import pymongo
import bson
import minio
from minio.error import ResponseError, S3Error
from typing import Iterable, List, Optional, Any


class MongoDAO:

    def __init__(self, address: str, db: str, collection: str) -> None:
        """
        Basic class for data access in MongoDB.
        Args:
            address (str):  Mongo cluster address.
                            Example: mongodb://localhost:27017/
            db (str): Database name
            collection (str): Collection to access
        """
        self.address = address
        self.client = pymongo.MongoClient(address)
        self.db = self.client[db]
        self.collection = self.db[collection]

    def find_by_id(self, _id: str) -> Optional[Any]:
        # Exception handling here
        return self.collection.find_one({"_id": bson.ObjectId(_id)})

    def remove_by_id(self, _id: str) -> None:
        self.collection.delete_one({"_id": bson.ObjectId(_id)})

    def add(self, document: dict) -> str:
        new_item = self.collection.insert_one(document=document)
        return str(new_item.inserted_id)

    def update(self, _id: str, new_document: dict):
        # Handle not found
        self.collection.update_one({_id: _id}, {"$set": new_document})

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
    
    def list_bucket_items(self, bucket: str) -> Iterable[Any]:
        try:
            return self.client.list_objects(bucket_name=bucket)
        except S3Error as e:
            raise e

    def save_to_bucket(self, bucket: str, path_in_bucket: str,
                                          path_to_save_from: str) -> None:
        self.client.fput_object(bucket_name=bucket, 
        object_name=path_in_bucket, file_path=path_to_save_from)

    def remove_from_bucket(self, bucket: str, path_in_bucket: str) -> None:
        self.client.remove_object(bucket_name=bucket,
                                  object_name=path_in_bucket)
    
    def get_from_bucket(self, bucket: str, path_in_bucket: str):
        return self.client.get_object(bucket_name=bucket,
                                      object_name=path_in_bucket)
