#!/usr/bin/env python
#
#The MIT License (MIT)
#
# Copyright (c) 2015 Bit9 + Carbon Black
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# -----------------------------------------------------------------------------
# Wrapper object around CB API that extends it to add functionality
#
# last updated 2015-03-07 by Ben Johnson bjohnson@bit9.com
#

from cbapi import cbapi
import requests
import simplejson as json

class CbExtendedApi(cbapi.CbApi):
    """
    Extends the official CbApi to have more functionality.
    """
    def __init__(self, server, ssl_verify=True, token=None):
        """
        Takes an instantiated cbapi instance as the only argument
        """
        cbapi.CbApi.__init__(self, server, ssl_verify, token)

    def binary_search_iter(self, query_string, start=0, rows=10, sort="server_added_timestamp desc"):
        """
        A generator for doing a binary search so you can say for results in binary_search_iter
        so that you can keep iterating through all the results.
        :param query_string:
        :param start:
        :param rows:
        :param sort:
        :return:
        """
        our_start = start
        while True:
            resp = self.binary_search(query_string, our_start, rows, sort)
            results = resp.get('results')
            for binary in results:
                yield binary
            our_start += len(results)
            if len(results) < rows:
                break

    def process_search_iter(self, query_string, start=0, rows=10, sort="last_update desc"):
        """
        A generator for doing a process search so you can say for results in process_search_iter
        so that you can keep going through all the results.

        :param cbapi_inst:
        :param query_string:
        :param start:
        :param rows:
        :param sort:
        :return:
        """
        our_start = start
        while True:
            resp = self.process_search(query_string, our_start, rows, sort)
            results = resp.get('results')
            for proc in results:
                yield proc
            our_start += len(results)
            if len(results) < rows:
                break

    def process_search_and_detail_iter(self, query):
        """

        :param query:
        :return:
        """
        for proc in self.process_search_iter(query, start=0, rows=200):
            details = self.process_summary(proc.get('id'), proc.get('segment_id'))
            parent_details = details.get('parent')
            proc_details = details.get('process')
            yield (proc, proc_details, parent_details)

    def process_search_and_events_iter(self, query):
        """

        :param query:
        :return:
        """
        for proc in self.process_search_iter(query, start=0, rows=200):
            events = self.process_events(proc['id'], proc['segment_id']).get('process', [])
            yield (proc, events)


    # class ActionType:
    #     Email=0
    #     Syslog=1
    #     HTTPPost=2
    #     Alert=3
    def watchlist_enable_action(self, watchlist_id, action_type=3, action_data=None):
        """
        Enable an action like create an alert, use syslog, or use email on watchlist hit.
        """
        data = {'action_type': action_type}
        if action_data:
            data['action_data'] = action_data
            data['watchlist_id'] = watchlist_id

        url = "%s/util/v1/watchlist/%d/action" % (self.server, watchlist_id)
        r = requests.post(url, headers=self.token_header, data=json.dumps(data), verify=self.ssl_verify)
        r.raise_for_status()

        return r.json()