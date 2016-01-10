from os.path import expanduser
import ConfigParser


class SwistakConfig(object):
    def __init__(self, file_name='config.ini'):
        self.file_name = file_name
        self.config = ConfigParser.ConfigParser()
        self.__create_if_not_exist()

    @property
    def accounts(self):
        raw_accounts = self.__read('Accounts')
        return {account[0]: account[1] for account in raw_accounts}

    def get_account(self, username):
        return self.__read('Accounts', username)

    def add_account(self, username, password):
        self.__set('Accounts', username, password)

    def del_account(self, username):
        self.__del('Accounts', username)

    def get_report_dir(self):
        return self.__read('Settings', 'Dir')

    def set_report_dir(self, path):
        self.__set('Settings', 'Dir', path)

    def del_report_dir(self):
        self.__del('Settings', 'Dir')

    def write(self):
        with open(self.file_name, 'w') as configfile:
            self.config.write(configfile)

    def __create_if_not_exist(self):
        _r = self.config.read(self.file_name)
        if not _r:
            self.config.add_section('Accounts')
            self.config.add_section('Settings')
            self.config.set('Settings', 'Dir', expanduser('~'))

    def __read(self, section, item=None):
        self.config.read(self.file_name)
        if not item:
            return self.config.items(section)
        return self.config.get(section, item)

    def __del(self, section, item):
        self.config.read(self.file_name)
        self.config.remove_option(section, item)

    def __set(self, section, item, value):
        self.config.read(self.file_name)
        self.config.set(section, item, value)
