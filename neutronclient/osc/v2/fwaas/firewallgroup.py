# Copyright 2016-2017 FUJITSU LIMITED
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

import logging

from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils
from osc_lib.utils import columns as column_util

from neutronclient._i18n import _
from neutronclient.osc import utils as osc_utils
from neutronclient.osc.v2.fwaas import constants as const
from neutronclient.osc.v2 import utils as v2_utils


LOG = logging.getLogger(__name__)

_formatters = {
    'admin_state_up': v2_utils.AdminStateColumn,
}

_attr_map_dict = {
    'id': 'ID',
    'name': 'Name',
    'ingress_firewall_policy_id': 'Ingress Policy ID',
    'egress_firewall_policy_id': 'Egress Policy ID',
    'description': 'Description',
    'status': 'Status',
    'ports': 'Ports',
    'admin_state_up': 'State',
    'shared': 'Shared',
    'tenant_id': 'Project',
    'project_id': 'Project',
}

_attr_map = (
    ('id', 'ID', column_util.LIST_BOTH),
    ('name', 'Name', column_util.LIST_BOTH),
    ('ingress_firewall_policy_id', 'Ingress Policy ID', column_util.LIST_BOTH),
    ('egress_firewall_policy_id', 'Egress Policy ID', column_util.LIST_BOTH),
    ('description', 'Description', column_util.LIST_LONG_ONLY),
    ('status', 'Status', column_util.LIST_LONG_ONLY),
    ('ports', 'Ports', column_util.LIST_LONG_ONLY),
    ('admin_state_up', 'State', column_util.LIST_LONG_ONLY),
    ('shared', 'Shared', column_util.LIST_LONG_ONLY),
    ('tenant_id', 'Project', column_util.LIST_LONG_ONLY),
)


def _get_common_parser(parser):
    parser.add_argument(
        '--name',
        help=_('Name for the firewall group'))
    parser.add_argument(
        '--description',
        metavar='<description>',
        help=_('Description of the firewall group'))
    ingress_group = parser.add_mutually_exclusive_group()
    ingress_group.add_argument(
        '--ingress-firewall-policy',
        metavar='<ingress-firewall-policy>',
        dest='ingress_firewall_policy',
        help=_('Ingress firewall policy (name or ID)'))
    ingress_group.add_argument(
        '--no-ingress-firewall-policy',
        dest='no_ingress_firewall_policy',
        action='store_true',
        help=_('Detach ingress firewall policy from the firewall group'))
    egress_group = parser.add_mutually_exclusive_group()
    egress_group.add_argument(
        '--egress-firewall-policy',
        metavar='<egress-firewall-policy>',
        dest='egress_firewall_policy',
        help=_('Egress firewall policy (name or ID)'))
    egress_group.add_argument(
        '--no-egress-firewall-policy',
        dest='no_egress_firewall_policy',
        action='store_true',
        help=_('Detach egress firewall policy from the firewall group'))
    shared_group = parser.add_mutually_exclusive_group()

    shared_group.add_argument(
        '--share',
        action='store_true',
        help=_('Share the firewall group to be used in all projects '
               '(by default, it is restricted to be used by the '
               'current project).'))
    shared_group.add_argument(
        '--no-share',
        action='store_true',
        help=_('Restrict use of the firewall group to the '
               'current project'))
    admin_group = parser.add_mutually_exclusive_group()
    admin_group.add_argument(
        '--enable',
        action='store_true',
        help=_('Enable firewall group'))
    admin_group.add_argument(
        '--disable',
        action='store_true',
        help=_('Disable firewall group'))
    return parser


def _get_common_attrs(client_manager, parsed_args, is_create=True):
    attrs = {}
    client = client_manager.network

    if is_create:
        if 'project' in parsed_args and parsed_args.project is not None:
            attrs['tenant_id'] = osc_utils.find_project(
                client_manager.identity,
                parsed_args.project,
                parsed_args.project_domain,
            ).id
    if (parsed_args.ingress_firewall_policy and
            parsed_args.no_ingress_firewall_policy):
        attrs['ingress_firewall_policy_id'] = client.find_firewall_policy(
            parsed_args.ingress_firewall_policy)['id']
    elif parsed_args.ingress_firewall_policy:
        attrs['ingress_firewall_policy_id'] = client.find_firewall_policy(
            parsed_args.ingress_firewall_policy)['id']
    elif parsed_args.no_ingress_firewall_policy:
        attrs['ingress_firewall_policy_id'] = None
    if (parsed_args.egress_firewall_policy and
            parsed_args.no_egress_firewall_policy):
        attrs['egress_firewall_policy_id'] = client.find_firewall_policy(
            parsed_args.egress_firewall_policy)['id']
    elif parsed_args.egress_firewall_policy:
        attrs['egress_firewall_policy_id'] = client.find_firewall_policy(
            parsed_args.egress_firewall_policy)['id']
    elif parsed_args.no_egress_firewall_policy:
        attrs['egress_firewall_policy_id'] = None
    if parsed_args.share:
        attrs['shared'] = True
    if parsed_args.no_share:
        attrs['shared'] = False
    if parsed_args.enable:
        attrs['admin_state_up'] = True
    if parsed_args.disable:
        attrs['admin_state_up'] = False
    if parsed_args.name:
        attrs['name'] = str(parsed_args.name)
    if parsed_args.description:
        attrs['description'] = str(parsed_args.description)
    if parsed_args.port and parsed_args.no_port:
        attrs['ports'] = sorted([client.find_port(
            p)['id'] for p in set(parsed_args.port)])
    elif parsed_args.port:
        ports = []
        for p in set(parsed_args.port):
            ports.append(client.find_port(p)['id'])
        if not is_create:
            ports += client.find_firewall_group(
                parsed_args.firewall_group)['ports']
        attrs['ports'] = sorted(set(ports))
    elif parsed_args.no_port:
        attrs['ports'] = []
    return attrs


class CreateFirewallGroup(command.ShowOne):
    _description = _("Create a new firewall group")

    def get_parser(self, prog_name):
        parser = super(CreateFirewallGroup, self).get_parser(prog_name)
        _get_common_parser(parser)
        osc_utils.add_project_owner_option_to_parser(parser)
        port_group = parser.add_mutually_exclusive_group()
        port_group.add_argument(
            '--port',
            metavar='<port>',
            action='append',
            help=_('Port(s) (name or ID) to apply firewall group.  This '
                   'option can be repeated'))
        port_group.add_argument(
            '--no-port',
            dest='no_port',
            action='store_true',
            help=_('Detach all port from the firewall group'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.network
        attrs = _get_common_attrs(self.app.client_manager, parsed_args)
        obj = client.create_firewall_group(**attrs)
        display_columns, columns = utils.get_osc_show_columns_for_sdk_resource(
            obj, _attr_map_dict, ['location', 'tenant_id'])
        data = utils.get_dict_properties(obj, columns, formatters=_formatters)
        return (display_columns, data)


class DeleteFirewallGroup(command.Command):
    _description = _("Delete firewall group(s)")

    def get_parser(self, prog_name):
        parser = super(DeleteFirewallGroup, self).get_parser(prog_name)
        parser.add_argument(
            const.FWG,
            metavar='<firewall-group>',
            nargs='+',
            help=_('Firewall group(s) to delete (name or ID)'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.network
        result = 0
        for fwg in parsed_args.firewall_group:
            try:
                fwg_id = client.find_firewall_group(fwg)['id']
                client.delete_firewall_group(fwg_id)
            except Exception as e:
                result += 1
                LOG.error(_("Failed to delete firewall group with "
                            "name or ID '%(firewall_group)s': %(e)s"),
                          {const.FWG: fwg, 'e': e})

        if result > 0:
            total = len(parsed_args.firewall_group)
            msg = (_("%(result)s of %(total)s firewall group(s) "
                     "failed to delete.") % {'result': result, 'total': total})
            raise exceptions.CommandError(msg)


class ListFirewallGroup(command.Lister):
    _description = _("List firewall groups")

    def get_parser(self, prog_name):
        parser = super(ListFirewallGroup, self).get_parser(prog_name)
        parser.add_argument(
            '--long',
            action='store_true',
            help=_("List additional fields in output")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.network
        obj = client.firewall_groups()
        headers, columns = column_util.get_column_definitions(
            _attr_map, long_listing=parsed_args.long)
        return (headers, (utils.get_dict_properties(
            s, columns, formatters=_formatters) for s in obj))


class SetFirewallGroup(command.Command):
    _description = _("Set firewall group properties")

    def get_parser(self, prog_name):
        parser = super(SetFirewallGroup, self).get_parser(prog_name)
        _get_common_parser(parser)
        parser.add_argument(
            const.FWG,
            metavar='<firewall-group>',
            help=_('Firewall group to update (name or ID)'))
        parser.add_argument(
            '--port',
            metavar='<port>',
            action='append',
            help=_('Port(s) (name or ID) to apply firewall group.  This '
                   'option can be repeated'))
        parser.add_argument(
            '--no-port',
            dest='no_port',
            action='store_true',
            help=_('Detach all port from the firewall group'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.network
        fwg_id = client.find_firewall_group(parsed_args.firewall_group)['id']
        attrs = _get_common_attrs(self.app.client_manager, parsed_args,
                                  is_create=False)
        try:
            client.update_firewall_group(fwg_id, **attrs)
        except Exception as e:
            msg = (_("Failed to set firewall group '%(group)s': %(e)s")
                   % {'group': parsed_args.firewall_group, 'e': e})
            raise exceptions.CommandError(msg)


class ShowFirewallGroup(command.ShowOne):
    _description = _("Display firewall group details")

    def get_parser(self, prog_name):
        parser = super(ShowFirewallGroup, self).get_parser(prog_name)
        parser.add_argument(
            const.FWG,
            metavar='<firewall-group>',
            help=_('Firewall group to show (name or ID)'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.network
        fwg_id = client.find_firewall_group(parsed_args.firewall_group)['id']
        obj = client.get_firewall_group(fwg_id)
        display_columns, columns = utils.get_osc_show_columns_for_sdk_resource(
            obj, _attr_map_dict, ['location', 'tenant_id'])
        data = utils.get_dict_properties(obj, columns, formatters=_formatters)
        return (display_columns, data)


class UnsetFirewallGroup(command.Command):
    _description = _("Unset firewall group properties")

    def get_parser(self, prog_name):
        parser = super(UnsetFirewallGroup, self).get_parser(prog_name)
        parser.add_argument(
            const.FWG,
            metavar='<firewall-group>',
            help=_('Firewall group to unset (name or ID)'))
        port_group = parser.add_mutually_exclusive_group()
        port_group.add_argument(
            '--port',
            metavar='<port>',
            action='append',
            help=_('Port(s) (name or ID) to apply firewall group.  This '
                   'option can be repeated'))
        port_group.add_argument(
            '--all-port',
            action='store_true',
            help=_('Remove all ports for this firewall group'))
        parser.add_argument(
            '--ingress-firewall-policy',
            action='store_true',
            help=_('Ingress firewall policy (name or ID) to delete'))
        parser.add_argument(
            '--egress-firewall-policy',
            action='store_true',
            dest='egress_firewall_policy',
            help=_('Egress firewall policy (name or ID) to delete'))
        shared_group = parser.add_mutually_exclusive_group()
        shared_group.add_argument(
            '--share',
            action='store_true',
            help=_('Restrict use of the firewall group to the '
                   'current project'))
        parser.add_argument(
            '--enable',
            action='store_true',
            help=_('Disable firewall group'))
        return parser

    def _get_attrs(self, client, parsed_args):
        attrs = {}
        if parsed_args.ingress_firewall_policy:
            attrs['ingress_firewall_policy_id'] = None
        if parsed_args.egress_firewall_policy:
            attrs['egress_firewall_policy_id'] = None
        if parsed_args.share:
            attrs['shared'] = False
        if parsed_args.enable:
            attrs['admin_state_up'] = False
        if parsed_args.port:
            old = client.find_firewall_group(
                parsed_args.firewall_group)['ports']
            new = [client.find_port(r)['id'] for r in parsed_args.port]
            attrs['ports'] = sorted(list(set(old) - set(new)))
        if parsed_args.all_port:
            attrs['ports'] = []
        return attrs

    def take_action(self, parsed_args):
        client = self.app.client_manager.network
        fwg_id = client.find_firewall_group(parsed_args.firewall_group)['id']
        attrs = self._get_attrs(client, parsed_args)
        try:
            client.update_firewall_group(fwg_id, **attrs)
        except Exception as e:
            msg = (_("Failed to unset firewall group '%(group)s': %(e)s")
                   % {'group': parsed_args.firewall_group, 'e': e})
            raise exceptions.CommandError(msg)
