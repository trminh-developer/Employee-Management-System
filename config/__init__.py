import pymysql
pymysql.install_as_MySQLdb()

# Monkey-patch Django's BaseContext for Python 3.14 compatibility
import django
from django.template.context import BaseContext

def _basecontext_copy(self):
    duplicate = object.__new__(type(self))
    duplicate.__dict__ = self.__dict__.copy()
    duplicate.dicts = self.dicts[:]
    return duplicate

BaseContext.__copy__ = _basecontext_copy
