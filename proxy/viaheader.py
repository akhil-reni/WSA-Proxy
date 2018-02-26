#!/usr/bin/env python3

from __future__ import absolute_import

def via_header_value(orig, request_version):
    via = orig
    if via:
        via += ', '
    else:
        via = ''
    via = via + '%s %s' % (request_version, 'Strobes')
    return via
