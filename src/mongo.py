import os
import random
import subprocess
from typing import Union
from datetime import datetime
from pymongo import MongoClient
from .logger import Log
from . import LOG_LEVEL, LOG_FILE_DISABLE


logger = Log()
if LOG_LEVEL:
    logger.set_level(LOG_LEVEL)
if not LOG_FILE_DISABLE:
    logger.set_date_handler()
logger.set_msg_handler()


class MongoTool():

    def __init__(self, host: str, database: str, collection: str, dir_path: str, date: str = None) -> None:
        # mongo連線 匯入
        self.mongo = MongoClient(host)
        self.host = host
        self.database = database
        self.collection = collection
        self.dir_path = dir_path
        if date:
            self.date = date
        else:
            self.date = datetime.now().__format__('%Y%m%d')

        if not os.path.exists(f'{self.dir_path}/{self.date}'):
            os.makedirs(f'{self.dir_path}/{self.date}')

    def set_dir_path(self, dir_path: str):
        """設置 備份檔放置路徑

        Args:
            dir_path (str): 資料夾路徑
        """
        self.dir_path = dir_path

    def set_date(self, date: str):
        """設置 日期

        Args:
            date (str): 20230101
        """
        self.date = date

    def get_lastst_date(self, path: str) -> Union[dict, None]:
        """取得最新日期的資料夾名稱

        檔名格式 = '%Y%m%d'

        Args:
            path (str): 目標資料夾

        Returns:
            Union[dict, None]: _description_
        """
        date_dirs = os.listdir(path)
        format_date = '%Y%m%d'
        stock = {}
        for date in date_dirs:
            try:
                stock[datetime.strptime(date, format_date)] = date
            except Exception as err:
                logger.error(err, exc_info=True)
                return None
        return stock[max(stock.keys())]

    def dump(self) -> bool:
        """匯出

        Returns:
            bool: _description_
        """
        logger.info(f'匯出  {self.database} {self.collection} 至 {self.dir_path}/{self.collection}/{self.date}')
        command = f'mongodump --quiet -h {self.host} -d {self.database} -c {self.collection} -o {self.dir_path}/{self.collection}/{self.date}'
        logger.debug(f'指令:\n{command}')
        try:
            result = subprocess.run(command)
            stdout = result.stdout.decode("utf-8")
            stderr = result.stderr.decode("utf-8")
            if stdout:
                logger.debug(f'結果: {stdout}')
            if stderr:
                logger.error(f'錯誤: {stdout}')
        except Exception as err:
            logger.error(err, exc_info=True)
            return False
        return True

    def restore(self, name: str = None) -> bool:
        """匯入 mongo集合

        Args:
            name (str, optional): 備份後集合名稱. Defaults to None.

        Returns:
            _type_: _description_
        """
        if name:
            logger.info(f'匯入 {self.dir_path}/{self.database}/{self.collection}.bson 至 {self.database} {name}')
            command = f'mongorestore -h {self.host} -d {self.database} -c {name} {self.dir_path}/{self.database}/{self.collection}.bson'
        else:
            logger.info(f'匯入 {self.dir_path}/{self.database}/{self.collection}.bson 至 {self.database} {self.collection}')
            command = f'mongorestore -h {self.host} -d {self.database} -c {self.collection} {self.dir_path}/{self.database}/{self.collection}.bson'
        logger.debug(f'指令\n{command}')
        try:
            result = subprocess.run(command)
            stdout = result.stdout.decode("utf-8")
            stderr = result.stderr.decode("utf-8")
            if stdout:
                logger.debug(f'結果: {stdout}')
            if stderr:
                logger.error(f'錯誤: {stdout}')
        except Exception as err:
            logger.error(err, exc_info=True)
            return False
        return True

    def drop_collection(self) -> bool:
        '''移除collection'''
        try:
            logger.info(f'刪除 {self.database} {self.collection}')
            self.mongo[self.database][self.collection].drop()
        except Exception as err:
            logger.error(err, exc_info=True)
            return False
        return True

    def delete_all_document(self) -> bool:
        '''清空collection內所有資料'''
        try:
            logger.info(f'刪除 {self.database} {self.collection} 內所有資料')
            self.mongo[self.database][self.collection].delete_many({})
        except Exception as err:
            logger.error(err, exc_info=True)
            return False
        return True


class MongoRandomSample():

    def __init__(self, host: str, database: str, collection: str) -> None:
        """抽樣指定資料庫以及集合的資料,數量預設為200

        Args:
            db (str): 要抽取樣本的資料庫名稱
            collection (str): 要抽取樣本的集合名稱
        """
        self.sample_size = 200
        self.client = MongoClient(host)
        self.database = database
        self.collection = collection
        self.query = None

    def set_sample_size(self, size: int):
        """設置樣本數量

        Args:
            size (int): 指定數量
        """
        self.sample_size = size

    def set_query(self, **kwargs):
        self.query = kwargs

    def get_random_datas(self):
        """取得樣本

        Returns:
            list: mongo文件
        """
        if self.query:
            documents = list(self.client[self.db][self.collection].find(self.query))
        else:
            documents = list(self.client[self.db][self.collection].find())
        random_documents = random.sample(documents, min(len(documents), self.sample_size))
        return random_documents