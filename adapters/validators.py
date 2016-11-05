from .exceptions import ValidationError


class ValidatorListNode(object):
    def __init__(self, inputs=None, outputs=None, validators=None, name=None):
        if inputs is None:
            self.inputs = frozenset()
        else:
            self.inputs = frozenset(inputs)
        if outputs is None:
            self.outputs = frozenset()
        else:
            self.outputs = frozenset(outputs)
        if validators is None:
            validators = []
        self.validators = list(validators)
        self.name = name
        self._dependencies = set()
        self._dependants = set()

    def __repr__(self):
        return (
            '{}(inputs={!r}, outputs={!r}, validators={!r}, name={!r})'
            ''.format(self.__class__.__name__, self.inputs, self.outputs,
                      self.validators, self.name)
        )

    def add_dependency(self, node):
        if node not in self._dependencies:
            self._dependencies.add(node)
            node.add_dependant(self)

    def add_dependant(self, node):
        if node not in self._dependants:
            self._dependants.add(node)
            node.add_dependency(self)

    @property
    def dependencies(self):
        return self._dependencies

    @property
    def dependants(self):
        return self._dependants

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
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)

        if DeclarativeValidationNode is None:
            # creating DeclarativeValidationNode class
            return

        node_kwargs = {'name': name}
        if hasattr(cls, 'inputs'):
            node_kwargs['inputs'] = cls.inputs
        elif hasattr(cls, 'depends'):
            inputs = set()
            for dependency in cls.depends:
                inputs.update(dependency._node.outputs)
            node_kwargs['inputs'] = inputs

        if hasattr(cls, 'outputs'):
            node_kwargs['outputs'] = cls.outputs
        else:
            node_kwargs['outputs'] = node_kwargs['inputs']

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

        if hasattr(cls, 'depends'):
            for dependency in cls.depends:
                cls._node.add_dependency(dependency)

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

    def add_dependency(cls, node):
        cls._node.add_dependency(node)

    def add_dependant(cls, node):
        cls._node.add_dependant(node)

    @property
    def dependencies(cls):
        return cls._node.dependencies

    @property
    def dependants(cls):
        return cls._node.dependants

    def validate(cls, data, **kwargs):
        return cls._node.validate(data, **kwargs)


class DeclarativeValidationNode(object, metaclass=DeclarativeValidationNodeMeta):
    pass
