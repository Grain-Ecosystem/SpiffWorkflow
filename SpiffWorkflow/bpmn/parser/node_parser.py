from SpiffWorkflow.bpmn.parser.ValidationException import ValidationException
from .util import xpath_eval, first

CAMUNDA_MODEL_NS = 'http://camunda.org/schema/1.0/bpmn'

class NodeParser:

    def __init__(self, node, filename, doc_xpath, lane=None):

        self.node = node
        self.filename = filename
        self.doc_xpath = doc_xpath
        self.xpath = xpath_eval(node)
        self.lane = self._get_lane() or lane
        self.position = self._get_position() or {'x': 0.0, 'y': 0.0}
        self.group = self._get_group()

    def get_id(self):
        return self.node.get('id')
    
    def parse_condition(self, sequence_flow):
        xpath = xpath_eval(sequence_flow)
        expression = first(xpath('.//bpmn:conditionExpression'))
        return expression.text if expression is not None else None

    def parse_documentation(self, sequence_flow=None):
        xpath = xpath_eval(sequence_flow) if sequence_flow is not None else self.xpath
        documentation_node = first(xpath('.//bpmn:documentation'))
        return None if documentation_node is None else documentation_node.text

    def parse_incoming_data_references(self):
        specs = []
        for name in self.xpath('.//bpmn:dataInputAssociation/bpmn:sourceRef'):
            ref = first(self.doc_xpath(f".//bpmn:dataObjectReference[@id='{name.text}']"))
            if ref is not None and ref.get('dataObjectRef') in self.process_parser.spec.data_objects:
                specs.append(self.process_parser.spec.data_objects[ref.get('dataObjectRef')])
            else:
                raise ValidationException(f'Cannot resolve dataInputAssociation {name}', self.node, self.filename)
        return specs

    def parse_outgoing_data_references(self):
        specs = []
        for name in self.xpath('.//bpmn:dataOutputAssociation/bpmn:targetRef'):
            ref = first(self.doc_xpath(f".//bpmn:dataObjectReference[@id='{name.text}']"))
            if ref is not None and ref.get('dataObjectRef') in self.process_parser.spec.data_objects:
                specs.append(self.process_parser.spec.data_objects[ref.get('dataObjectRef')])
            else:
                raise ValidationException(f'Cannot resolve dataOutputAssociation {name}', self.node, self.filename)
        return specs

    def parse_extensions(self, node=None):
        extensions = {}
        extra_ns = {'camunda': CAMUNDA_MODEL_NS}
        xpath = xpath_eval(self.node, extra_ns) if node is None else xpath_eval(node, extra_ns)
        extension_nodes = xpath( './/bpmn:extensionElements/camunda:properties/camunda:property')
        for node in extension_nodes:
            extensions[node.get('name')] = node.get('value')
        return extensions

    def _get_lane(self):
        noderef = first(self.doc_xpath(f".//bpmn:flowNodeRef[text()='{self.get_id()}']"))
        if noderef is not None:
            return noderef.getparent().get('name')

    def _get_position(self):
        bounds = first(self.doc_xpath(f".//bpmndi:BPMNShape[@bpmnElement='{self.get_id()}']//dc:Bounds"))
        if bounds is not None:
            return {'x': float(bounds.get('x', 0)), 'y': float(bounds.get('y', 0))}

    def _get_group(self):
        shape = first(self.doc_xpath(f".//bpmndi:BPMNShape[@bpmnElement='{self.get_id()}']//dc:Bounds"))
        if shape is not None:
            node_bounds = {
                'x': float(shape.get('x', 0)),
                'y': float(shape.get('y', 0)),
                'w': float(shape.get('width', 0)),
                'h': float(shape.get('height', 0))}

        p = self.xpath('..')[0]

        children = p.getchildren()
        for child in children:
            if 'group' in child.tag:
                g_id = child.get('id')
                cref = child.get('categoryValueRef')
                cat_val = first(self.doc_xpath(f".//bpmn:categoryValue[@id='{cref}']"))
                group_name = cat_val.get('value')
                bounds = first(self.doc_xpath(f".//bpmndi:BPMNShape[@bpmnElement='{g_id}']//dc:Bounds"))
                x = float(bounds.get('x', 0))
                y = float(bounds.get('y', 0))
                w = float(bounds.get('width', 0))
                h = float(bounds.get('height', 0))

                if node_bounds['x'] > x and node_bounds['x']+node_bounds['w'] < (x+w) and node_bounds['y'] > y and node_bounds['y']+node_bounds['h'] < (y+h):
                    return group_name

        return "no group"