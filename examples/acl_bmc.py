# Copyright Notice:
# Copyright 2016-2021 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link:
# https://github.com/DMTF/python-redfish-library/blob/master/LICENSE.md

import sys
from redfish_advantech.restful.v1api import redfish_advantech
import argparse

nLogLevel = 0
parser = argparse.ArgumentParser()
parser.add_argument("-v",
                    "--verbose",
                    action="count",
                    default=0,
                    help="verbose level")
args = parser.parse_args()
print(f"args.verbose level：{args.verbose}")
if (args.verbose >= 0):
    nLogLevel = args.verbose

login_host = "172.17.21.120"
login_port = 443
login_account = "administrator"
login_password = "advantech"

sky8101 = redfish_advantech(login_host, login_port,
                            login_account, login_password, nLogLevel)
sky8101.getRedfishV1()
sky8101.getOData()
sky8101.login()
sky8101.getSessionService()
sky8101.getSessionServiceSessions()
sky8101.getSessionServiceSessionsAll()
sky8101.getAccountService()
sky8101.getAccountServiceAccounts()
sky8101.getAccountServiceAccountsAll()
sky8101.getAccountServiceRoles()
sky8101.getAccountServiceRolesAll()
sky8101.getAccountServicePrivilegeMap()
sky8101.getEventService()
sky8101.getEventServiceSubscriptions()
sky8101.getChassis()
sky8101.getChassis1u()
sky8101.getChassis1uThermal()
sky8101.getChassis1uPower()
sky8101.getSystems()
sky8101.getSystems0()
sky8101.getSystems0Bios()
sky8101.getSystems0Processors()
sky8101.getSystems0ProcessorsCPU0()
sky8101.getSystems0SimpleStorage()
sky8101.getSystems0SimpleStorageAll()
sky8101.getSystems0Memory()
sky8101.getSystems0MemoryAll()
sky8101.getSystems0EthernetInterfaces()
sky8101.getSystems0EthernetInterfacesAll()
sky8101.getSystems0LogServices()
sky8101.getSystems0LogServicesLog()
sky8101.getSystems0LogServicesLogEntries()
#response = sky8101.get("/redfish/v1/Systems", None)
#result = response.read().decode(errors='replace')
# sky8101.logger.debug(result)
#response = sky8101.get("/redfish/v1/Systems/0", None)
#result = response.read().decode(errors='replace')
# sky8101.logger.debug(result)
# sky8101.getSystems0()
# sky8101.actionGracefulShutdownOrPowerOn()
sky8101.logout()
sky8101.disconnect()
del sky8101
