# Copyright (c) 2017 Huawei Technologies India Pvt.Limited.
# All Rights Reserved.
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

from osc_lib.cli import parseractions
from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils
from osc_lib.utils import columns as column_util

from neutronclient._i18n import _

LOG = logging.getLogger(__name__)

resource = 'port_pair'

_attr_map = (
    ('id', 'ID', column_util.LIST_BOTH),
    ('name', 'Name', column_util.LIST_BOTH),
    ('ingress', 'Ingress Logical Port', column_util.LIST_BOTH),
    ('egress', 'Egress Logical Port', column_util.LIST_BOTH),
    ('service_function_parameters', 'Service Function Parameters',
     column_util.LIST_LONG_ONLY),
    ('description', 'Description', column_util.LIST_LONG_ONLY),
    ('project_id', 'Project', column_util.LIST_LONG_ONLY),
)

_attr_map_dict = {
    'id': 'ID',
    'name': 'Name',
    'description': 'Description',
    'ingress': 'Ingress Logical Port',
    'egress': 'Egress Logical Port',
    'service_function_parameters': 'Service Function Parameters',
    'tenant_id': 'Project',
    'project_id': 'Project',
}


class CreateSfcPortPair(command.ShowOne):
    _description = _("Create a port pair")

    def get_parser(self, prog_name):
        parser = super(CreateSfcPortPair, self).get_parser(prog_name)
        parser.add_argument(
            'name',
            metavar='<name>',
            help=_('Name of the port pair'))
        parser.add_argument(
            '--description',
            metavar='<description>',
            help=_('Description for the port pair'))
        parser.add_argument(
            '--service-function-parameters',
            metavar='correlation=<correlation-type>,weight=<weight>',
            action=parseractions.MultiKeyValueAction,
            optional_keys=['correlation', 'weight'],
            help=_('Dictionary of service function parameters. '
                   'Currently, correlation=(None|mpls|nsh) and weight '
                   'are supported. Weight is an integer that influences '
                   'the selection of a port pair within a port pair group '
                   'for a flow. The higher the weight, the more flows will '
                   'hash to the port pair. The default weight is 1.'))
        parser.add_argument(
            '--ingress',
            metavar='<ingress>',
            required=True,
            help=_('Ingress neutron port (name or ID)'))
        parser.add_argument(
            '--egress',
            metavar='<egress>',
            required=True,
            help=_('Egress neutron port (name or ID)'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.network
        attrs = _get_common_attrs(self.app.client_manager, parsed_args)
        obj = client.create_sfc_port_pair(**attrs)
        display_columns, columns = utils.get_osc_show_columns_for_sdk_resource(
            obj, _attr_map_dict, ['location', 'tenant_id'])
        data = utils.get_dict_properties(obj, columns)
        return display_columns, data


class DeleteSfcPortPair(command.Command):
    _description = _("Delete a given port pair")

    def get_parser(self, prog_name):
        parser = super(DeleteSfcPortPair, self).get_parser(prog_name)
        parser.add_argument(
            'port_pair',
            metavar="<port-pair>",
            nargs='+',
            help=_("Port pair(s) to delete (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.network
        result = 0
        for pp in parsed_args.port_pair:
            try:
                port_pair_id = client.find_sfc_port_pair(
                    pp, ignore_missing=False)['id']
                client.delete_sfc_port_pair(port_pair_id)
            except Exception as e:
                result += 1
                LOG.error(_("Failed to delete port pair with name "
                            "or ID '%(port_pair)s': %(e)s"),
                          {'port_pair': pp, 'e': e})
        if result > 0:
            total = len(parsed_args.port_pair)
            msg = (_("%(result)s of %(total)s port pair(s) "
                     "failed to delete.") % {'result': result,
                                             'total': total})
            raise exceptions.CommandError(msg)


class ListSfcPortPair(command.Lister):
    _description = _("List port pairs")

    def get_parser(self, prog_name):
        parser = super(ListSfcPortPair, self).get_parser(prog_name)
        parser.add_argument(
            '--long',
            action='store_true',
            help=_("List additional fields in output")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.network
        data = client.sfc_port_pairs()
        headers, columns = column_util.get_column_definitions(
            _attr_map, long_listing=parsed_args.long)
        return (headers,
                (utils.get_dict_properties(
                    s, columns,
                ) for s in data))


class SetSfcPortPair(command.Command):
    _description = _("Set port pair properties")

    def get_parser(self, prog_name):
        parser = super(SetSfcPortPair, self).get_parser(prog_name)
        parser.add_argument(
            '--name',
            metavar='<name>',
            help=_('Name of the port pair'))
        parser.add_argument(
            '--description',
            metavar='<description>',
            help=_('Description for the port pair'))
        parser.add_argument(
            'port_pair',
            metavar='<port-pair>',
            help=_("Port pair to modify (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.network
        port_pair_id = client.find_sfc_port_pair(
            parsed_args.port_pair, ignore_missing=False
        )['id']
        attrs = _get_common_attrs(self.app.client_manager, parsed_args,
                                  is_create=False)
        try:
            client.update_sfc_port_pair(port_pair_id, **attrs)
        except Exception as e:
            msg = (_("Failed to update port pair '%(port_pair)s': %(e)s")
                   % {'port_pair': parsed_args.port_pair, 'e': e})
            raise exceptions.CommandError(msg)


class ShowSfcPortPair(command.ShowOne):
    _description = _("Display port pair details")

    def get_parser(self, prog_name):
        parser = super(ShowSfcPortPair, self).get_parser(prog_name)
        parser.add_argument(
            'port_pair',
            metavar='<port-pair>',
            help=_("Port pair to display (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.network
        port_pair_id = client.find_sfc_port_pair(
            parsed_args.port_pair, ignore_missing=False
        )['id']
        obj = client.get_sfc_port_pair(port_pair_id)
        display_columns, columns = utils.get_osc_show_columns_for_sdk_resource(
            obj, _attr_map_dict, ['location', 'tenant_id'])
        data = utils.get_dict_properties(obj, columns)
        return display_columns, data


def _get_common_attrs(client_manager, parsed_args, is_create=True):
    attrs = {}
    if parsed_args.name is not None:
        attrs['name'] = parsed_args.name
    if parsed_args.description is not None:
        attrs['description'] = parsed_args.description
    if is_create:
        _get_attrs(client_manager, attrs, parsed_args)
    return attrs


def _get_attrs(client_manager, attrs, parsed_args):
    client = client_manager.network
    if parsed_args.ingress is not None:
        attrs['ingress'] = client.find_port(
            parsed_args.ingress, ignore_missing=False
        )['id']
    if parsed_args.egress is not None:
        attrs['egress'] = client.find_port(
            parsed_args.egress, ignore_missing=False
        )['id']
    if parsed_args.service_function_parameters is not None:
        attrs['service_function_parameters'] = _get_service_function_params(
            parsed_args.service_function_parameters)


def _get_service_function_params(sf_params):
    attrs = {}
    for sf_param in sf_params:
        if 'correlation' in sf_param:
            if sf_param['correlation'] == 'None':
                attrs['correlation'] = None
            else:
                attrs['correlation'] = sf_param['correlation']
        if 'weight' in sf_param:
            attrs['weight'] = sf_param['weight']
    return attrs
