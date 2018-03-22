from .exceptions import CycleError, ValidationError


class ValidationNode(object):
    def __init__(self, *, name=None, inputs=frozenset(), outputs=frozenset(), dependencies=frozenset()):
        self.name = name
        self.inputs = frozenset(inputs)
        self.outputs = frozenset(outputs)
        self.dependencies = frozenset(dependencies)

        if not self.inputs:
            for dep in self.dependencies:
                self.inputs = self.inputs.union(dep.inputs)
        if not self.outputs:
            self.outputs = self.inputs

    def __repr__(self):
        return (
            '{}(inputs={!r}, outputs={!r}, name={!r})'
            ''.format(self.__class__.__name__, self.inputs, self.outputs,
                      self.name)
        )

    def make_tree(self):
        return ValidationTree(self)

    def validate(self, data, **kwargs):
        raise NotImplementedError


class ValidatorListNode(ValidationNode):
    def __init__(self, *, validators=None, **kwargs):
        super().__init__(**kwargs)
        self.validators = list(validators)

    def __repr__(self):
        return (
            '{}(inputs={!r}, outputs={!r}, validators={!r}, name={!r})'
            ''.format(self.__class__.__name__, self.inputs, self.outputs,
                      self.validators, self.name)
        )

    def validate(self, data, **kwargs):
        if not self.inputs.issubset(data.keys()):
            missing_keys = ', '.join(self.inputs.difference(data.keys()))
            raise ValidationError('missing data: {}'.format(missing_keys))

        data = data.copy()
        for validator in self.validators:
            new_data = validator(data, **kwargs)
            if new_data is not None:
                data = new_data

        for key in self.outputs - data.keys():
            data[key] = None

        return data


DeclarativeValidationNode = None


class DeclarativeValidationNodeMeta(type):
    NODE_ATTRS = frozenset(
        {'name', 'inputs', 'outputs', 'dependencies', 'make_tree', 'validate', 'validators'}
    )
    DECLARATIVE_ATTRS = frozenset({'inputs', 'outputs', 'dependencies'})

    def __new__(mcs, name, bases, attrs):
        if DeclarativeValidationNode is None:
            # creating DeclarativeValidationNode class
            return super().__new__(mcs, name, bases, attrs)

        node_kwargs = {'name': name}
        declarative_attrs = {}
        for attr in mcs.DECLARATIVE_ATTRS:
            node_kwargs[attr] = set()
            if attr in attrs:
                declarative_attrs[attr] = attrs.pop(attr)
        cls = super().__new__(mcs, name, bases, attrs)
        cls._declarative_attrs = declarative_attrs

        for base in reversed(cls.__mro__):
            if '_declarative_attrs' in base.__dict__:
                for attr in mcs.DECLARATIVE_ATTRS:
                    node_kwargs[attr].update(base._declarative_attrs.get(attr, frozenset()))

        validators = []
        if hasattr(cls, 'validators'):
            validators.extend(cls.validators)
        for attr in dir(cls):
            if attr.startswith('validate') or attr.startswith('coerce'):
                method = getattr(cls, attr)
                if callable(method):
                    validators.append(method)
        node_kwargs['validators'] = validators

        cls._node = ValidatorListNode(**node_kwargs)
        return cls

    def __call__(cls):
        raise TypeError("can't instantiate {}".format(cls.__name__))

    def __hash__(cls):
        if cls is DeclarativeValidationNode:
            return super().__hash__()
        else:
            return hash(cls._node)

    def __eq__(cls, other):
        if cls is other:
            return True
        elif cls is DeclarativeValidationNode:
            return False
        else:
            return cls._node == other

    def __getattr__(cls, name):
        if name in cls.NODE_ATTRS:
            return getattr(cls._node, name)
        else:
            return super().__getattr__(name)


class DeclarativeValidationNode(object, metaclass=DeclarativeValidationNodeMeta):
    pass


class ValidationResult(object):
    def __init__(self, tree, data, errors=None, failed_nodes=frozenset()):
        self.tree = tree
        self.data = data
        if errors is None:
            self.errors = []
        else:
            self.errors = errors
        self.failed_nodes = frozenset(failed_nodes)

    @property
    def is_valid(self):
        return not self.errors

    def fields_with_errors(self):
        fields = set()
        for error in self.errors:
            fields.add(error.field)
        return fields


class ValidationTree(object):
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
        return ValidationResult(self, data, errors, failed_nodes)

    def revalidate(self, result, updated_data, **kwargs):
        data = result.data.copy()
        data.update(updated_data)
        failed_nodes = set()
        errors = []
        for node in self._topological_order:
            if (node not in result.failed_nodes and
                    not any(field in node.inputs for field in updated_data.keys())):
                continue
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
        return ValidationResult(self, data, errors, failed_nodes)
