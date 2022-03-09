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
import redis

from paddlenlp import TriedTree

def redisWords():
    pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0, decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    return r



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
rcon = redisWords()

'''
class TriedTree(object):
    """Implementataion of TriedTree
    """

    def __init__(self):
        self.tree = {}

    def add_word(self, word):
        """add single word into TriedTree"""
        self.tree[word] = len(word)
        for i in range(1, len(word)):
            wfrag = word[:i]
            self.tree[wfrag] = self.tree.get(wfrag, None)

    def search(self, content):
        """Backward maximum matching

        Args:
            content (str): string to be searched
        Returns:
            List[Tuple]: list of maximum matching words, each element represents 
                the starting and ending position of the matching string.
        """
        result = []
        length = len(content)
        for start in range(length):
            for end in range(start + 1, length + 1):
                pos = self.tree.get(content[start:end], -1)
                if pos == -1:
                    break
                if pos and (len(result) == 0 or end > result[-1][1]):
                    result.append((start, end))
        return result


'''

class RedisCustomization(object):
    """
    User intervention based on Aho-Corasick automaton
    """

    def __init__(self):
        self.dictitem = {}
        self.ac = None

    def load_customization_redis(self, conn, sep=None):
        self.ac = TriedTree()
        # rw = redisWords()
        #print("--+-->", conn.smembers("words"))
        for line in conn.smembers("words"):
            print("line: ", line)
            if sep == None:
                words = line.strip().split()
            else:
                sep = strdecode(sep)
                words = line.strip().split(sep)

            if len(words) == 0:
                continue
            print("words: ", words)
            phrase = ""
            tags = []
            offset = []
            for word in words:
                print("word.rfind('/'): ", word.rfind('/'))
                if word.rfind('/') < 1:
                    phrase += word
                    tags.append('')
                else:
                    phrase += word[:word.rfind('/')]
                    tags.append(word[word.rfind('/') + 1:])
                offset.append(len(phrase))
                print("phrase: ", phrase)
            print("phrase+: ", phrase)
            if len(phrase) < 2 and tags[0] == '':
                continue
            print("tags: ", tags, "offset: ", offset)
            self.dictitem[phrase] = (tags, offset)
            print("self.dictitem: ", self.dictitem)
            print("---->phrase: ", phrase)
            self.ac.add_word(phrase)
            print("self.ac: ", self.ac.__dict__)


        return self


    def parse_customization(self, query, lac_tags, prefix=False):
        """Use custom vocab to modify the lac results"""
        if not self.ac:
            logging.warning("customization dict is not load")
            return
        ac_res = self.ac.search(query)
        print("query:", query, "lac_tags: ", lac_tags)
        print("self.ac: ", self.ac.__dict__, " ac_res: ", ac_res)
        for begin, end in ac_res:
            phrase = query[begin:end]
            index = begin

            tags, offsets = self.dictitem[phrase]

            if prefix:
                for tag, offset in zip(tags, offsets):
                    while index < begin + offset:
                        if len(tag) == 0:
                            lac_tags[index] = "I" + lac_tags[index][1:]
                        else:
                            lac_tags[index] = "I-" + tag
                        index += 1
                lac_tags[begin] = "B" + lac_tags[begin][1:]
                for offset in offsets:
                    index = begin + offset
                    if index < len(lac_tags):
                        lac_tags[index] = "B" + lac_tags[index][1:]
            else:
                for tag, offset in zip(tags, offsets):
                    while index < begin + offset:
                        if len(tag) == 0:
                            lac_tags[index] = lac_tags[index][:-1] + "I"
                        else:
                            lac_tags[index] = tag + "-I"
                        index += 1
                lac_tags[begin] = lac_tags[begin][:-1] + "B"
                for offset in offsets:
                    index = begin + offset
                    if index < len(lac_tags):
                        lac_tags[index] = lac_tags[index][:-1] + "B"

_custom = RedisCustomization()
_custom.load_customization_redis(rcon)

#print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%", _custom.__dict__, _custom.ac.__dict__)

seg = Taskflow("word_segmentation", use_cuda=options.cuda, user_redis=True, connect=rcon)


class CheckHandler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def get(self):
        text = self.get_argument("text", None)
        text = ''.join(e for e in text if e.isalnum())
        text = text + "\n"
        #seg = Taskflow("word_segmentation", use_cuda=options.cuda, user_redis=True, connect=rcon)
        #print(seg.task_instance)
        #reload(seg)
        #print("old: ======================", seg.task_instance._custom)
        #print("new: ======================", seg.__dict__)
        #seg.WordSegmentationTask()
        seg.task_instance._custom = _custom.load_customization_redis(rcon)
        print("_custom.load_customization_redis(rcon): ", _custom.load_customization_redis(rcon))
        #print(",,,,,,,,,,,,,,,,,,,,,", seg.task_instance._custom)
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
    
