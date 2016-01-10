# -*- coding: utf-8 -*-
import suds

import logging
logging.basicConfig(level=logging.ERROR)


class SwistakApi(object):
    __slots__ = ['_login', '_password', '__client']

    URL = 'http://www.swistak.pl/out/wsdl/wsdl.html?wsdl'

    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.__client = suds.client.Client(self.URL)

    @property
    def login(self):
        return self._login

    @login.setter
    def login(self, login):
        self._login = login

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = password

    def get_hash(self):
        return self.__client.service.get_hash(**{'login': self._login, 'pass': self._password})

    def get_transactions_report(self, date_time):
        """
        :param time: python datatime object
        :return: list
        """
        import time
        date_in_unix = time.mktime(date_time.timetuple())
        return self.__client.service.get_transactions_report(**{'hash': self.get_hash(), 'time': date_in_unix})

    def get_transactions(self, ids=None, ids_out=None):
        if not ids and not ids_out:
            raise Exception("Ids or Ids_out required")
        return self.__client.service.get_transactions(**{'hash': self.get_hash(), 'ids': ids})

    def get_auctions(self, ids):
        return self.__client.service.get_auctions(**{'hash': self.get_hash(), 'ids': ids})

    def get_id_by_login(self, login):
        return self.__client.service.get_id_by_login(**{'hash': self.get_hash(), 'login': login})

    def get_unit(self):
        return self.__client.service.get_unit()

    def get_delivery_info(self):
        return self.__client.service.get_delivery_info()

    def get_province(self):
        return self.__client.service.get_province()
