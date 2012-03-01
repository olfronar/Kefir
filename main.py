#!/usr/bin/env python
__author__ = 'olfronar'

import os
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import asyncmongo

from tornado.options import define, options

define("port", default=8001, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        self.db = asyncmongo.Client(pool_id='mydb', host='127.0.0.1', port=27017, maxcached=10, maxconnections=50, dbname='kefir_test')
        handlers = [
            (r'/', Main),
            (r'/insert_data', Insert)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'static'),
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class Main(tornado.web.RequestHandler):
    def get(self):
        self.render("main_template.html", title="My title")

class Insert(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.application.db.messages.find({}, limit=50, sort=[('time', -1)], callback=self.on_response)

    def on_response(self, response, error):
        if error:
            raise tornado.web.HTTPError(500)
        self.render('index.html', message=response)


def main():
    tornado.options.parse_command_line()
    application = Application()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
        main()