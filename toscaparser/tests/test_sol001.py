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

import os
import six
import testtools

from toscaparser.common import exception
import toscaparser.elements.interfaces as ifaces
from toscaparser.elements.nodetype import NodeType
from toscaparser.elements.portspectype import PortSpec
from toscaparser.functions import GetInput
from toscaparser.functions import GetProperty
from toscaparser.nodetemplate import NodeTemplate
from toscaparser.tests.base import TestCase
from toscaparser.tosca_template import ToscaTemplate
from toscaparser.utils.gettextutils import _
import toscaparser.utils.yamlparser


@testtools.skip(reason="Fails when building deb package")
class ToscaSol001Test(TestCase):
    '''TOSCA template.'''
    def setUp(self):
        TestCase.setUp(self)
        exception.ExceptionCollector.stop()  # Added as sometimes negative testcases fails.
        self.tosca_tpl = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "spec_samples/etsi_sol001/sunshinedb/Definitions/sunshinedb.yaml")
        self.tosca = ToscaTemplate(path=tosca_tpl, no_required_paras_check=True)


    def test_version(self):
        self.assertEqual(self.tosca.version, "tosca_simple_yaml_1_2")

    def test_description(self):
        expected_description = "Relational database cluster (non-scalable)"
        self.assertEqual(self.tosca.description, expected_description)

    def test_node_tpls(self):
        '''Test nodetemplate names.'''
        self.assertEqual(
            sorted(['vnf', 'dbBackend', 'mariaDbStorage',
             'dbBackendCp', 'dbBackendInternalCp', 'internalVl']),
            sorted([tpl.name for tpl in self.tosca.nodetemplates]))

        tpl_name = "dbBackend"
        expected_type = "tosca.nodes.nfv.Vdu.Compute"
        expected_properties = sorted(['name', 'description', 'vdu_profile', 'sw_image_data', 'boot_data'])
        expected_capabilities = sorted(['feature', 'monitoring_parameter', 'virtual_binding', 'virtual_compute'])
        expected_requirements = [{'virtual_storage': 'mariaDbStorage'}]

        for tpl in self.tosca.nodetemplates:
            if tpl_name == tpl.name:
                '''Test node type.'''
                self.assertEqual(tpl.type, expected_type)

                '''Test properties.'''
                self.assertEqual(
                    expected_properties,
                    sorted(tpl.get_properties().keys()))

                '''Test capabilities.'''
                self.assertEqual(
                    expected_capabilities,
                    sorted(tpl.get_capabilities().keys()))

                '''Test requirements.'''
                self.assertEqual(
                    expected_requirements, tpl.requirements)

    def test_node_inheritance_type(self):
        vnf_node = [
            node for node in self.tosca.nodetemplates
            if node.name == 'vnf'][0]
        self.assertTrue(
            vnf_node.is_derived_from("mycompany.nodes.nfv.SunshineDB.1_0.1_0"))
        self.assertTrue(
            vnf_node.is_derived_from("tosca.nodes.nfv.VNF"))
        self.assertTrue(
            vnf_node.is_derived_from("tosca.nodes.Root"))

    def test_interfaces(self):
        vnf_node = [
            node for node in self.tosca.nodetemplates
            if node.name == 'vnf'][0]
        interfaces = vnf_node.interfaces
        self.assertEqual(1, len(interfaces))
        for interface in interfaces:
            if interface.name == 'instantiate':
                self.assertEqual('Scripts/install.sh',
                                 interface.implementation)
            else:
                raise AssertionError(
                    'Unexpected interface: {0}'.format(interface.name))
