#!/usr/bin/env python3
# coding: utf-8

from __future__ import absolute_import
import http.server 
from io import BytesIO
from urllib.parse import urlsplit, urlparse, parse_qs
import json
from http.cookies import SimpleCookie


class ParseCookie:
    def __init__(self, cookie):
        self.cookie = cookie
        self.base_list = []
        self.flat_list =[]
        self.parsed = {}
        self.parse()
    
    def parse(self):
        self.base_list.append(self.cookie.split(";"))
        self.flat_list = [item for sublist in self.base_list for item in sublist]
        for i in self.flat_list:
            y = i.split("=")
            try:
                if y[1]:
                    self.parsed[y[0].strip()] = y[1]
            except:
                self.parsed[y[0].strip()] = ""
        del y
    
    def expires(self):
        if 'expires' in self.parsed:
            return self.parsed['expires']
        return False
    
    def path(self):
        if 'path' in self.parsed:
            return self.parsed['path']
        return False
    
    def comment(self):
        if 'comment' in self.parsed:
            return self.parsed['comment']
        return False
    
    def domain(self):
        if 'domain' in self.parsed:
            return self.parsed['domain']
        return False
    
    def name(self):
        name, value=self.flat_list[0].split("=")
        return name
    
    def value(self):
        name, value=self.flat_list[0].split("=")
        return value
    
    def secure(self):
        if 'secure' in self.parsed:
            return True
        return False
    
    def http(self):
        if 'httponly' in self.parsed:
            return True
        return False
    
    def version(self):
        if 'version' in self.parsed:
            return True
        return False
        

class ParseHTTP(http.server.BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = BytesIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message


class GetRequest:
    def __init__(self, request, url):
        o = urlparse(url)
        self.url = o.scheme + "://" + o.netloc + o.path
        self.raw = str(request.decode("utf-8"))
        request = ParseHTTP(request)
        body = request.rfile.read().decode()

        self.headers = request.headers
        if "cookies" in self.headers:
            cookie = SimpleCookie()
            cookie.load(self.headers["cookies"])
            if cookie:
                cookies = {}
                for key, morsel in cookie.items():
                    cookies[key] = morsel.value
                self.cookies = cookies
                del self.headers["cookies"]
        else:
            self.cookies = False
        query = parse_qs(urlsplit(url).query, keep_blank_values=True)
        if query:
            self.params = query
        else:
            self.params = False
        if body:
            try:
                self.body = json.loads(body)
                self.json = True
            except Exception as e:
                self.json = False
                self.body = parse_qs(body, keep_blank_values=True)
        else:
            self.body = False
            self.json = False
        self.method = request.command
        self.host = self.headers['host']

    def request(self):
        return self


class GetResponse:
    def __init__(self, response, response_body, url, time):
        self.time = time
        self.headers = response
        self.cookies = []
        if self.headers.get_all('set-cookie'):
            for cookie in self.headers.get_all('set-cookie'):
                x = ParseCookie(cookie)
                self.cookies.append(x)
        else:
            self.cookies = self.headers.get_all('set-cookie')
        if response.get_content_charset():
            try:
                self.text = response_body.decode(response.get_content_charset(), 'ignore')
            except:
                self.text = response_body
        else:
            self.text = response_body
        self.url = url
        

    def response(self):
        return self

