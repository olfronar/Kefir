#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'olfronar'

import os
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado import gen
import asyncmongo,pymongo
import time
from random import randrange

from tornado.options import define, options

define("port", default=8001, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        self.db = asyncmongo.Client(pool_id='mydb', host='127.0.0.1', port=27017, maxcached=100, maxconnections=1000, dbname='kefir_test')
        handlers = [
            (r'/', Main),
            (r'/insert_data', Insert),
            (r'/test_data', Test),
            (r'/get_random_item', GetRandomItem)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'static'),
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class Main(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        conn = pymongo.Connection('127.0.0.1', 27017)
        db = conn['kefir_test']
        db_count = db.items.find().count()
        self.render("main_template.html", title="My title", message="", db_count = db_count)
        #self.finish()

class Insert(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.engine
    def post(self):
        try:
            count = int(self.get_argument("count"))
        except:
            message = "Incorrect count value"
            self.render("main_template.html", title="My title", message=message)
        if count > 1000000:
            message = "Ай-яй-яй"
            self.render("main_template.html", title="My title", message=message)
        self.application.db.items.remove(callback = (yield gen.Callback("removed")))
        remove_response = yield gen.Wait("removed")
        for x in xrange(0, count):
            self.application.db.items.save({'_id':x, 'val':randrange(0,count)}, callback = (yield gen.Callback("key")))
            response = yield gen.Wait("key")
        conn = pymongo.Connection('127.0.0.1', 27017)
        db = conn['kefir_test']
        db_count = db.items.find().count()
        self.render("main_template.html", title="My title", message="Done", db_count = db_count)
        #self.finish()

class Test(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.engine
    def post(self):
        try:
            count = int(self.get_argument("count"))
            repeat = int(self.get_argument("repeat"))
        except:
            message = "Incorrect count value"
            self.render("main_template.html", title="My title", message=message, db_count = count)
        if count > 1000000 or repeat > 5000:
            message = "Ай-яй-яй"
            self.render("main_template.html", title="My title", message=message, db_count = count)
        global_time = time.time()
        for x in xrange(0,repeat):
            target = randrange(0, count)
            self.application.db.items.find_one({'_id': target}, callback = (yield gen.Callback("key")))
            response,error = yield gen.Wait("key")
        global_time = time.time() - global_time
        global_count = repeat
        self.render("result_template.html", title="My title", message="Done",
            time = global_time, count = global_count, rps = global_count/float(global_time),
            mid_time = global_time/float(global_count))

class GetRandomItem(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        count = 100000
        target = randrange(0, count)
        self.application.db.items.find({'_id': target}, callback = (yield gen.Callback("key")))
        response,error = yield gen.Wait("key")
        self.write({"_id": response[0][0][u'_id'], "val": response[0][0][u'val']})
        self.finish()

def main():
    tornado.options.parse_command_line()
    application = Application()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
        main()