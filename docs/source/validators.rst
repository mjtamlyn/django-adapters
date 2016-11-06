==========
Validation
==========

.. module:: adapters.validation


Validation Nodes
================

The main components of validation are instances of :class:`ValidationNode`. Each
node contains a bit of validation logic that operates on a predefined set of
data. Multiple nodes can be combined to a
:class:`~adapters.validation.ValidationTree` to build more complex validation
scenarios.

Example: User Validation
------------------------

You can create validation nodes by subclassing
:class:`~DeclarativeValidationNode`::

    class ValidateUsername(DeclarativeValidationNode):
        inputs = {'username'}

We start with specifying which fields the node expects as input in the
:attr:`~DeclarativeValidationNode.inputs` attribute. Here, the
``ValidateUsername`` node expects only an username. This is everything that is
needed to create a validation node. Of course, a validation node that doesn't
actually validate anything isn't particularly useful. So let's now define
validation functions::

    class ValidateUsername(DeclarativeValidationNode):
        inputs = {'username'}

        @staticmethod
        def validate_username_length(data, **kwargs):
            if len(data['username']) < 5:
                raise ValidationError(
                    'username must have at least 5 characters',
                    'username'
                )

        @staticmethod
        def validate_username_starts_with_capital_letter(data, **kwargs):
            if not data['username'][0].isupper():
                raise ValidationError(
                    'username must start with capital letter',
                    'username'
                )

The :attr:`DeclarativeValidationNode` class automatically picks up all methods
whose name starts with ``validate``. These methods should be static methods and
take at least the parameter ``data``. This parameter is a dictionary that
contains at least all the keys specified in
:attr:`~DeclarativeValidationNode.inputs`. The method can then raise a
:class:`~adapters.exceptions.ValidationError` if the validation should fail.
When data is validated on the node, all validation methods are called in the
order they were specified. We can test that like this::

    >>> ValidateUsername.validate({})
    Traceback (most recent call last):
        ...
    adapters.exceptions.ValidationError: ('missing data: username', None)
    >>> ValidateUsername.validate({'username': 'bob'})
    Traceback (most recent call last):
        ...
    adapters.exceptions.ValidationError: ('username must have at least 5 characters', 'username')
    >>> ValidateUsername.validate({'username': 'robert'})
    Traceback (most recent call last):
        ...
    adapters.exceptions.ValidationError: ('username must start with capital letter', 'username')
    >>> ValidateUsername.validate({'username': 'Robert'})
    {'username': 'Robert'}

A validation method can also modify ("coerce") the input data by either
modifying existing data or adding new values. To add new values, they have to be
added to the :attr:`~DeclarativeValidationNode.outputs` attribute. Also, the
names of validation methods that change the data should start with ``coerce``::

    class UppercaseUsername(DeclarativeValidationNode):
        inputs = {'username'}
        outputs = {'username', 'username_uppercase'}

        @staticmethod
        def coerce_username_upper(data, **kwargs):
            data['username_uppercase'] = data['username'].upper()
            return data

We can check that our node now actually generates the upper case version of the
username::

    >>> UppercaseUsername.validate({'username': 'foobar'})
    {'username': 'foobar', 'username_uppercase': 'FOOBAR'}

Now, the real power in validation nodes lies in the fact that they can *depend*
on each other. This enables you to have a hierarchy of many different of nodes
that can fail independently. Let's now create a new validation node
``ValidatePerson`` that depends on ``ValidateUsername`` and also defines some
validation methods itself::

    class ValidatePerson(DeclarativeValidationNode):
        dependencies = [ValidateUsername]
        inputs = {'username', 'name'}

        @staticmethod
        def validate_username_contains_initials(data, **kwargs):
            names = data['name'].split()
            initials = ''.join(name[0] for name in names)
            if initials.lower() not in data['username'].lower():
                raise ValidationError(
                    'username must contain initials of the name',
                    'username'
                )


Reference
---------

.. class:: ValidationNode

.. attribute:: ValidationNode.name

.. attribute:: ValidationNode.inputs

.. attribute:: ValidationNode.outputs

.. attribute:: ValidationNode.dependencies

.. method:: VaidationNode.validate(data, **kwargs)

.. class:: ValidatorListNode

.. method:: ValidatorListNode.validate(data, **kwargs)

.. class:: DeclarativeValidationNode

.. method:: DeclarativeValidationNode.validate(data, **kwargs)


Validation Tree
===============

Reference
---------

.. class:: ValidationTree

.. method:: ValidationTree.validate(data, **kwargs)

.. method:: ValidationTree.revalidate(result, updated_data, **kwargs)
