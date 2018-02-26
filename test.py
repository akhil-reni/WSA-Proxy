from proxy.proxyhandler import WSAProxyHandler
from socketserver import ThreadingMixIn
from http.server import HTTPServer
import socket


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    # listening on IPv4 address
    address_family = socket.AF_INET


@staticmethod
def callback(request, response):
    # can handle the request and response
    pass



def startproxy(HandlerClass=WSAProxyHandler, ServerClass=ThreadingHTTPServer, protocol="HTTP/1.1", **kwargs):
    port = kwargs["port"]
    server_address = (kwargs["ip"], port)
    HandlerClass.callback = callback
    HandlerClass.protocol_version = protocol
    httpd = ServerClass(server_address, HandlerClass)
    sa = httpd.socket.getsockname()
    print("Serving HTTP on", sa[0], "port", sa[1], "...")
    httpd.serve_forever()

    
# change IP and port    
startproxy(ip='127.0.0.1', port=8888)



