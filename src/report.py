# -*- coding: utf-8 -*-

import csv
from threading import Thread, Lock
from Queue import Queue
from collections import defaultdict
import urllib
import os.path

from api import SwistakApi


class LockingList(object):
    def __init__(self):
        self.lock = Lock()
        self.items = []

    def append(self, item):
        with self.lock:
            self.items.append(item)


class ReportData(object):

    def __init__(self, user, password):
        self.user = user
        self.api = SwistakApi(login=user, password=password)

    def get_data(self, from_date, threads_num=4):
        list_lock = LockingList()
        transactions = self.api.get_transactions_report(from_date)

        queue = Queue()
        for transaction in transactions:
            queue.put(transaction)

        self._create_threads(threads_num, queue, list_lock)

        queue.join()

        return list_lock.items

    def get_report_name(self, from_date):
        return u'{0}_{1}'.format(from_date.strftime('%Y-%m-%d'), self.user)

    def _create_threads(self, thread_num, queue, out_list):
        for _ in range(thread_num):
            worker = Thread(target=self._get_transaction, args=(queue, out_list))
            worker.setDaemon(True)
            worker.start()

    def _get_transaction(self, transaction, list_lock):
        while True:
            tt = transaction.get()
            out_data = {}
            try:
                trasaction_a = self.api.get_transactions([tt['id']])
                out_data['transaction'] = trasaction_a[0]
                out_data['auction'] = self.api.get_auctions([tt['id']])[0]
                list_lock.append(out_data)
            except Exception:
                pass
            transaction.task_done()


class Report(object):

    @classmethod
    def parse(cls, transaction_raw_list):
        out = defaultdict(dict)
        for transaction in transaction_raw_list:
            login = transaction['transaction']['customer_login']
            id = transaction['transaction']['id']
            out[login][id] = {}
            out[login][id]['id'] = transaction['transaction']['id']
            out[login][id]['item_sold_count'] = transaction['transaction']['item_sold_count']
            out[login][id]['price'] = transaction['transaction']['price']
            out[login][id]['title'] = transaction['auction']['title']
            out[login][id]['foto_url'] = transaction['auction']['fotos'][0]['url']
        return out

    @classmethod
    def create_report(cls, data, report_filename):
        pass

    @classmethod
    def download_images(cls, urls, location, thread_num=4):

        queue = Queue()

        def _download_image(urls_queue, location):
            while True:
                url = urls_queue.get()
                url_file_name = url.split('/')[-1]
                urllib.urlretrieve(url, "{0}/{1}".format(location, url_file_name))
                urls_queue.task_done()

        for _ in range(thread_num):
            worker = Thread(target=_download_image, args=(queue, location))
            worker.setDaemon(True)
            worker.start()

        for url in urls:
            queue.put(url)

        queue.join()


class CSVReport(Report):

    @classmethod
    def create_report(cls, data, report_filename):
        data = cls.parse(data)
        with open("{0}.csv".format(report_filename), 'w') as csvfile:
            writer_csv = csv.writer(csvfile, delimiter=';')
            writer_csv.writerow([u'Urzytkownik', 'aukcja', 'obraz', 'ilosc', 'cena', 'suma'])
            for o, v in data.items():
                writer_csv.writerow([o, '', '', '', '', ''])
                summ = 0
                count = 0
                for c, z in v.items():
                    writer_csv.writerow([
                        '',
                        u'{0}'.format(z['title']).encode('utf-8'),
                        z['foto_url'],
                        z['item_sold_count'],
                        z['price'],
                        '',
                    ])
                    count += z['item_sold_count']
                    summ += z['price']
                writer_csv.writerow(['', '', 'Razem: ', count, '', summ])


class HTMLReport(Report):
    @classmethod
    def create_report(cls, data, report_filename):
        data = cls.parse(data)
        with open("{0}.html".format(report_filename), 'w') as htmlfile:
            if not os.path.exists(report_filename):
                os.makedirs(report_filename)
            urls = [z['foto_url'] for d in data.values() for z in d.values()]
            cls.download_images(urls, report_filename)
            htmlfile.write("<html><head><style>td {padding: 10px;} img {width: 200px;}</style></head>")
            htmlfile.write("<body><table>"
                           "<tr ><td>Urzytkownik</td><td>aukcja</td><td>obraz</td><td>ilosc</td><td>cena</td><td>suma</td>"
                           )
            for o, v in data.items():
                htmlfile.write("<tr><td>{0}</td><td></td><td></td><td></td><td></td><td></td>".format(o))
                summ = 0
                count = 0
                for c, z in v.items():
                    url_file_name = z['foto_url'].split('/')[-1]
                    htmlfile.write(
                        "<tr><td></td>"
                        "<td>{0}</td>"
                        "<td><img src='{1}'/></td>"
                        "<td>{2}</td>"
                        "<td>{3}</td>"
                        "<td></td></tr>".format(
                            u'{0}'.format(z['title']).encode('utf-8'),
                            u'{0}/{1}'.format(report_filename, url_file_name),
                            z['item_sold_count'],
                            z['price']))
                    count += z['item_sold_count']
                    summ += z['price']
                htmlfile.write("<tr><td></td><td></td><td>Razem:</td><td>{0}</td><td></td><td>{1}</td>".format(count, summ))
            htmlfile.write("</tr>"
                           "</table></body></html>")

