# ROS/IOP Bridge
# Copyright (c) 2017 Fraunhofer
#
# This program is dual licensed; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# version 2 as published by the Free Software Foundation, or
# enter into a proprietary license agreement with the copyright
# holder.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; or you can read the full license at
# <http://www.gnu.de/documents/gpl-2.0.html>
#
# :author: Alexander Tiderko

from iop_msgs_fkie.msg import OcuFeedback, JausAddress

from .address import Address


class Client(object):

    '''
    Client is a group of nodes with equal subsystem and node id.
    If one of the services is specified to monitor only, all clients are set to monitor only mode.
    If for one of the services is controlled_susystem is set it will be applied to all clients of the group.
    '''

    def __init__(self, subsystem_id, node_id):
        '''
        :type jaus_address: iop_msgs_fkie/JausMessage
        '''
        jaus_address = JausAddress(subsystem_id, node_id, 0)
        self._address = Address(jaus_address)
        self._subsystem_restricted = 65535
        self._only_monitor = False
        self._ocu_nodes = dict()  # address of ocu client : services
        self._warnings = dict()  # address of ocu client : list of services with warnings
        self._has_control_access = False
        self.control_subsystem = -1  # this value is set by robot.py

    @property
    def address(self):
        return self._address

    @property
    def subsystem_id(self):
        return self._address.subsystem_id

    @property
    def node_id(self):
        return self._address.node_id

    @property
    def component_id(self):
        return self._address.component_id

    @property
    def subsystem_restricted(self):
        return self._subsystem_restricted

    @property
    def only_monitor(self):
        return self._only_monitor

    @property
    def has_control_access(self):
        return self._has_control_access

    def apply(self, feedback):
        '''
        :type jaus_address: iop_msgs_fkie/OcuFeedback
        '''
        if not isinstance(feedback, OcuFeedback):
            raise TypeError("Client.apply() expects iop_msgs_fkie/OcuFeedback, got %s" % type(feedback))
        if self != feedback.reporter:
            return False
        # change the controlled subsystem only once to avoid glint
        if self._subsystem_restricted == 65535:
            if feedback.subsystem_restricted not in [0, 65535]:
                self._subsystem_restricted = feedback.subsystem_restricted
        if not self._only_monitor and feedback.only_monitor:
            self._only_monitor = feedback.only_monitor
        self._ocu_nodes[Address(feedback.reporter)] = feedback.services
        self._warnings = dict()
        self._has_control_access = False
        for services in self._ocu_nodes.values():
            for service_info in services:
                warnstate = service_info.access_state in [4, 5]  # see OcuServiceInfo for number
                address = Address(feedback.reporter)
                if warnstate:
                    if address not in self._warnings:
                        self._warnings[address] = list()
                    self._warnings[address].append(service_info)
#                if service_info.access_state in [3, 6]:  # see OcuServiceInfo for number
#                    self._assined_subsystems.add(service_info.addr_control.subsystem_id)
                if service_info.access_state in [3]:  # see OcuServiceInfo for number
                    self._has_control_access = True
        return True

    def get_warnings(self, subsystem=None):
        '''
        Returns warnings for controlled subsystem. Returns all warnings if no subsystem specified.
        '''
        if subsystem is None:
            return self._warnigns
        result = dict()
        for address, service_infos in self._warnings.items():
            for service_info in service_infos:
                if service_info.addr_control.subsystem_id == subsystem:
                    if address not in result:
                        result[address] = list()
                    result[address].append(service_info)
        return result

    def __repr__(self, *args, **kwargs):
        return "Client[%s]" % (self.address)

    def __str__(self, *args, **kwargs):
        return "%s" % (self.address)

    def __hash__(self):
        return hash(self._address)

    def __eq__(self, other):
        if isinstance(other, Client):
            return self.address == other.address
        elif isinstance(other, (JausAddress, Address)):
            return self.address == JausAddress(other.subsystem_id, other.node_id, 0)
        return False

    def __ne__(self, other):
        # Not strictly necessary, but to avoid having both x==y and x!=y
        # True at the same time
        if isinstance(other, Client):
            return not(self.address == other.address)
        elif isinstance(other, (JausAddress, Address)):
            return not (self.address == JausAddress(other.subsystem_id, other.node_id, 0))
        return True

    def __lt__(self, other):
        if isinstance(other, Client):
            return self.address < other.address
        elif isinstance(other, (JausAddress, Address)):
            return self.address < JausAddress(other.subsystem_id, other.node_id, 0)
        raise TypeError("Client.__lt__() expects Client, JausAddress or Address, got %s" % type(other))
