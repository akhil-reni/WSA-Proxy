#!/usr/bin/env python3

from __future__ import absolute_import
import tempfile
import hashlib

class ProxyingRecorder(object):

    def __init__(self, fp, proxy_client, digest_algorithm='sha1', url=None):
        self.fp = fp
        # "The file has no name, and will cease to exist when it is closed."
        self.tempfile = tempfile.SpooledTemporaryFile(max_size=512*1024)
        self.digest_algorithm = digest_algorithm
        self.block_digest = hashlib.new(digest_algorithm)
        self.payload_offset = None
        self.proxy_client = proxy_client
        self._proxy_client_conn_open = bool(self.proxy_client)
        self.len = 0
        self.url = url

    def payload_starts_now(self):
        self.payload_offset = self.len

    def _update(self, hunk):
        self.block_digest.update(hunk)
        self.tempfile.write(hunk)

        if self.payload_offset is not None and self._proxy_client_conn_open:
            try:
                self.proxy_client.sendall(hunk)
            except BaseException as e:
                self._proxy_client_conn_open = False

        self.len += len(hunk)

    def read(self, size=-1):
        hunk = self.fp.read(size)
        self._update(hunk)
        return hunk

    def readinto(self, b):
        n = self.fp.readinto(b)
        self._update(b[:n])
        return n

    def readline(self, size=-1):
        # XXX depends on implementation details of self.fp.readline(), in
        # particular that it doesn't call self.fp.read()
        hunk = self.fp.readline(size)
        self._update(hunk)
        return hunk

    def flush(self):
        return self.fp.flush()

    def close(self):
        return self.fp.close()

    def __len__(self):
        return self.len

    def payload_size(self):
        if self.payload_offset is not None:
            return self.len - self.payload_offset
        else:
            return 0
        