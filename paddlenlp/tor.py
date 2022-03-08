#!/usr/bin/env python
# encoding: utf-8

import tornado.ioloop
import tornado.web
import tornado.log
import tornado.httpserver
from tornado.options import define, options
import logging
import tornado.gen
import tornado.process
from paddlenlp import Taskflow

import re
import json
import sys
#sys.path.append("/Users/Lingyun/python/paddle/PaddleNLP/paddlenlp/")

#from paddlenlp.taskflow import Taskflow
#from paddlenlp import Taskflow

define('debug', type=bool, default=True, help="enable debug, default False")
define('host', type=str, default="127.0.0.1", help="http listen host, default 127.0.0.1")
define('port', type=int, default=8080, help="http listen port, default 8080")
define('dict', type=str, help="the path where your dict")
define('cuda', type=bool, default=False, help="enable or disable with CUDA")

options.parse_command_line()

logger = logging.getLogger('server')

class DictImport():

    def __init__(self):
        self.keyword_chains = {}

    def parse(self, path):
        with open(path) as f:
            for keyword in f:
                if not keyword:
                    coroutine
                keyword = keyword.lower()
                keyword = keyword.strip()
                self.keyword_chains[keyword] = 0
        return self.keyword_chains


di = DictImport()
dip = di.parse(options.dict)

class CheckHandler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def get(self):
        text = self.get_argument("text", None)
        text = ''.join(e for e in text if e.isalnum())
        text = text + "\n"
        seg = Taskflow("word_segmentation", use_cuda=options.cuda, user_redis=True)

        parse = seg(text)
        temp = {"拆分": parse}
        temp = json.dumps(temp, ensure_ascii=False)
        for i in parse:
            if i in dip:
                self.write(temp)
                return
        self.write(temp)


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r'/check', CheckHandler),
        ]

        settings = dict()
        settings['debug'] = True
        super(Application, self).__init__(handlers, **settings)

if __name__ == '__main__':
    application = Application()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(
        options.port,
        address=options.host
    )
    logger.info("http server listen on %s:%d", options.host, options.port)
    tornado.autoreload.start()
    #tornado.autoreload.watch(options.dict)
    tornado.ioloop.IOLoop.current().start()
    
