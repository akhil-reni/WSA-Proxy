#!/usr/bin/env python3

from __future__ import absolute_import
import http.server 
import urllib.parse
import http.client 
import ssl
import socket
import time
import urlcanon
import gzip
import zlib
import os
from io import BytesIO
from .proxyhttp import ProxyingRecordingHTTPResponse
from .viaheader import via_header_value
from .parsehttp import GetRequest, GetResponse
from utils.createcert import CreateCert
import threading

ZIP_DECODERS = {'gzip', 'x-gzip'}


class WSAProxyHandler(http.server.BaseHTTPRequestHandler):
    
    def __init__(self, request, client_address, server):
        self.start_time = time.time()
        self.is_connect = False
        self._headers_buffer = []
        request.settimeout(10)  
        http.server.BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def _determine_host_port(self):
        # Get hostname and port to connect to
        if self.is_connect:
            host, self.port = self.path.split(':')
        else:
            self.url = self.path
            u = urllib.parse.urlparse(self.url)
            if u.scheme != 'http':
                raise Exception(
                        'unable to parse request %r as a proxy request' % (
                            self.requestline))
            host = u.hostname
            self.port = u.port or 80
            self.path = urllib.parse.urlunparse(
                urllib.parse.ParseResult(
                    scheme='', netloc='', params=u.params, path=u.path or '/',
                    query=u.query, fragment=u.fragment))
        self.hostname = urlcanon.normalize_host(host).decode('ascii')

    def _connect_to_remote_server(self):
        self._remote_server_sock = socket.socket()
        self._remote_server_sock.settimeout(10)
        self._remote_server_sock.connect((self.hostname, int(self.port)))

        # Wrap socket if SSL is required
        if self.is_connect:
            try:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self._remote_server_sock = context.wrap_socket(
                        self._remote_server_sock, server_hostname=self.hostname)
            except AttributeError:
                try:
                    self._remote_server_sock = ssl.wrap_socket(
                            self._remote_server_sock)
                except ssl.SSLError:
                    raise

        return self._remote_server_sock

    def _transition_to_ssl(self):
        dirpath = os.getcwd()
        dynamic_certdir = dirpath+'/certificates/dynamic/'
        epoch = "%d" % (time.time() * 1000)
        CreateCert(self.hostname, epoch)
        keyfile = dirpath+'/certificates/server.key'
        certpath = "%s/%s.crt" % (dynamic_certdir.rstrip('/'), self.hostname)
        self.request = self.connection = ssl.wrap_socket(
                self.connection, server_side=True, keyfile=keyfile, certfile=certpath)
        
    def do_CONNECT(self):
        self.is_connect = True
        try:
            self._determine_host_port()
            # If successful, let's do this!
            self.send_response(200, 'Connection established')
            self.end_headers()
            self._transition_to_ssl()
        except Exception as e:
            try:
                if type(e) is socket.timeout:
                    self.send_error(504, str(e))
                else:
                    self.send_error(500, str(e))
            except Exception as f:
                pass
            return

        # Reload!
        self.setup()
        self.handle_one_request()

    def _construct_tunneled_url(self):
        if int(self.port) == 443:
            netloc = self.hostname
        else:
            netloc = '{}:{}'.format(self.hostname, self.port)

        result = urllib.parse.urlunparse(
            urllib.parse.ParseResult(
                scheme='https',
                netloc=netloc,
                params='',
                path=self.path,
                query='',
                fragment=''
            )
        )

        return result

    def do_COMMAND(self):
        
        try:
            if self.is_connect:
                self.url = self._construct_tunneled_url()
            else:
                self._determine_host_port()
                assert self.url

            # Connect to destination
            self._connect_to_remote_server()
        except Exception as e:
            # limit enforcers have already sent the appropriate response
            return
        except Exception as e:
            self.send_error(500, str(e))
            return

        try:
            return self._proxy_request()
        except Exception as e:

            self.send_error(502, str(e))
            return

    @staticmethod
    def decode_content_body(encoded_data: "bytes", encoding: "str") -> "str":
        if encoding == 'identity':
            decoded_text = encoded_data
        elif encoding in ZIP_DECODERS:
            bytes_stream = BytesIO(encoded_data)
            with gzip.GzipFile(fileobj=bytes_stream) as io:
                decoded_text = io.read()
        elif encoding == 'deflate':
            try:
                decoded_text = zlib.decompress(encoded_data)
            except zlib.error:
                decoded_text = zlib.decompress(encoded_data, -zlib.MAX_WBITS)
        elif not encoding:
            decoded_text = encoded_data
        else:
            decoded_text = encoded_data
        return decoded_text
    
    def _proxy_request(self, extra_response_headers={}):
        # Build request
        req_str = '{} {} {}\r\n'.format(
                self.command, self.path, self.request_version)
        for key in (
                'Connection', 'Proxy-Connection', 'Keep-Alive',
                'Proxy-Authenticate', 'Proxy-Authorization', 'Upgrade'):
            del self.headers[key]
 
        self.headers['Via'] = via_header_value(
                self.headers.get('Via'),
                self.request_version.replace('HTTP/', ''))

        req_str += '\r\n'.join(
                '{}: {}'.format(k,v) for (k,v) in self.headers.items())

        req = req_str.encode('latin1') + b'\r\n\r\n'

        # Append message body if present to the request
        if 'Content-Length' in self.headers:
            req += self.rfile.read(int(self.headers['Content-Length']))

        prox_rec_res = None
        try:

            # Send it down the pipe!
            self._remote_server_sock.sendall(req)

            prox_rec_res = ProxyingRecordingHTTPResponse(
                    self._remote_server_sock, proxy_client=self.connection,
                    digest_algorithm='sha1',
                    url=self.url, method=self.command)
            prox_rec_res.begin(extra_response_headers=extra_response_headers)

            buf = prox_rec_res.read(65536)
            resdata = buf
            while buf != b'':
                buf = prox_rec_res.read(65536)
                resdata += buf

            self.log_request(prox_rec_res.status, prox_rec_res.recorder.len)
        finally:
            # Let's close off the remote end
            
            if prox_rec_res:
                prox_rec_res.close()
            self._remote_server_sock.close()
        data = ""
        try:
            data = self.decode_content_body(resdata, prox_rec_res.headers.get('Content-Encoding'))
        except Exception as e:
            print(e)
            pass
        self.end_time = time.time()
        time_taken = self.end_time - self.start_time
        thread = threading.Thread(target=self.handler, args=(req, self.url, prox_rec_res.headers, data, time_taken))
        thread.daemon = True              
        thread.start() 
        return req, prox_rec_res

    def __getattr__(self, item):
        if item.startswith('do_'):
            return self.do_COMMAND

    def handler(self, req, url, headers, data, time):
        request = GetRequest(req, url)
        response = GetResponse(headers, data, url, time)
        try:
            if self.callback:
                self.callback(request, response)
            else:
                pass
        except Exception as e:
            print(e)