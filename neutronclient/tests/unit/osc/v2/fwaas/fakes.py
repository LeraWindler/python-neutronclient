# Copyright 2016 FUJITSU LIMITED
# All Rights Reserved
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

import collections
from unittest import mock

from openstack.network.v2 import firewall_group as fw_group
from openstack.network.v2 import firewall_policy as fw_policy
from openstack.network.v2 import firewall_rule as fw_rule
from oslo_utils import uuidutils


class FakeFWaaS(object):

    def create(self, attrs={}):
        """Create a fake fwaas resources

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A OrderedDict faking the fwaas resource
        """
        self.ordered.update(attrs)
        if 'FirewallGroup' == self.__class__.__name__:
            return fw_group.FirewallGroup(**self.ordered)
        if 'FirewallPolicy' == self.__class__.__name__:
            return fw_policy.FirewallPolicy(**self.ordered)
        if 'FirewallRule' == self.__class__.__name__:
            fw_r = fw_rule.FirewallRule(**self.ordered)
            protocol = fw_r['protocol'].upper() if fw_r['protocol'] else 'ANY'
            src_ip = str(fw_r['source_ip_address']).lower()
            src_port = '(' + str(fw_r['source_port']).lower() + ')'
            dst_ip = str(fw_r['destination_ip_address']).lower()
            dst_port = '(' + str(fw_r['destination_port']).lower() + ')'
            src = 'source(port): ' + src_ip + src_port
            dst = 'dest(port): ' + dst_ip + dst_port
            action = fw_r['action'] if fw_r.get('action') else 'no-action'
            fw_r['summary'] = ',\n '.join([protocol, src, dst, action])
            return fw_r

    def bulk_create(self, attrs=None, count=2):
        """Create multiple fake fwaas resources

        :param Dictionary attrs:
            A dictionary with all attributes
        :param int count:
            The number of fwaas resources to fake
        :return:
            A list of dictionaries faking the fwaas resources
        """
        return [self.create(attrs=attrs) for i in range(0, count)]

    def get(self, attrs=None, count=2):
        """Create multiple fake fwaas resources

        :param Dictionary attrs:
            A dictionary with all attributes
        :param int count:
            The number of fwaas resources to fake
        :return:
            A list of dictionaries faking the fwaas resource
        """
        if attrs is None:
            self.attrs = self.bulk_create(count=count)
        return mock.Mock(side_effect=attrs)


class FirewallGroup(FakeFWaaS):
    """Fake one or more firewall group"""

    def __init__(self):
        super(FirewallGroup, self).__init__()
        self.ordered = collections.OrderedDict((
            ('id', 'firewall-group-id-' +
             uuidutils.generate_uuid(dashed=False)),
            ('name', 'my-group-' +
             uuidutils.generate_uuid(dashed=False)),
            ('ingress_firewall_policy_id', None),
            ('egress_firewall_policy_id', None),
            ('description', 'my-desc-' +
             uuidutils.generate_uuid(dashed=False)),
            ('status', 'INACTIVE'),
            ('ports', []),
            ('admin_state_up', True),
            ('shared', False),
            ('tenant_id', 'tenant-id-' +
             uuidutils.generate_uuid(dashed=False)),
        ))


class FirewallPolicy(FakeFWaaS):
    """Fake one or more firewall policy"""

    def __init__(self):
        super(FirewallPolicy, self).__init__()
        self.ordered = collections.OrderedDict((
            ('id', 'firewall-policy-' +
             uuidutils.generate_uuid(dashed=False)),
            ('name', 'my-policy-' +
             uuidutils.generate_uuid(dashed=False)),
            ('firewall_rules', []),
            ('description', 'my-desc-' +
             uuidutils.generate_uuid(dashed=False)),
            ('audited', True),
            ('shared', False),
            ('tenant_id', 'tenant-id-' +
             uuidutils.generate_uuid(dashed=False)),
        ))


class FirewallRule(FakeFWaaS):
    """Fake one or more firewall rule"""

    def __init__(self):
        super(FirewallRule, self).__init__()
        self.ordered = collections.OrderedDict((
            ('id', 'firewall-rule-id-' +
             uuidutils.generate_uuid(dashed=False)),
            ('name', 'my-rule-' +
             uuidutils.generate_uuid(dashed=False)),
            ('enabled', False),
            ('description', 'my-desc-' +
             uuidutils.generate_uuid(dashed=False)),
            ('ip_version', 4),
            ('action', 'deny'),
            ('protocol', None),
            ('source_ip_address', '192.168.1.0/24'),
            ('source_port', '1:11111'),
            ('destination_ip_address', '192.168.2.2'),
            ('destination_port', '2:22222'),
            ('shared', False),
            ('tenant_id', 'tenant-id-' +
             uuidutils.generate_uuid(dashed=False)),
            ('source_firewall_group_id', 'firewall-group-id-' +
             uuidutils.generate_uuid(dashed=False)),
            ('destination_firewall_group_id', 'firewall-group-id-' +
             uuidutils.generate_uuid(dashed=False)),
        ))
