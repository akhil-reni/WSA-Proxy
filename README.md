# WSA-Proxy
A HTTP(S) proxy built in python 3

# Features

- Easy to use
- Supports both IPv4 and IPv6
- Supports generating dynamic SSL certificates
- Parse requests and respones

# Requirements

- Python3
- pyOpenSSL


# Usage 

- ```pip3 install -r requirements.txt```
- ```python3 test.py```

By default the proxy will be running on 127.0.0.1:8888
To change the port or IP edit the test.py file and change the below code
```
startproxy(ip='<ip>', port=<port_no>)
```

To intercept HTTPS traffic, make sure to trust the ca.crt, which will be generated in certificates once you run the code. And all dynamic certificates will be generated in certicates/dynamic/ folder.

# API Reference

If you want to access the request and response, you can customize the callback code in test.py file

```
def callback(request, response):
    # can handle the request and response
    pass
```

#### Supported Request Functions
- ```request.headers``` :  Returns a dictonary of request headers
- ```request.parms``` :  Returns a dictonary of query parameters or False 
- ```request.body``` :  Returns a dictonary of post body parameters or False 
- ```request.json``` :  Returns True or False to let you know if the request.body are query parameters or JSON
- ```request.cookies``` :  Returns a dictonary of cookies or False
- ```request.method``` :  Returns request method (GET, POST, PUT, DELETE etc)
- ```request.url``` :  Returns request url


#### Supported Response Functions
- ```response.headers``` :  Returns dictionary of respones headers
- ```response.text```: Returns response body
- ```response.cookies```: Returns list of cookies from set-cookie

To access attributes of cookies
```
for cookie in response.cookies:
    '''
    returns cookie name
    '''
    print(cookie.name)
    
    '''
    return cookie domain
    '''
    print(cookie.domain)
    
    '''
    return cookie path
    '''
    print(cookie.path) 
    
    '''
    return cookie secure flag
    '''
    print(cookie.secure) // returns True or False
    
    '''
    return cookie http Flag
    '''
    print(cookie.http) // returns True or False
    
    '''
    return cookie expires
    '''
    print(cookie.expires) 
    
    '''
    return cookie value
    '''
    print(cookie.value) 
```


