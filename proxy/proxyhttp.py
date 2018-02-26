#!/usr/bin/env python3

from __future__ import absolute_import
import http.client 
from .proxyrecorder import ProxyingRecorder
from .viaheader import via_header_value
import hashlib


class ProxyingRecordingHTTPResponse(http.client.HTTPResponse):
    '''
    Implementation of HTTPResponse that uses a ProxyingRecorder to read the
    response from the remote web server and send it on to the proxy client,
    while recording the bytes in transit.
    '''
    def __init__(
            self, sock, debuglevel=0, method=None, proxy_client=None,
            digest_algorithm='sha1', url=None):
        http.client.HTTPResponse.__init__(
                self, sock, debuglevel=debuglevel, method=method)
        self.proxy_client = proxy_client
        self.url = url
        self.digest_algorithm = digest_algorithm

        # Keep around extra reference to self.fp because HTTPResponse sets
        # self.fp=None after it finishes reading, but we still need it
        self.recorder = ProxyingRecorder(
                self.fp, proxy_client, digest_algorithm, url=url)
        self.fp = self.recorder

        self.payload_digest = None
        
    def begin(self, extra_response_headers={}):
        http.client.HTTPResponse.begin(self)  # reads status line, headers

        status_and_headers = 'HTTP/1.1 {} {}\r\n'.format(
                self.status, self.reason)
        self.msg['Via'] = via_header_value(
                self.msg.get('Via'), '%0.1f' % (self.version / 10.0))
        if extra_response_headers:
            for header, value in extra_response_headers.items():
                self.msg[header] = value

        for k,v in self.msg.items():
            if k.lower() not in (
                    'connection', 'proxy-connection', 'keep-alive',
                    'proxy-authenticate', 'proxy-authorization', 'upgrade',
                    'strict-transport-security'):
                status_and_headers += '{}: {}\r\n'.format(k, v)
        status_and_headers += 'Connection: close\r\n\r\n'
        self.proxy_client.sendall(status_and_headers.encode('latin1'))

        self.recorder.payload_starts_now()
        self.payload_digest = hashlib.new(self.digest_algorithm)

    def read(self, amt=None):
        buf = http.client.HTTPResponse.read(self, amt)
        self.payload_digest.update(buf)
        return buf