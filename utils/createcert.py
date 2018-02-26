#!/usr/bin/env python3

from __future__ import absolute_import
from OpenSSL import crypto, SSL
from .gencert import create_self_signed_cert
from pathlib import Path
import os

class CreateCert:
    dirpath = os.getcwd()

    def __init__(self, hostname, serial):
        self.hostname = hostname
        req = self.create_req()
        self.createCertificate(req, serial)
        
    def create_req(self):
        if not os.path.exists(self.dirpath+"/certificates"):
            os.makedirs(self.dirpath+"/certificates")
        keyfile = Path(self.dirpath+"/certificates/server.key")
        if not keyfile.is_file():
            create_self_signed_cert()
        pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, open(self.dirpath+"/certificates/server.key", 'rb').read())
        req = crypto.X509Req()
        subj = req.get_subject()
        name = {}
        name = {"CN": self.hostname}
        for key, value in name.items():
            setattr(subj, key, value)

        req.set_pubkey(pkey)
        req.sign(pkey, "sha256")
        return req

    def createCertificate(self, req, serial, digest="sha256"):
        if not os.path.exists(self.dirpath+"/certificates/dynamic"):
            os.makedirs(self.dirpath+"/certificates/dynamic")
        issuerCert = crypto.load_certificate(crypto.FILETYPE_PEM, open(self.dirpath+"/certificates/ca.crt", 'rb').read())
        issuerKey = crypto.load_privatekey(crypto.FILETYPE_PEM, open(self.dirpath+"/certificates/ca.key", 'rb').read())
        cert = crypto.X509()
        cert.set_serial_number(int(serial))
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)
        cert.set_issuer(issuerCert.get_subject())
        cert.set_subject(req.get_subject())
        cert.set_pubkey(req.get_pubkey())
        cert.sign(issuerKey, digest)
        open(self.dirpath+"/certificates/dynamic/"+self.hostname+".crt", "wb").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        return cert

