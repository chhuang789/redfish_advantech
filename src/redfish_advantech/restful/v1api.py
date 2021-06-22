# Copyright Notice:
# Copyright 2016-2021 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link:
# https://github.com/DMTF/python-redfish-library/blob/master/LICENSE.md

# -*- coding: utf-8 -*-
"""Helper module for working with REST technology."""

# ---------Imports---------
#import itertools
import os
import sys
import ssl
import time
import gzip
import json
import base64
import logging.config
import http.client
import re
import inspect  # add by CH Huang

from collections import (OrderedDict)

from urllib.parse import urlparse, urlencode, quote
from io import StringIO
from io import BytesIO
# ---------End of imports---------

# ---------Debug logger---------

#LOGGER = logging.getLogger(__name__)

# ---------End of debug logger---------


class RetriesExhaustedError(Exception):
    """Raised when retry attempts have been exhausted."""
    pass


class InvalidCredentialsError(Exception):
    """Raised when invalid credentials have been provided."""
    pass


class ServerDownOrUnreachableError(Exception):
    """Raised when server is unreachable."""
    pass


class DecompressResponseError(Exception):
    """Raised when decompressing response failed."""
    pass


class JsonDecodingError(Exception):
    """Raised when there is an error in json data."""
    pass


class BadRequestError(Exception):
    """Raised when bad request made to server."""
    pass


class redfish_advantech:
    def __init__(self, hostname, port, username, password, nLogLevel=0):
        self.__logVerbose = nLogLevel
        # Load logging.conf
        logging.config.fileConfig('logging.conf')
        # create logger
        self.logger = logging.getLogger('simpleExample')
        if (self.get_logVerbose() >= 1): 
            self.logger.debug('=== Start to of redfish_advantech.__init__ ===')

        ssl._create_default_https_context = ssl._create_unverified_context

        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.payload = None
        self.theTimeout = 10
        self.connection = None
        self.authToken = None
        self.location = None
        self.url = ''
        self.method = ''
        self.urlThermal = ''
        self.urlPower = ''
        self.urlBios = ''
        self.urlProcessors = ''
        self.urlSimpleStorage = ''
        self.urlMemory = ''
        self.urlEthernetInterfaces = ''
        self.urlLogServices = ''
        self.strPowerState = ''
        self.lstURL = []
        self.nCount = 0
        self.nIndex = 0
        self.lstURL2 = []
        self.nCount2 = 0
        self.nIndex2 = 0
        self.urlLogEntries = ''

    def log(self, msg):
        self.logger.info("%s [hostname=%s port%d]",
                         msg, self.hostname, self.port)

    def get_logVerbose(self):
        """Return the level of log verbose"""
        return self.__logVerbose

    def set_logVerbose(self, logVerbose=0):
        """Set log Verbose level

        :param logVerbose: The level of log verbose to be set.
        :type logVerbose: int

        """
        self.__logVerbose = logVerbose

    def __del__(self):
        if (self.get_logVerbose() >= 1): 
            self.logger.debug('=== Destroy of redfish_advantech.__del__ ===')

    def __enter__(self):
        if (self.get_logVerbose() >= 1): 
            self.logger.debug('=== redfish_advantech.__enter__ ===')
        self.login()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if (self.get_logVerbose() >= 1): 
            self.logger.debug('=== redfish_advantech.__exit__ ===')
        self.logout()
        self.disconnect()

    # Redfish http request
    def rfRequest(self, log=True):
        if (self.get_logVerbose() >= 1 and log): 
            self.logger.debug('=== redfish_advantech.rfRequest ===')
        response = None
        if (self.authToken == None):  # for login only
            headers = {'Accept': '*/*',
                       'self.connection': 'Keep-Alive', 'OData-Version': '4.0'}
        else:  # for other requests
            headers = {'Accept': '*/*', 'self.connection': 'Keep-Alive',
                       'OData-Version': '4.0', 'X-Auth-Token': self.authToken}
        try:
            if (log):
                self.logger.info(
                    "--> rfRequest [%s %s]", self.method, self.url)
                if (self.payload == None):
                    self.logger.debug("headers=%s", headers)
                else:
                    self.logger.debug("headers=%s", headers)
                    self.logger.debug("self.payload=%s", self.payload)
            if (self.connection):
                if (self.payload == None):
                    self.connection.request(
                        self.method, self.url, self.payload, headers)
                else:
                    self.connection.request(
                        self.method, self.url, json.dumps(self.payload), headers)
                response = self.connection.getresponse()
            else:
                self.logger.error("self.connection is None")
        except Exception as e:
            self.logger.error(e)

        if (log):
            self.logger.info("response.status(reason)=%d(%s)",
                             response.status, response.reason)
        return response

    def get(self, path, args=None, headers=None):
        """Perform a GET request

        :param path: the URL path.
        :type path: str.
        :param args: the arguments to get.
        :type args: dict.
        :param headers: dict of headers to be appended.
        :type headers: dict.
        :returns: returns a rest request with method 'Get'

        """
        if (self.get_logVerbose() >= 1): 
            self.logger.debug('=== redfish_advantech.get ===')
        self.url = path
        self.method = "GET"
        try:
            return self.rfRequest()
        except ValueError:
            self.logger.error(
                "Error in json decoding. path=%s, method=%s", self.url, self.method)
            raise JsonDecodingError('Error in json decoding.')

    # Get Redfish V1 root
    def getRedfishV1(self):
        self.method = "GET"
        self.url = "/redfish/v1"
        self.logger.info(
            "--> getRedfishV1 [%s %s]", self.method, self.url)
        self.payload = None
        if (self.connection == None):
            self.connection = http.client.HTTPSConnection(
                self.hostname, self.port, timeout=self.theTimeout)
            self.logger.debug("Start the http connection")
        response = self.rfRequest()
        # Get the next link of getRedfishV1
        self.lstURL = []
        self.nCount = 0
        self.nIndex = 0
        result = response.read().decode(errors='replace')
        if (self.get_logVerbose() >= 1):
            self.logger.debug("result=%s", result)
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if (i[0] in {"OData", "SessionService", "AccountService", "EventService", "Systems", "Chassis", "Managers", "Links"}):
                    json_data2 = i[1]
                    for ii in json_data2.items():
                        if ii[0] == '@odata.id':
                            self.lstURL.append(ii[1])
                            self.nIndex += 1
                            self.nCount += 1
                            self.logger.debug("%s: %s", ii[0], ii[1])
                            self.logger.info("Next link=%s", ii[1])
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get OData
    def getOData(self):
        self.method = "GET"
        self.url = "/redfish/v1/OData"
        self.logger.info(
            "--> getOData [%s %s]", self.method, self.url)
        self.payload = None
        if (self.connection == None):
            self.connection = http.client.HTTPSConnection(
                self.hostname, self.port, timeout=self.theTimeout)
            self.logger.debug("Start the http connection")
        response = self.rfRequest()
        # Get the next link of getOData
        self.lstURL = []
        self.nCount = 0
        self.nIndex = 0
        result = response.read().decode(errors='replace')
        if (self.get_logVerbose() >= 1):
            self.logger.debug("result=%s", result)
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if i[0] == 'value':
                    if (self.get_logVerbose() >= 3):
                        self.logger.debug(
                            "%s: %s", i[0], json.dumps(i[1], indent=4))
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

    # Login
    def login(self):
        """ Login and start a REST session.  Remember to call logout() when you are done. """
        self.url = "/redfish/v1/SessionService/Sessions"
        self.method = "POST"
        self.logger.info("--> Login [%s %s]", self.method, self.url)
        if (not self.connection):
            self.connection = http.client.HTTPSConnection(
                self.hostname, self.port, timeout=self.theTimeout)
            self.logger.debug("Start the http connection")
        data = dict()
        data['UserName'] = self.username
        data['Password'] = self.password
        self.payload = data

        response = self.rfRequest(self)
        result = response.read().decode(errors='replace')
        if (self.get_logVerbose() >= 1):
            self.logger.debug("result=%s", result)
        # Get Token and Location of session after login
        self.authToken = response.headers['X-Auth-Token']
        self.logger.info("--> X-Auth-Token=%s]", self.authToken)
        # Get the next link of Chassis
        if (response.getcode() == 302):
            json_data = json.loads(result)
            for i in json_data.items():
                if i[0] == '@odata.id':
                    self.location = i[1]
                    self.logger.info("location=%s", self.location)
        self.payload = None

    # Logout
    def logout(self):
        """ Logout of session. YOU MUST CALL THIS WHEN YOU ARE DONE TO FREE UP SESSIONS"""
        if (self.authToken):
            self.url = self.location
            self.method = "DELETE"
            self.logger.info("--> Logout [%s %s]", self.method, self.url)
            self.payload = None
            response = self.rfRequest()
            if response.status not in [200, 202, 204]:
                self.logger.info("Invalid session resource: %s, return code: %d" % (
                    self.url, response.status))
            self.logger.info("User logout response.status(reason)=%d(%s)",
                             response.status, response.reason)
            self.authToken = None
            self.location = None

    # Disconnect
    def disconnect(self):
        if (self.get_logVerbose() >= 1): 
            self.logger.debug("=== Disconnecting http redfish_advantech.connection ===")
        if (self.connection):
            try:
                ret = self.connection.close()
                if (ret == None):
                    self.logger.info(
                        'http self.connection closed successfully')
                else:
                    logging.error(
                        'http self.connection closed failed with ', ret)
            except:
                logging.error(
                    'Unknown exception when close the http self.connection')
        else:
            self.logger.info(
                'http self.connection is not connected. No need to close it.')
        self.connection = None
        self.logger.debug('=== End to of redfish_advantech.disconnect ===')

    # Get SessionService
    def getSessionService(self):
        self.method = "GET"
        self.url = "/redfish/v1/SessionService"
        self.logger.info(
            "--> getSessionService [%s %s]", self.method, self.url)
        self.payload = None
        response = self.rfRequest()
        # Get the next link of SessionService
        self.url = ''
        result = response.read().decode(errors='replace')
        if (self.get_logVerbose() >= 1):
            self.logger.debug("result=%s", result)
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if i[0] == 'Sessions':
                    json_data2 = i[1]
                    for ii in json_data2.items():
                        if ii[0] == '@odata.id':
                            self.url = ii[1]
                    self.logger.debug("%s: %s", i[0], i[1])
                    self.logger.info("Next link=%s", self.url)
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get SessionService/Sessions
    def getSessionServiceSessions(self):
        self.lstURL = []
        self.nCount = 0
        self.nIndex = 0
        if (self.url != ''):
            #self.url = self.urlEthernetInterfaces
            self.method = "GET"
            self.logger.info(
                "--> getSessionServiceSessions [%s %s]", self.method, self.url)
            self.payload = None
            response = self.rfRequest()
            result = response.read().decode(errors='replace')
            if (response.getcode() == 200):
                json_data = json.loads(result)
                for i in json_data.items():
                    if i[0] == 'Members@odata.count':
                        self.nCount = i[1]
                    if i[0] == 'Members':
                        if (self.get_logVerbose() >= 2):
                            self.logger.debug(
                                "%s: %s", i[0], json.dumps(i[1], indent=4))
                    else:
                        self.logger.debug("%s: %s", i[0], i[1])
        # Get the next link(s) of getSessionServiceSessions
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if i[0] == 'Members@odata.count':
                    self.nCount = i[1]
                elif i[0] == 'Members':
                    json_data2 = dict(enumerate(i[1]))
                    for ii in json_data2.items():
                        for iii in ii[1].items():
                            if iii[0] == '@odata.id':
                                self.lstURL.append(iii[1])
                                self.nIndex += 1
                                if (self.get_logVerbose() >= 2):
                                    self.logger.info(
                                        "Next link=%s", self.lstURL[self.nIndex-1])
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get SessionService/Sessions/*
    def getSessionServiceSessionsAll(self):
        for i in range(self.nCount):
            if (self.lstURL[i] != ''):
                self.url = self.lstURL[i]
                self.method = "GET"
                self.logger.debug(
                    "--> getSessionServiceSessionsAll [%s %s]", self.method, self.url)
                self.payload = None
                response = self.rfRequest()
                result = response.read().decode(errors='replace')
                if (self.get_logVerbose() >= 2):
                    self.logger.debug(result)
                if (response.getcode() == 200):
                    json_data = json.loads(result)
                    for i in json_data.items():
                        if (self.get_logVerbose() >= 1):
                            self.logger.debug("%s: %s", i[0], i[1])

    # Get AccountService
    def getAccountService(self):
        self.method = "GET"
        self.url = "/redfish/v1/AccountService"
        self.logger.info(
            "--> getAccountService [%s %s]", self.method, self.url)
        self.payload = None
        response = self.rfRequest()
        # Get the next link of AccountService
        self.lstURL = []
        self.nCount = 0
        self.nIndex = 0
        result = response.read().decode(errors='replace')
        if (self.get_logVerbose() >= 1):
            self.logger.debug("result=%s", result)
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if (i[0] in {"Accounts", "Roles", "PrivilegeMap"}):
                    json_data2 = i[1]
                    for ii in json_data2.items():
                        if ii[0] == '@odata.id':
                            self.lstURL.append(ii[1])
                            self.nIndex += 1
                            self.nCount += 1
                            self.logger.debug("%s: %s", ii[0], ii[1])
                            self.logger.info("Next link=%s", ii[1])
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get AccountService/Accounts
    def getAccountServiceAccounts(self):
        self.method = "GET"
        self.url = "/redfish/v1/AccountService/Accounts"
        self.logger.info(
            "--> getAccountServiceAccounts [%s %s]", self.method, self.url)
        self.payload = None
        response = self.rfRequest()
        # Get the next link of AccountServiceAccounts
        self.lstURL2 = []
        self.nCount2 = 0
        self.nIndex2 = 0
        result = response.read().decode(errors='replace')
        if (self.get_logVerbose() >= 1):
            self.logger.debug("result=%s", result)
        # Get the next link(s) of AccountServiceAccounts
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if i[0] == 'Members@odata.count':
                    self.nCount2 = i[1]
                elif i[0] == 'Members':
                    json_data2 = dict(enumerate(i[1]))
                    for ii in json_data2.items():
                        for iii in ii[1].items():
                            if iii[0] == '@odata.id':
                                self.lstURL2.append(iii[1])
                                self.nIndex2 += 1
                                if (self.get_logVerbose() >= 1):
                                    self.logger.info(
                                        "Next link=%s", self.lstURL2[self.nIndex2-1])
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get AccountService/Accounts/*
    def getAccountServiceAccountsAll(self):
        for i in range(self.nCount2):
            if (self.lstURL2[i] != ''):
                self.url = self.lstURL2[i]
                self.method = "GET"
                self.logger.debug(
                    "--> getAccountServiceAccountsAll [%s %s]", self.method, self.url)
                self.payload = None
                response = self.rfRequest()
                result = response.read().decode(errors='replace')
                if (self.get_logVerbose() >= 1):
                    self.logger.debug(result)
                if (response.getcode() == 200):
                    json_data = json.loads(result)
                    for i in json_data.items():
                        if (self.get_logVerbose() >= 1):
                            self.logger.debug("%s: %s", i[0], i[1])

    # Get AccountService/Roles
    def getAccountServiceRoles(self):
        self.method = "GET"
        self.url = "/redfish/v1/AccountService/Roles"
        self.logger.info(
            "--> getAccountServiceRoles [%s %s]", self.method, self.url)
        self.payload = None
        response = self.rfRequest()
        # Get the next link of getAccountServiceRoles
        self.lstURL2 = []
        self.nCount2 = 0
        self.nIndex2 = 0
        result = response.read().decode(errors='replace')
        if (self.get_logVerbose() >= 1):
            self.logger.debug("result=%s", result)
        # Get the next link(s) of AccountServiceAccounts
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if i[0] == 'Members@odata.count':
                    self.nCount2 = i[1]
                elif i[0] == 'Members':
                    json_data2 = dict(enumerate(i[1]))
                    for ii in json_data2.items():
                        for iii in ii[1].items():
                            if iii[0] == '@odata.id':
                                self.lstURL2.append(iii[1])
                                self.nIndex2 += 1
                                if (self.get_logVerbose() >= 1):
                                    self.logger.info(
                                        "Next link=%s", self.lstURL2[self.nIndex2-1])
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get AccountService/Roles/*
    def getAccountServiceRolesAll(self):
        for i in range(self.nCount2):
            if (self.lstURL2[i] != ''):
                self.url = self.lstURL2[i]
                self.method = "GET"
                self.logger.debug(
                    "--> getAccountServiceRolesAll [%s %s]", self.method, self.url)
                self.payload = None
                response = self.rfRequest()
                result = response.read().decode(errors='replace')
                if (self.get_logVerbose() >= 1):
                    self.logger.debug(result)
                if (response.getcode() == 200):
                    json_data = json.loads(result)
                    for i in json_data.items():
                        if (self.get_logVerbose() >= 1):
                            self.logger.debug("%s: %s", i[0], i[1])

    # Get AccountService/PrivilegeMap
    def getAccountServicePrivilegeMap(self):
        self.method = "GET"
        self.url = "/redfish/v1/AccountService/PrivilegeMap"
        self.logger.info(
            "--> getAccountServicePrivilegeMap [%s %s]", self.method, self.url)
        self.payload = None
        response = self.rfRequest()
        # Get the next link of getAccountServicePrivilegeMap
        result = response.read().decode(errors='replace')
        if (self.get_logVerbose() >= 3):
            self.logger.debug("result=%s", result)

    # Get EventService
    def getEventService(self):
        self.method = "GET"
        self.url = "/redfish/v1/EventService"
        self.logger.info(
            "--> getEventService [%s %s]", self.method, self.url)
        self.payload = None
        response = self.rfRequest()
        # Get the next link of EventService
        self.lstURL = []
        self.nCount = 0
        self.nIndex = 0
        result = response.read().decode(errors='replace')
        if (self.get_logVerbose() >= 1):
            self.logger.debug("result=%s", result)
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if (i[0] in {"Subscriptions"}):
                    json_data2 = i[1]
                    for ii in json_data2.items():
                        if ii[0] == '@odata.id':
                            self.lstURL.append(ii[1])
                            self.nIndex += 1
                            self.nCount += 1
                            self.logger.debug("%s: %s", ii[0], ii[1])
                            self.logger.info("Next link=%s", ii[1])
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get EventService/Subscriptions
    def getEventServiceSubscriptions(self):
        self.method = "GET"
        self.url = "/redfish/v1/EventService/Subscriptions"
        self.logger.info(
            "--> getEventServiceSubscriptions [%s %s]", self.method, self.url)
        self.payload = None
        response = self.rfRequest()
        # Get the next link of AccountService
        self.lstURL = []
        self.nCount = 0
        self.nIndex = 0
        result = response.read().decode(errors='replace')
        if (self.get_logVerbose() >= 1):
            self.logger.debug("result=%s", result)
        # Get the next link(s) of getEventServiceSubscriptions
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if i[0] == 'Members@odata.count':
                    self.nCount = i[1]
                elif i[0] == 'Members':
                    json_data2 = dict(enumerate(i[1]))
                    for ii in json_data2.items():
                        for iii in ii[1].items():
                            if iii[0] == '@odata.id':
                                self.lstURL.append(iii[1])
                                self.nIndex += 1
                                if (self.get_logVerbose() >= 1):
                                    self.logger.info(
                                        "Next link=%s", self.lstURL[self.nIndex-1])
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

                                    
    # Get Chassis
    def getChassis(self):
        self.method = "GET"
        self.url = "/redfish/v1/Chassis"
        self.logger.info("--> getChassis [%s %s]", self.method, self.url)
        self.payload = None
        response = self.rfRequest()
        # Get the next link of Chassis
        self.url = ''
        result = response.read().decode(errors='replace')
        if (self.get_logVerbose() >= 1):
            self.logger.debug("result=%s", result)
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if i[0] == 'Members':
                    json_data2 = i[1][0]
                    for ii in json_data2.items():
                        if ii[0] == '@odata.id':
                            self.url = ii[1]
                    self.logger.debug("%s: %s", i[0], i[1])
                    self.logger.info("Next link=%s", self.url)
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get Chassis/1u
    def getChassis1u(self):
        if (self.url != ''):
            self.method = "GET"
            self.payload = None
            self.logger.info("--> getChassis1u [%s %s]", self.method, self.url)
            response = self.rfRequest()
            result = response.read().decode(errors='replace')
            if (self.get_logVerbose() >= 1):
                self.logger.debug("result=%s", result)
            if (response.getcode() == 200):
                json_data = json.loads(result)
                for i in json_data.items():
                    if i[0] == "Thermal":
                        json_data2 = json.loads(json.dumps(i[1]))
                        for ii in json_data2.items():
                            if ii[0] == '@odata.id':
                                self.urlThermal = ii[1]
                        self.logger.debug("%s: %s", ii[0], ii[1])
                        self.logger.info(
                            "Thermal self.url=%s", self.urlThermal)
                    elif i[0] == 'Power':
                        json_data2 = json.loads(json.dumps(i[1]))
                        for ii in json_data2.items():
                            if ii[0] == '@odata.id':
                                self.urlPower = ii[1]
                        self.logger.debug("%s: %s", i[0], i[1])
                        self.logger.info("Power self.url=%s", self.urlPower)
                    else:
                        self.logger.debug("%s: %s", i[0], i[1])

    # Get Chassis/1u/Thermal
    def getChassis1uThermal(self):
        if (self.urlThermal != ''):
            self.method = "GET"
            self.url = self.urlThermal
            self.logger.info(
                "--> getChassis1uThermal [%s %s]", self.method, self.url)
            self.payload = None
            response = self.rfRequest()
            result = response.read().decode(errors='replace')
            if (self.get_logVerbose() >= 1):
                self.logger.debug(result)
            if (response.getcode() == 200):
                json_data = json.loads(result)
                for i in json_data.items():
                    if i[0] == "Temperatures":
                        self.logger.debug("Temperatures")
                        json_data2 = dict(enumerate(i[1]))
                        for ii in json_data2.items():
                            for iii in ii[1].items():
                                if iii[0] == 'Name':
                                    sensorName = iii[1]
                                elif iii[0] == 'ReadingCelsius':
                                    sensorValues = iii[1]
                                    self.logger.debug(
                                        "SensorName: %s = %s °C", sensorName, sensorValues)
                    elif i[0] == 'Fans':
                        self.logger.info("Fans")
                        json_data2 = dict(enumerate(i[1]))
                        for ii in json_data2.items():
                            for iii in ii[1].items():
                                if iii[0] == 'Name':
                                    sensorName = iii[1]
                                elif iii[0] == 'Reading':
                                    sensorValues = iii[1]
                                    self.logger.info(
                                        "SensorName: %s=%s RPM", sensorName, sensorValues)
                    elif i[0] == 'Redundancy':
                        self.logger.info("Redundancy")
                    else:
                        self.logger.debug("%s: %s", i[0], i[1])

    # Get Chassis/1u/Power
    def getChassis1uPower(self):
        if (self.urlPower != ''):
            self.method = "GET"
            self.url = self.urlPower
            self.logger.info(
                "--> getChassis1uPower [%s %s]", self.method, self.url)
            self.payload = None
            response = self.rfRequest()
            result = response.read().decode(errors='replace')
            if (self.get_logVerbose() >= 1):
                self.logger.debug(result)
            if (response.getcode() == 200):
                json_data = json.loads(result)
                for i in json_data.items():
                    if i[0] == "Voltages":
                        self.logger.debug("Voltages")
                        json_data2 = dict(enumerate(i[1]))
                        for ii in json_data2.items():
                            for iii in ii[1].items():
                                if iii[0] == 'Name':
                                    sensorName = iii[1]
                                elif iii[0] == 'ReadingVolts':
                                    sensorValues = iii[1]
                                    self.logger.info(
                                        "SensorName: %s=%s V(DC)", sensorName, sensorValues)
                    elif i[0] == 'PowerSupplies':
                        self.logger.info("PowerSupplies")
                        json_data2 = dict(enumerate(i[1]))
                        for ii in json_data2.items():
                            for iii in ii[1].items():
                                if iii[0] == 'Name':
                                    sensorName = iii[1]
                                elif iii[0] == 'LineInputVoltage':
                                    sensorValues = iii[1]
                                    self.logger.info(
                                        "SensorName: %s=%s V(AC)", sensorName, sensorValues)
                    elif i[0] == 'Redundancy':
                        self.logger.info("Redundancy")
                    else:
                        self.logger.debug("%s: %s", i[0], i[1])

    # Get Systems
    def getSystems(self):
        self.url = "/redfish/v1/Systems"
        self.method = "GET"
        self.logger.info("--> getSystems [%s %s]", self.method, self.url)
        self.payload = None
        response = self.rfRequest()
        result = response.read().decode(errors='replace')
        if (self.get_logVerbose() >= 1):
            self.logger.debug(result)
        # Get the next link of Systems
        self.url = ''
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if i[0] == 'Members':
                    json_data2 = i[1][0]
                    for ii in json_data2.items():
                        if ii[0] == '@odata.id':
                            self.url = ii[1]
                    self.logger.debug("%s: %s", i[0], i[1])
                    self.logger.info("Next link=%s", self.url)
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get Systems/0
    def getSystems0(self):
        if (self.url != ''):
            self.url = "/redfish/v1/Systems/0"
            self.method = "GET"
            self.logger.debug("--> getSystems0 [%s %s]", self.method, self.url)
            self.payload = None
            response = self.rfRequest()
            result = response.read().decode(errors='replace')
            if (self.get_logVerbose() >= 1):
                self.logger.debug(result)
            if (response.getcode() == 200):
                json_data = json.loads(result)
                for i in json_data.items():
                    if i[0] == "PowerState":
                        self.strPowerState = i[1]
                        self.logger.debug("%s: %s", i[0], i[1])
                    elif i[0] == "Bios":
                        json_data2 = json.loads(json.dumps(i[1]))
                        for ii in json_data2.items():
                            if ii[0] == '@odata.id':
                                self.urlBios = ii[1]
                        self.logger.debug("%s: %s", i[0], i[1])
                        self.logger.info("Next link=%s", self.urlBios)
                    elif i[0] == 'Processors':
                        json_data2 = json.loads(json.dumps(i[1]))
                        for ii in json_data2.items():
                            if ii[0] == '@odata.id':
                                self.urlProcessors = ii[1]
                        self.logger.debug("%s: %s", i[0], i[1])
                        self.logger.info("Next link=%s", self.urlProcessors)
                    elif i[0] == 'SimpleStorage':
                        json_data2 = json.loads(json.dumps(i[1]))
                        for ii in json_data2.items():
                            if ii[0] == '@odata.id':
                                self.urlSimpleStorage = ii[1]
                        self.logger.debug("%s: %s", i[0], i[1])
                        self.logger.info("Next link=%s", self.urlSimpleStorage)
                    elif i[0] == 'Memory':
                        json_data2 = json.loads(json.dumps(i[1]))
                        for ii in json_data2.items():
                            if ii[0] == '@odata.id':
                                self.urlMemory = ii[1]
                        self.logger.debug("%s: %s", i[0], i[1])
                        self.logger.info("Next link=%s", self.urlMemory)
                    elif i[0] == 'EthernetInterfaces':
                        json_data2 = json.loads(json.dumps(i[1]))
                        for ii in json_data2.items():
                            if ii[0] == '@odata.id':
                                self.urlEthernetInterfaces = ii[1]
                        self.logger.debug("%s: %s", i[0], i[1])
                        self.logger.info(
                            "Next link=%s", self.urlEthernetInterfaces)
                    elif i[0] == 'LogServices':
                        json_data2 = json.loads(json.dumps(i[1]))
                        for ii in json_data2.items():
                            if ii[0] == '@odata.id':
                                self.urlLogServices = ii[1]
                        self.logger.debug("%s: %s", i[0], i[1])
                        self.logger.info("Next link=%s", self.urlLogServices)
                    else:
                        if (i[0] == 'Voltages' or i[0] == 'PowerSupplies'):
                            self.logger.debug("%s: a lots of data", i[0])
                        else:
                            self.logger.debug("%s: %s", i[0], i[1])

    # Get Systems/0/Bios
    def getSystems0Bios(self):
        if (self.urlBios != ''):
            self.url = self.urlBios
            self.method = "GET"
            self.logger.info(
                "--> getSystems0Bios [%s %s]", self.method, self.url)
            self.payload = None
            response = self.rfRequest()
            result = response.read().decode(errors='replace')
            if (self.get_logVerbose() >= 1):
                self.logger.debug(result)
            # Get contents of Systems/Bios
            if (response.getcode() == 200):
                json_data = json.loads(result)
                for i in json_data.items():
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get Systems/0/Processors
    def getSystems0Processors(self):
        if (self.urlProcessors != ''):
            self.url = self.urlProcessors
            self.method = "GET"
            self.logger.info(
                "--> getSystems0Processors [%s %s]", self.method, self.url)
            self.payload = None
            response = self.rfRequest()
            result = response.read().decode(errors='replace')
            if (self.get_logVerbose() >= 1):
                self.logger.debug(result)
            # Get contents of Systems/Bios
            if (response.getcode() == 200):
                json_data = json.loads(result)
                for i in json_data.items():
                    self.logger.debug("%s: %s", i[0], i[1])
        # Get the next link of Processors
        self.url = ''
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if i[0] == 'Members':
                    json_data2 = i[1][0]
                    for ii in json_data2.items():
                        if ii[0] == '@odata.id':
                            self.url = ii[1]
                    self.logger.debug("%s: %s", i[0], i[1])
                    self.logger.info("Next link=%s", self.url)
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get Systems/0/Processors/CPU0
    def getSystems0ProcessorsCPU0(self):
        if (self.url != ''):
            self.method = "GET"
            self.logger.info(
                "--> getSystems0ProcessorsCPU0 [%s %s]", self.method, self.url)
            self.payload = None
            response = self.rfRequest()
            result = response.read().decode(errors='replace')
            if (self.get_logVerbose() >= 1):
                self.logger.debug(result)
            # Get contents of Systems/Bios
            if (response.getcode() == 200):
                json_data = json.loads(result)
                for i in json_data.items():
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get Systems/0/SimpleStorage
    def getSystems0SimpleStorage(self):
        if (self.urlSimpleStorage != ''):
            self.url = self.urlSimpleStorage
            self.method = "GET"
            self.logger.debug(
                "--> getSystems0SimpleStorage [%s %s]", self.method, self.url)
            self.payload = None
            response = self.rfRequest()
            result = response.read().decode(errors='replace')
            if (self.get_logVerbose() >= 1):
                self.logger.debug(result)
            # Get contents of Systems/Bios
            if (response.getcode() == 200):
                json_data = json.loads(result)
                for i in json_data.items():
                    self.logger.debug("%s: %s", i[0], i[1])
        # Get the next link(s) of SimpleStorage
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if i[0] == 'Members@odata.count':
                    self.nCount = i[1]
                elif i[0] == 'Members':
                    json_data2 = dict(enumerate(i[1]))
                    for ii in json_data2.items():
                        for iii in ii[1].items():
                            if iii[0] == '@odata.id':
                                self.lstURL.append(iii[1])
                                self.nIndex = self.nIndex + 1
                                self.logger.info(
                                    "Next link=%s", self.lstURL[self.nIndex-1])
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get Systems/0/SimpleStorage/*
    def getSystems0SimpleStorageAll(self):
        for i in range(self.nCount):
            if (self.lstURL[i] != ''):
                self.url = self.lstURL[i]
                self.method = "GET"
                self.logger.debug(
                    "--> getSystems0SimpleStorageAll [%s %s]", self.method, self.url)
                self.payload = None
                response = self.rfRequest()
                result = response.read().decode(errors='replace')
                if (self.get_logVerbose() >= 1):
                    self.logger.debug(result)
                if (response.getcode() == 200):
                    json_data = json.loads(result)
                    for i in json_data.items():
                        self.logger.debug("%s: %s", i[0], i[1])

    # Get Systems/0/Memory
    def getSystems0Memory(self):
        if (self.urlMemory != ''):
            self.url = self.urlMemory
            self.method = "GET"
            self.logger.info(
                "--> getSystems0Memory [%s %s]", self.method, self.url)
            self.payload = None
            response = self.rfRequest()
            result = response.read().decode(errors='replace')
            if (self.get_logVerbose() >= 1):
                self.logger.debug(result)
            if (response.getcode() == 200):
                json_data = json.loads(result)
                for i in json_data.items():
                    self.logger.debug("%s: %s", i[0], i[1])
        # Get the next link(s) of Memory
        self.lstURL = []
        self.nCount = 0
        self.nIndex = 0
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if i[0] == 'Members@odata.count':
                    self.nCount = i[1]
                elif i[0] == 'Members':
                    json_data2 = dict(enumerate(i[1]))
                    for ii in json_data2.items():
                        for iii in ii[1].items():
                            if iii[0] == '@odata.id':
                                self.lstURL.append(iii[1])
                                self.nIndex = self.nIndex + 1
                                self.logger.info(
                                    "Next link=%s", self.lstURL[self.nIndex-1])
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get Systems/0/Memory/*
    def getSystems0MemoryAll(self):
        for i in range(self.nCount):
            if (self.lstURL[i] != ''):
                self.url = self.lstURL[i]
                self.method = "GET"
                self.logger.info(
                    "--> getSystems0MemoryAll [%s %s]", self.method, self.url)
                self.payload = None
                response = self.rfRequest()
                result = response.read().decode(errors='replace')
                if (self.get_logVerbose() >= 1):
                    self.logger.debug(result)
                if (response.getcode() == 200):
                    json_data = json.loads(result)
                    for i in json_data.items():
                        self.logger.debug("%s: %s", i[0], i[1])

    # Get Systems/0/EthernetInterfaces
    def getSystems0EthernetInterfaces(self):
        if (self.urlEthernetInterfaces != ''):
            self.url = self.urlEthernetInterfaces
            self.method = "GET"
            self.logger.info(
                "--> getSystems0EthernetInterfaces [%s %s]", self.method, self.url)
            self.payload = None
            response = self.rfRequest()
            result = response.read().decode(errors='replace')
            if (self.get_logVerbose() >= 1):
                self.logger.debug(result)
            if (response.getcode() == 200):
                json_data = json.loads(result)
                for i in json_data.items():
                    self.logger.debug("%s: %s", i[0], i[1])
        # Get the next link(s) of EthernetInterfaces
        self.lstURL = []
        self.nCount = 0
        self.nIndex = 0
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if i[0] == 'Members@odata.count':
                    self.nCount = i[1]
                elif i[0] == 'Members':
                    json_data2 = dict(enumerate(i[1]))
                    for ii in json_data2.items():
                        for iii in ii[1].items():
                            if iii[0] == '@odata.id':
                                self.lstURL.append(iii[1])
                                self.nIndex = self.nIndex + 1
                                self.logger.info(
                                    "Next link=%s", self.lstURL[self.nIndex-1])
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get Systems/0/EthernetInterfaces/*
    def getSystems0EthernetInterfacesAll(self):
        for i in range(self.nCount):
            if (self.lstURL[i] != ''):
                self.url = self.lstURL[i]
                self.method = "GET"
                self.logger.info(
                    "--> getSystems0EthernetInterfacesAll [%s %s]", self.method, self.url)
                self.payload = None
                response = self.rfRequest()
                result = response.read().decode(errors='replace')
                if (self.get_logVerbose() >= 1):
                    self.logger.debug(result)
                if (response.getcode() == 200):
                    json_data = json.loads(result)
                    for i in json_data.items():
                        self.logger.debug("%s: %s", i[0], i[1])

    # Get Systems/0/LogServices
    def getSystems0LogServices(self):
        if (self.urlLogServices != ''):
            self.url = self.urlLogServices
            self.method = "GET"
            self.logger.info(
                "--> getSystems0LogServices [%s %s]", self.method, self.url)
            self.payload = None
            response = self.rfRequest()
            result = response.read().decode(errors='replace')
            if (self.get_logVerbose() >= 1):
                self.logger.debug(result)
            if (response.getcode() == 200):
                json_data = json.loads(result)
                for i in json_data.items():
                    self.logger.debug("%s: %s", i[0], i[1])
        # Get the next link(s) of LogServices
        self.lstURL = []
        self.nCount = 0
        self.nIndex = 0
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if i[0] == 'Members@odata.count':
                    self.nCount = i[1]
                elif i[0] == 'Members':
                    json_data2 = dict(enumerate(i[1]))
                    for ii in json_data2.items():
                        for iii in ii[1].items():
                            if iii[0] == '@odata.id':
                                self.lstURL.append(iii[1])
                                self.nIndex = self.nIndex + 1
                                self.logger.info(
                                    "Next link=%s", self.lstURL[self.nIndex-1])
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get Systems/0/LogServices/Log
    def getSystems0LogServicesLog(self):
        self.urlLogEntries = ''
        for i in range(self.nCount):
            if (self.lstURL[i] != ''):
                self.url = self.lstURL[i]
                self.method = "GET"
                self.logger.info(
                    "--> getSystems0LogServicesLog [%s %s]", self.method, self.url)
                self.payload = None
                response = self.rfRequest()
                result = response.read().decode(errors='replace')
                if (self.get_logVerbose() >= 1):
                    self.logger.debug(result)
                if (response.getcode() == 200):
                    json_data = json.loads(result)
                    for i in json_data.items():
                        self.logger.debug("%s: %s", i[0], i[1])
                    if i[0] == 'Entries':
                        json_data2 = list(i[1].items())
                        if json_data2[0][0] == '@odata.id':
                            self.urlLogEntries = json_data2[0][1]
                            self.logger.info(
                                "Next link=%s", self.urlLogEntries)
                else:
                    self.logger.debug("%s: %s", i[0], i[1])

    # Get Systems/0/LogServices/Log/Entries
    def getSystems0LogServicesLogEntries(self):
        if (self.urlLogEntries != ''):
            self.url = self.urlLogEntries
            self.method = "GET"
            self.logger.info(
                "--> getSystems0LogServicesLogEntries [%s %s]", self.method, self.url)
            self.payload = None
            response = self.rfRequest()
            result = response.read().decode(errors='replace')
            if (self.get_logVerbose() >= 2):
                self.logger.debug(result)
            if (response.getcode() == 200):
                json_data = json.loads(result)
                for i in json_data.items():
                    if (i[0] != "Members"):
                        self.logger.debug("%s: %s", i[0], i[1])
        # Get the next link(s) of Entries
        self.lstURL = []
        self.nCount = 0
        self.nIndex = 0
        if (response.getcode() == 200):
            json_data = json.loads(result)
            for i in json_data.items():
                if i[0] == 'Members@odata.count':
                    self.nCount = i[1]
                    self.logger.info(
                        "Number of LogServicesLogEntries %d", self.nCount)
                elif i[0] == 'Members':
                    json_data2 = dict(enumerate(i[1]))
                    for ii in json_data2.items():
                        for iii in ii[1].items():
                            if iii[0] == '@odata.id':
                                self.lstURL.append(iii[1])
                                self.nIndex = self.nIndex + 1
                                if (self.get_logVerbose() >= 2):
                                    self.logger.debug(
                                        "Next link=%s", self.lstURL[self.nIndex-1])
                else:
                    self.logger.debug("%s: %s", i[0], i[1])
        # Get Systems/0/LogServices/Log/Entries/*
        for i in range(self.nCount):
            if (self.lstURL[i] != ''):
                if (self.get_logVerbose() <= 1):
                    if i < self.nCount - 1:
                        print("\rLogServicesLogEntries({})={}".format(i+1, self.lstURL[i]), end = '')
                    else:
                        print("\rLogServicesLogEntries({})={}".format(i+1, self.lstURL[i]))
                self.url = self.lstURL[i]
                self.method = "GET"
                self.payload = None
                response = self.rfRequest(False)
                result = response.read().decode(errors='replace')
                if (self.get_logVerbose() >= 3):
                    self.logger.debug(result)
                if (response.getcode() == 200):
                    json_data = json.loads(result)
                    for i in json_data.items():
                        if (self.get_logVerbose() >= 2):
                            self.logger.debug("%s: %s", i[0], i[1])

    # GracefulShutdown or Power on
    def actionGracefulShutdownOrPowerOn(self):
        if (self.strPowerState != ''):
            self.url = "/redfish/v1/Systems/0/Actions/ComputerSystem.Reset"
            self.method = "POST"
            self.logger.info(
                "--> actionGracefulShutdownOrPowerOn [%s %s]", self.method, self.url)
            if (self.strPowerState == 'On'):
                #self.payload = {'ResetType': 'GracefulShutdown'}
                data = dict()
                data['ResetType'] = 'GracefulShutdown'
                self.payload = data
                self.logger.info('self.payload GracefulShutdown')
            else:
                #self.payload = {'ResetType': 'On'}
                data = dict()
                data['ResetType'] = 'On'
                self.payload = data
                self.logger.info('self.payload Power On')
            response = self.rfRequest()
            result = response.read().decode(errors='replace')
            if (self.get_logVerbose() >= 1):
                self.logger.debug(result)
        self.payload = None