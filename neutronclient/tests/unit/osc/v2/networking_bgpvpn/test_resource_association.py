# Copyright (c) 2016 Juniper Networks Inc.
# All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

import operator
from unittest import mock

from osc_lib import exceptions
from osc_lib import utils as osc_utils
from osc_lib.utils import columns as column_util

from neutronclient.tests.unit.osc.v2.networking_bgpvpn import fakes


columns_short = tuple(col for col, _, listing_mode
                      in fakes.BgpvpnFakeAssoc._attr_map
                      if listing_mode in (column_util.LIST_BOTH,
                                          column_util.LIST_SHORT_ONLY))
columns_long = tuple(col for col, _, listing_mode
                     in fakes.BgpvpnFakeAssoc._attr_map
                     if listing_mode in (column_util.LIST_BOTH,
                                         column_util.LIST_LONG_ONLY))
headers_short = tuple(head for _, head, listing_mode
                      in fakes.BgpvpnFakeAssoc._attr_map
                      if listing_mode in (column_util.LIST_BOTH,
                                          column_util.LIST_SHORT_ONLY))
headers_long = tuple(head for _, head, listing_mode
                     in fakes.BgpvpnFakeAssoc._attr_map
                     if listing_mode in (column_util.LIST_BOTH,
                                         column_util.LIST_LONG_ONLY))
sorted_attr_map = sorted(fakes.BgpvpnFakeAssoc._attr_map,
                         key=operator.itemgetter(1))
sorted_columns = tuple(col for col, _, _ in sorted_attr_map)
sorted_headers = tuple(head for _, head, _ in sorted_attr_map)


def _get_data(attrs, columns=sorted_columns):
    return osc_utils.get_dict_properties(
        attrs, columns, formatters=fakes.BgpvpnFakeAssoc._formatters)


class TestCreateResAssoc(fakes.TestNeutronClientBgpvpn):
    def setUp(self):
        super(TestCreateResAssoc, self).setUp()
        self.networkclient.find_bgpvpn = mock.Mock(
            side_effect=lambda name_or_id: {'id': name_or_id})
        self.networkclient.find_fake_resource = mock.Mock(
            side_effect=lambda name_or_id: {'id': name_or_id})
        self.cmd = fakes.CreateBgpvpnFakeResAssoc(self.app, self.namespace)

    def test_create_resource_association(self):
        fake_bgpvpn = fakes.create_one_bgpvpn()
        fake_res = fakes.create_one_resource()
        fake_res_assoc = fakes.create_one_resource_association(
            fake_res)
        self.networkclient.create_bgpvpn_router_association = mock.Mock(
            return_value=fake_res_assoc)
        self.networkclient.find_bgpvpn_fake_resource_association = mock.Mock(
            side_effect=lambda name_or_id: {'id': name_or_id})
        arglist = [
            fake_bgpvpn['id'],
            fake_res['id'],
            '--project', fake_bgpvpn['tenant_id'],
        ]
        verifylist = [
            ('bgpvpn', fake_bgpvpn['id']),
            ('resource', fake_res['id']),
            ('project', fake_bgpvpn['tenant_id'])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cols, data = self.cmd.take_action(parsed_args)

        fake_res_assoc_call = {
            'fake_resource_id': 'fake_resource_id',
            'tenant_id': 'fake_project_id'
        }

        self.networkclient.create_bgpvpn_router_association.\
            assert_called_once_with(
                fake_bgpvpn['id'],
                **fake_res_assoc_call)
        self.assertEqual(sorted_columns, cols)
        self.assertEqual(_get_data(fake_res_assoc), data)


class TestSetResAssoc(fakes.TestNeutronClientBgpvpn):
    def setUp(self):
        super(TestSetResAssoc, self).setUp()
        self.cmd = fakes.SetBgpvpnFakeResAssoc(self.app, self.namespace)

    def test_set_resource_association(self):
        fake_bgpvpn = fakes.create_one_bgpvpn()
        fake_res = fakes.create_one_resource()
        fake_res_assoc = fakes.create_one_resource_association(
            fake_res)
        self.networkclient.update_bgpvpn_router_association = mock.Mock(
            return_value={fakes.BgpvpnFakeAssoc._resource: fake_res_assoc})
        arglist = [
            fake_res_assoc['id'],
            fake_bgpvpn['id'],
        ]
        verifylist = [
            ('resource_association_id', fake_res_assoc['id']),
            ('bgpvpn', fake_bgpvpn['id']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.networkclient.update_bgpvpn_router_association.\
            assert_not_called()
        self.assertIsNone(result)


class TestDeleteResAssoc(fakes.TestNeutronClientBgpvpn):
    def setUp(self):
        super(TestDeleteResAssoc, self).setUp()
        self.networkclient.find_bgpvpn = mock.Mock(
            side_effect=lambda name_or_id: {'id': name_or_id})
        self.cmd = fakes.DeleteBgpvpnFakeResAssoc(self.app, self.namespace)

    def test_delete_one_association(self):
        fake_bgpvpn = fakes.create_one_bgpvpn()
        fake_res = fakes.create_one_resource()
        fake_res_assoc = fakes.create_one_resource_association(
            fake_res)
        self.networkclient.delete_bgpvpn_router_association = \
            mock.Mock()
        arglist = [
            fake_res_assoc['id'],
            fake_bgpvpn['id'],
        ]
        verifylist = [
            ('resource_association_ids', [fake_res_assoc['id']]),
            ('bgpvpn', fake_bgpvpn['id']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.networkclient.delete_bgpvpn_router_association.\
            assert_called_once_with(fake_bgpvpn['id'], fake_res_assoc['id'])
        self.assertIsNone(result)

    def test_delete_multi_bpgvpn(self):
        count = 3
        fake_bgpvpn = fakes.create_one_bgpvpn()
        fake_res = fakes.create_resources(count=count)
        fake_res_assocs = fakes.create_resource_associations(
            fake_res)
        fake_res_assoc_ids = [
            fake_res_assoc['id'] for fake_res_assoc in fake_res_assocs
        ]
        self.networkclient.delete_bgpvpn_router_association = \
            mock.Mock()
        arglist = \
            fake_res_assoc_ids + [
                fake_bgpvpn['id']
            ]
        verifylist = [
            ('resource_association_ids', fake_res_assoc_ids),
            ('bgpvpn', fake_bgpvpn['id']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.networkclient.delete_bgpvpn_router_association.\
            assert_has_calls([
                mock.call(
                    fake_bgpvpn['id'], id) for id in fake_res_assoc_ids])
        self.assertIsNone(result)

    def test_delete_multi_bpgvpn_with_unknown(self):
        count = 3
        fake_bgpvpn = fakes.create_one_bgpvpn()
        fake_res = fakes.create_resources(count=count)
        fake_res_assocs = fakes.create_resource_associations(
            fake_res)
        fake_res_assoc_ids = [
            fake_res_assoc['id'] for fake_res_assoc in fake_res_assocs
        ]

        def raise_unknonw_resource(resource_path, name_or_id):
            if str(count - 2) in name_or_id:
                raise Exception()
        self.networkclient.delete_bgpvpn_router_association = mock.Mock(
            side_effect=raise_unknonw_resource)
        arglist = \
            fake_res_assoc_ids + [
                fake_bgpvpn['id']
            ]
        verifylist = [
            ('resource_association_ids', fake_res_assoc_ids),
            ('bgpvpn', fake_bgpvpn['id']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(exceptions.CommandError, self.cmd.take_action,
                          parsed_args)

        self.networkclient.delete_bgpvpn_router_association.\
            assert_has_calls([
                mock.call(fake_bgpvpn['id'], id) for id in fake_res_assoc_ids]
            )


class TestListResAssoc(fakes.TestNeutronClientBgpvpn):
    def setUp(self):
        super(TestListResAssoc, self).setUp()
        self.networkclient.find_bgpvpn = mock.Mock(
            side_effect=lambda name_or_id: {'id': name_or_id})
        self.cmd = fakes.ListBgpvpnFakeResAssoc(self.app, self.namespace)

    def test_list_bgpvpn_associations(self):
        count = 3
        fake_bgpvpn = fakes.create_one_bgpvpn()
        fake_res = fakes.create_resources(count=count)
        fake_res_assocs = fakes.create_resource_associations(
            fake_res)
        self.networkclient.bgpvpn_router_associations = mock.Mock(
            return_value=fake_res_assocs)
        arglist = [
            fake_bgpvpn['id'],
        ]
        verifylist = [
            ('bgpvpn', fake_bgpvpn['id']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        headers, data = self.cmd.take_action(parsed_args)

        self.networkclient.bgpvpn_router_associations.\
            assert_called_once_with(fake_bgpvpn['id'], retrieve_all=True)
        self.assertEqual(headers, list(headers_short))
        self.assertEqual(
            list(data),
            [_get_data(fake_res_assoc, columns_short) for fake_res_assoc
             in fake_res_assocs])

    def test_list_bgpvpn_associations_long_mode(self):
        count = 3
        fake_bgpvpn = fakes.create_one_bgpvpn()
        fake_res = fakes.create_resources(count=count)
        fake_res_assocs = fakes.create_resource_associations(
            fake_res)
        self.networkclient.bgpvpn_router_associations = mock.Mock(
            return_value=fake_res_assocs)
        arglist = [
            '--long',
            fake_bgpvpn['id'],
        ]
        verifylist = [
            ('long', True),
            ('bgpvpn', fake_bgpvpn['id']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        headers, data = self.cmd.take_action(parsed_args)

        self.networkclient.bgpvpn_router_associations.\
            assert_called_once_with(fake_bgpvpn['id'], retrieve_all=True)
        self.assertEqual(headers, list(headers_long))
        self.assertEqual(
            list(data),
            [_get_data(fake_res_assoc, columns_long) for fake_res_assoc
             in fake_res_assocs])


class TestShowResAssoc(fakes.TestNeutronClientBgpvpn):
    def setUp(self):
        super(TestShowResAssoc, self).setUp()
        self.networkclient.find_bgpvpn = mock.Mock(
            side_effect=lambda name_or_id: {'id': name_or_id})
        self.cmd = fakes.ShowBgpvpnFakeResAssoc(self.app, self.namespace)

    def test_show_resource_association(self):
        fake_bgpvpn = fakes.create_one_bgpvpn()
        fake_res = fakes.create_one_resource()
        fake_res_assoc = fakes.create_one_resource_association(
            fake_res)
        self.networkclient.get_bgpvpn_router_association = mock.Mock(
            return_value=fake_res_assoc)
        arglist = [
            fake_res_assoc['id'],
            fake_bgpvpn['id'],
        ]
        verifylist = [
            ('resource_association_id', fake_res_assoc['id']),
            ('bgpvpn', fake_bgpvpn['id']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.networkclient.get_bgpvpn_router_association.\
            assert_called_once_with(fake_bgpvpn['id'], fake_res_assoc['id'])
        self.assertEqual(sorted_columns, columns)
        self.assertEqual(data, _get_data(fake_res_assoc))
