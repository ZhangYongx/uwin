import tornado.ioloop
import tornado.web


class IndexHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        self.write("Hello world")


if __name__ == "__mian__":
    app = tornado.web.Application([
        (r"/", IndexHandler)
    ])

    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()

