#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'olfronar'

import os
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado import gen
import asyncmongo
from random import randrange

from tornado.options import define, options

define("port", default=8001, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        self.db = asyncmongo.Client(pool_id='mydb', host='127.0.0.1', port=27017, maxcached=10, maxconnections=1000001, dbname='kefir_test')
        handlers = [
            (r'/', Main),
            (r'/insert_data', Insert),
            (r'/test_data', Test)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'static'),
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class Main(tornado.web.RequestHandler):
    def get(self):
        self.render("main_template.html", title="My title", message="")
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
        keys = []
        big_count = count / 200
        small_count = count % 200
        for y in xrange(0,big_count):
            keys = []
            for x in xrange(0, 200):
                keys.append("key"+str(x))
                self.application.db.items.save({'_id':x+y*200, 'val':randrange(0,count)}, callback = (yield gen.Callback("key"+str(x))))
            response = yield gen.WaitAll(keys)
        keys = []
        for x in xrange(0, small_count):
            keys.append("key"+str(x))
            self.application.db.items.save({'_id':x+big_count*200, 'val':randrange(0,count)}, callback = (yield gen.Callback("key"+str(x))))
        response = yield gen.WaitAll(keys)
        self.render("main_template.html", title="My title", message="Done")
        #self.finish()

class Test(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.application.db.messages.find({}, limit=50, sort=[('time', -1)], callback=self.on_response)

    def on_response(self, response, error):
        if error:
            raise tornado.web.HTTPError(500)
        self.render('index.html', message=response)
        #self.finish()


def main():
    tornado.options.parse_command_line()
    application = Application()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
        main()