# ===============================================================================
#
# Copyright (c) 2010, 2011 by Thomas Hauth and Stephan Riedel
#
# This file is part of ROCED.
#
# ROCED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ROCED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ROCED.  If not, see <http://www.gnu.org/licenses/>.
#
# ===============================================================================


import libxml2
import logging
from Core import MachineRegistry
from IntegrationAdapter.Integration import IntegrationAdapterBase
from Util import ScaleTools


class TorqueIntegrationAdapter(IntegrationAdapterBase):
    reg_torque_node_name = "torque_node_name"
    reg_torque_bootstrap_url = "torque_bootstrap_url"
    reg_torque_node_ip = "torque_node_ip"

    def torqHostName():  # @NoSelf
        doc = """Docstring"""  # @UnusedVariable

        def fget(self):
            return self._torqHostName

        def fset(self, value):
            self._torqHostName = value

        def fdel(self):
            del self._torqHostName

        return locals()

    torqHostName = property(**torqHostName())

    def torqIp():  # @NoSelf
        doc = """Docstring"""  # @UnusedVariable

        def fget(self):
            return self._torqIp

        def fset(self, value):
            self._torqIp = value

        def fdel(self):
            del self._torqIp

        return locals()

    torqIp = property(**torqIp())

    def torqNodeBootstrapRoot():  # @NoSelf
        doc = """Docstring"""  # @UnusedVariable

        def fget(self):
            return self._torqNodeBootstrapRoot

        def fset(self, value):
            self._torqNodeBootstrapRoot = value

        def fdel(self):
            del self._torqNodeBootstrapRoot

        return locals()

    torqNodeBootstrapRoot = property(**torqNodeBootstrapRoot())

    def torqNodeBootstrapUrl():  # @NoSelf
        doc = """Docstring"""  # @UnusedVariable

        def fget(self):
            return self._torqNodeBootstrapUrl

        def fset(self, value):
            self._torqNodeBootstrapUrl = value

        def fdel(self):
            del self._torqNodeBootstrapUrl

        return locals()

    torqNodeBootstrapUrl = property(**torqNodeBootstrapUrl())

    ''' ssh key to torque server
    if this property is None, all calls will be made locally
    '''

    def torqKey():  # @NoSelf
        doc = """Docstring"""  # @UnusedVariable

        def fget(self):
            return self._torqKey

        def fset(self, value):
            self._torqKey = value

        def fdel(self):
            del self._torqKey

        return locals()

    torqKey = property(**torqKey())

    def __init__(self):
        IntegrationAdapterBase.__init__(self)

        self.mr = MachineRegistry.MachineRegistry()
        self.torqIp = None
        self.torqHostName = None
        self.torqKey = None
        self.torqInternalIp = None

        self.torqNodeBootstrapRoot = None
        self.torqNodeBootstrapUrl = None

    def init(self):
        IntegrationAdapterBase.init(self)
        self.mr.registerListener(self)

    def manage(self):

        disint = filter(lambda (k, v): v.get(self.mr.regStatus) == self.mr.statusDisintegrating,
                        self.mr.machines.iteritems())

        # check if fully offline
        mlist = ""

        for (mid, v) in disint:
            mlist += v.get(self.reg_torque_node_name) + " "

        if len(mlist) == 0:
            return

        (res, xmlRes) = self.runCommandOnPbs('pbsnodes -x ' + mlist.strip())

        if res == 0:
            try:
                xd = libxml2.parseDoc(xmlRes)

                for (mid, v) in disint:
                    nodeName = v.get(self.reg_torque_node_name)
                    stateLs = xd.xpathEval("/Data/Node[name='%s']/state" % nodeName)
                    if len(stateLs) > 0:
                        if str(stateLs[0].content).strip() == "offline" or str(
                                stateLs[0].content).strip() == "down,offline":
                            self.runCommandOnPbs('python torqconf.py del_node ' + nodeName)
                            self.mr.updateMachineStatus(mid, self.mr.statusDisintegrated)
                        else:
                            logging.info("node %s not offline yet" % nodeName)
                    else:
                        logging.error("no state information contained for node %s" % nodeName)
            except:
                logging.error("could not parse %s" % xmlRes)

        """
                ssh = ScaleTools.Ssh(self.torqIp, "root", self.torqKey, None, 1)
                nodeName = self.mr.machines[evt.id][self.reg_torque_node_name]
                ssh.handleSshCall( 'python torqconf.py del_node ' + nodeName)
                self.mr.updateMachineStatus(evt.id, self.mr.StatusDisintegrated)
        """
        pass

    def retrieveTorqueIpOpenVpn(self, machine_id):
        ssh = ScaleTools.Ssh.getSshOnMachine(self.mr.machines[machine_id])
        # get from an openvpn connection
        (res, vpn_ip) = ssh.handleSshCall("/sbin/ifconfig tun0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'")
        vpn_ip = vpn_ip.strip().strip("\n")
        if (not res == 0) or len(vpn_ip) < 1:
            logging.error("Can't determine vpn ip for machine " + machine_id)
        else:
            self.mr.machines[machine_id][self.reg_torque_node_ip] = vpn_ip

    def retrieveTorqueIp(self, machine_id):
        # default behaviour
        self.mr.machines[machine_id][self.reg_torque_node_ip] = self.mr.machines[machine_id][self.mr.regInternalIp]

    def setNodeOffline(self, machine_id):
        nodeName = self.mr.machines[machine_id][self.reg_torque_node_name]
        self.runCommandOnPbs('pbsnodes -o ' + nodeName)

    def integrateNode(self, machine_id):
        nodeName = "cloud-" + str(machine_id)
        self.mr.machines[machine_id][self.reg_torque_node_name] = nodeName

        # calls on node itself, routed through the node controller automatically by ssh class if needed
        ssh = ScaleTools.Ssh.getSshOnMachine(self.mr.machines[machine_id])

        paramList = self.torqInternalIp + \
                    " " + self.torqHostName + \
                    " " + nodeName + \
                    " " + self.mr.machines[machine_id][self.mr.regSiteType]

        # call run-bootstrap.sh script if needed
        if not self.torqNodeBootstrapUrl == None:
            ssh.handleSshCall("./run-bootstrap.sh " +
                              self.torqNodeBootstrapUrl + " " + self.torqNodeBootstrapRoot + " " + paramList)  # additional parameters go here...

        # upload file if needed
        if not self.nodeBootstrapFile == None:
            ssh.copyToRemote(self.nodeBootstrapFile)

        # run command if needed
        if not self.nodeBootstrapCall == None:
            ssh.handleSshCall(self.nodeBootstrapCall + " " + paramList)

        # retrieve the ip torque uses to connect to this instance
        self.retrieveTorqueIp(machine_id)

    def integrateWithTorq(self, machine_id):
        ip = self.mr.machines[machine_id].get(self.reg_torque_node_ip)
        self.runCommandOnPbs(
            'python torqconf.py add_node ' + self.mr.machines[machine_id][self.reg_torque_node_name] + ' ' + ip)

    '''
    uses either SSH or a simple shell call to run commands on the pbs server
    '''

    def runCommandOnPbs(self, cmd):
        if self.torqKey == None:
            return ScaleTools.Shell.executeCommand(cmd)
        else:
            ssh = ScaleTools.Ssh(self.torqIp, "root", self.torqKey, None, 1)
            return ssh.handleSshCall(cmd)

    def onEvent(self, evt):
        if isinstance(evt, MachineRegistry.StatusChangedEvent):
            if evt.newStatus == self.mr.statusUp:
                logging.debug("Integrating machine with ip " + str(self.mr.machines[evt.id].get(self.mr.regHostname)))

                # ha, new machine to integrate
                self.mr.updateMachineStatus(evt.id, self.mr.statusIntegrating)

                self.integrateNode(evt.id)
                self.integrateWithTorq(evt.id)

                # TODO: only if everything worked
                self.mr.updateMachineStatus(evt.id, self.mr.statusWorking)

            # cat /etc/hosts | grep 172.19.1.100 | awk '{print $2}'
            if evt.newStatus == self.mr.statusWorking:
                # check if this node was added by us or if if is already running on the cluster, try to integrate
                if self.mr.machines[evt.id].get(self.reg_torque_node_name, None) == None:
                    # not listed internally, try to find the node name

                    (res, nodeName) = self.runCommandOnPbs("python torqconf.py get_node_name %s" % \
                                                           self.mr.machines[evt.id].get(self.reg_torque_node_ip,
                                                                                        "xxx.xxx.xxx.xxy"))
                    nodeName = nodeName.strip()

                    if (res == 0) and (len(nodeName) > 0):
                        logging.info("rediscovered torque node: %s" % nodeName)
                        self.mr.machines[evt.id][self.reg_torque_node_name] = nodeName
                    else:
                        logging.warn("cant rediscovered torque node: %s with internal ip %s" % (
                        evt.id, self.mr.machines[evt.id].get(self.reg_torque_node_ip)))

            if evt.newStatus == self.mr.statusPendingDisintegration:
                # ha, machine to disintegrate
                self.mr.updateMachineStatus(evt.id, self.mr.statusDisintegrating)

                if self.mr.machines[evt.id].get(self.reg_torque_node_name, None) == None:
                    # never registered with torqe, kill right away
                    self.mr.updateMachineStatus(evt.id, self.mr.statusDisintegrated)
                else:
                    # set node offline. only remove as soon as no more jobs running
                    self.setNodeOffline(evt.id)

    def getDescription(self):
        return "TorqueIntegrationAdapter"