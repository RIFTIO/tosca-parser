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

from toscaparser.common.exception import ExceptionCollector
from toscaparser.common.exception import InvalidNodeTypeError
from toscaparser.common.exception import MissingDefaultValueError
from toscaparser.common.exception import MissingRequiredFieldError
from toscaparser.common.exception import MissingRequiredInputError
from toscaparser.common.exception import MissingRequiredOutputError
from toscaparser.common.exception import TOSCAException
from toscaparser.common.exception import UnknownFieldError
from toscaparser.common.exception import UnknownOutputError
from toscaparser.elements.nodetype import NodeType
from toscaparser.properties import Property
from toscaparser.utils.gettextutils import _

log = logging.getLogger('tosca-parser')


class SubstitutionMappings(object):
    '''SubstitutionMappings class declaration

    SubstitutionMappings exports the topology template as an
    implementation of a Node type.
    '''

    SECTIONS = (NODE_TYPE, REQUIREMENTS, CAPABILITIES, PROPERTIES, INTERFACES) = \
               ('node_type', 'requirements', 'capabilities', 'properties', 'interfaces')

    OPTIONAL_OUTPUTS = ['tosca_id', 'tosca_name', 'state']

    def __init__(self, sub_mapping_def, nodetemplates, inputs, outputs,
                 sub_mapped_node_template, custom_defs):
        self.nodetemplates = nodetemplates
        self.sub_mapping_def = sub_mapping_def
        TOSCAException.set_context(self.type, "substitution_mapping")
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.sub_mapped_node_template = sub_mapped_node_template
        self.custom_defs = custom_defs or {}
        self._validate()

        self.type_definition = NodeType(self.type, custom_defs)
        self._properties = None
        self._capabilities = None
        self._requirements = None
        self._interfaces = None
        TOSCAException.reset_context()

    @property
    def type(self):
        if self.sub_mapping_def:
            return self.sub_mapping_def.get(self.NODE_TYPE)

    @classmethod
    def get_node_type(cls, sub_mapping_def):
        if isinstance(sub_mapping_def, dict):
            return sub_mapping_def.get(cls.NODE_TYPE)

    @property
    def node_type(self):
        return self.sub_mapping_def.get(self.NODE_TYPE)

    @property
    def capabilities(self):
        return self.sub_mapping_def.get(self.CAPABILITIES)

    @property
    def requirements(self):
        return self.sub_mapping_def.get(self.REQUIREMENTS)

    @property
    def interfaces(self):
        return self.sub_mapping_def.get(self.INTERFACES)

    @property
    def node_definition(self):
        return NodeType(self.node_type, self.custom_defs)

    # Needed to support TOSCA Simple YAML 1.2
    def get_properties_objects(self):
        '''Return properties objects for this template.'''
        if self._properties is None:
            self._properties = self._create_properties()
        return self._properties

    def get_properties(self):
        '''Return a dictionary of property name-object pairs.'''
        return {prop.name: prop
                for prop in self.get_properties_objects()}

    def get_property_value(self, name):
        '''Return the value of a given property name.'''
        props = self.get_properties()
        if props and name in props.keys():
                return props[name].value

    def _create_properties(self):
        props = []
        properties = self.type_definition.get_value(self.PROPERTIES,
                                                    self.sub_mapping_def) or {}
        for name, value in properties.items():
            props_def = self.type_definition.get_properties_def()
            if props_def and name in props_def:
                prop = Property(name, value,
                                props_def[name].schema, self.custom_defs)
                props.append(prop)
        for p in self.type_definition.get_properties_def_objects():
            if p.default is not None and p.name not in properties.keys():
                prop = Property(p.name, p.default, p.schema, self.custom_defs)
                props.append(prop)
        return props

    def __str__(self):
        s = "Substitution Mappings:\n"
        s += "\tproperties: {}\n".format({prop.name: prop.value
                for prop in self.get_properties_objects()})
        s += "\ttype: {}\n".format(self.type)
        s += "\trequirements: {}\n".format(self.requirements)
        s += "\tcapabilites: {}\n".format(self.capabilities)
        s += "\tinterfaces: {}\n".format(self.interfaces)
        s += "\tinputs: {}\n".format([str(inp) for inp in self.inputs])
        return s


    def _validate(self):
        # Basic validation
        self._validate_keys()
        self._validate_type()

        # SubstitutionMapping class syntax validation
        self._validate_inputs()
        self._validate_capabilities()
        self._validate_requirements()
        self._validate_outputs()

    def _validate_keys(self):
        """validate the keys of substitution mappings."""
        for key in self.sub_mapping_def.keys():
            if key not in self.SECTIONS:
                ExceptionCollector.appendException(
                    UnknownFieldError(what=_('SubstitutionMappings'),
                                      field=key))

    def _validate_type(self):
        """validate the node_type of substitution mappings."""
        node_type = self.sub_mapping_def.get(self.NODE_TYPE)
        if not node_type:
            ExceptionCollector.appendException(
                MissingRequiredFieldError(
                    what=_('SubstitutionMappings used in topology_template'),
                    required=self.NODE_TYPE))

        node_type_def = self.custom_defs.get(node_type)
        if not node_type_def:
            ExceptionCollector.appendException(
                InvalidNodeTypeError(what=node_type))

    def _validate_inputs(self):
        """validate the inputs of substitution mappings.

        The inputs defined by the topology template have to match the
        properties of the node type or the substituted node. If there are
        more inputs than the substituted node has properties, default values
        must be defined for those inputs.
        """

        all_inputs = set([input.name for input in self.inputs])
        required_properties = set([p.name for p in
                                   self.node_definition.get_properties_def_objects()
                                   if p.required and p.default is None])
        # Must provide inputs for required properties of node type.
        for property in required_properties:
            # Check property which is 'required' and has no 'default' value
            if property not in all_inputs:
                ExceptionCollector.appendException(
                    MissingRequiredInputError(
                        what=_('SubstitutionMappings with node_type ')
                        + self.node_type,
                        input_name=property))

        # If the optional properties of node type need to be customized by
        # substituted node, it also is necessary to define inputs for them,
        # otherwise they are not mandatory to be defined.
        customized_parameters = set(self.sub_mapped_node_template.get_properties().keys()
                                    if self.sub_mapped_node_template else [])
        all_properties = set([p.name for p in
                              self.node_definition.get_properties_def_objects()
                              if not p.required])
        for parameter in customized_parameters - all_inputs:
            if parameter in all_properties:
                ExceptionCollector.appendException(
                    MissingRequiredInputError(
                        what=_('SubstitutionMappings with node_type ')
                        + self.node_type,
                        input_name=parameter))

        # Additional inputs are not in the properties of node type must
        # provide default values. Currently the scenario may not happen
        # because of parameters validation in nodetemplate, here is a
        # guarantee.
        for input in self.inputs:
            if input.name in all_inputs - all_properties \
               and input.default is None:
                ExceptionCollector.appendException(
                    MissingDefaultValueError(
                        what=_('SubstitutionMappings with node_type ')
                        + self.node_type,
                        input_name=input.name))

    def _validate_capabilities(self):
        """validate the capabilities of substitution mappings."""

        # The capabilites must be in node template wchich be mapped.
        tpls_capabilities = self.sub_mapping_def.get(self.CAPABILITIES)
        node_capabiliteys = self.sub_mapped_node_template.get_capabilities() \
            if self.sub_mapped_node_template else None
        for cap in node_capabiliteys.keys() if node_capabiliteys else []:
            if (tpls_capabilities and
                    cap not in list(tpls_capabilities.keys())):
                pass
                # ExceptionCollector.appendException(
                #    UnknownFieldError(what='SubstitutionMappings',
                #                      field=cap))

    def _validate_requirements(self):
        """validate the requirements of substitution mappings."""

        # The requirements must be in node template which is mapped.
        tpls_requirements = self.sub_mapping_def.get(self.REQUIREMENTS)
        node_requirements = self.sub_mapped_node_template.requirements \
            if self.sub_mapped_node_template else None
        log.debug("tpls req: {}, node req: {}".format(tpls_requirements, node_requirements))

        def process_req(req):
            log.debug("Node requirements: {}".format(req))
            if tpls_requirements:
                keys = []
                if isinstance(tpls_requirements, list):
                    for tp in tpls_requirements:
                        keys.extend(list(tp.keys()))
                else:
                    keys = list(tpls_requirements.keys())
                log.debug("Tpl keys: {}".format(keys))
                for req_key in req.keys():
                    if req_key in keys:
                        pass
                    else:
                        log.info("Unknown field Subs: {}".format(req))
                        ExceptionCollector.appendException(
                            UnknownFieldError(what='SubstitutionMappings',
                                              field=req))

        if isinstance(node_requirements, dict) or not node_requirements:
            for req in node_requirements if node_requirements else {}:
                process_req({req: node_requirements[req]})
        elif isinstance(node_requirements, list):
            for req in node_requirements:
                process_req(req)
        else:
            ExceptionCollector.appendException(
                UnknownFieldError(what='SubstitutionMappings',
                                  field='Requirements is not list or dict'))

    def _validate_outputs(self):
        """validate the outputs of substitution mappings.

        The outputs defined by the topology template have to match the
        attributes of the node type or the substituted node template,
        and the observable attributes of the substituted node template
        have to be defined as attributes of the node type or outputs in
        the topology template.
        """

        # The outputs defined by the topology template have to match the
        # attributes of the node type according to the specification, but
        # it's reasonable that there are more inputs than the node type
        # has properties, the specification will be amended?
        for output in self.outputs:
            if output.name not in self.node_definition.get_attributes_def():
                ExceptionCollector.appendException(
                    UnknownOutputError(
                        where=_('SubstitutionMappings with node_type ')
                        + self.node_type,
                        output_name=output.name))

        # The observable attributes of the substituted node template
        # have to be defined as attributes of the node type or outputs in
        # the topology template, the attributes in tosca.node.root are
        # optional.
        for attribute in self.node_definition.get_attributes_def():
            if attribute not in [output.name for output in self.outputs] \
               and attribute not in self.OPTIONAL_OUTPUTS:
                ExceptionCollector.appendException(
                    MissingRequiredOutputError(
                        what=_('SubstitutionMappings with node_type ')
                        + self.node_type,
                        output_name=attribute))
