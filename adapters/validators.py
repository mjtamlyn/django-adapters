from .exceptions import ValidationError


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
    NODE_ATTRS = frozenset({'name', 'inputs', 'outputs', 'dependencies', 'validate', 'validators'})
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
