from .exceptions import CycleError, ValidationError


class ValidationResult(object):
    def __init__(self, schema, data, errors=None):
        self.schema = schema
        self.data = data
        if errors is None:
            self.errors = []
        else:
            self.errors = errors

    @property
    def is_valid(self):
        return not self.errors


class Schema(object):
    def __init__(self, final_node):
        topological_order = [final_node]
        all_nodes = {final_node}
        nodes = {final_node}
        while nodes:
            node = nodes.pop()
            new_nodes = node.dependencies - all_nodes
            all_nodes.update(new_nodes)
            nodes.update(new_nodes)
            topological_order.extend(new_nodes)
        topological_order.reverse()

        nodes = {final_node}
        for i in range(len(all_nodes) + 1):
            node = nodes.pop()
            nodes.update(node.dependencies)
            if not nodes:
                break
        else:
            raise CycleError('cycle in validators')

        self._final_node = final_node
        self._all_nodes = all_nodes
        self._topological_order = topological_order

    def validate(self, data, **kwargs):
        failed_nodes = set()
        errors = []
        for node in self._topological_order:
            if any(d in failed_nodes for d in node.dependencies):
                failed_nodes.add(node)
            else:
                try:
                    new_data = node.validate(data, **kwargs)
                except ValidationError as e:
                    failed_nodes.add(node)
                    errors.append(e)
                else:
                    if new_data is not None:
                        data = new_data
        return ValidationResult(self, data, errors)
