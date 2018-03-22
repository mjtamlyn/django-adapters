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

To actually run the validation on a node, we first have to create a tree. This
is necessary even if there is only one node! The
:meth:`~ValidationNode.make_tree()` method does exactly that::

    >>> tree = ValidateUsername.make_tree()

Now we can use the tree to validate data by calling the
:meth:`~ValidationTree.validate()` method. It returns a
:class:`ValidationResult` that tells us if the validation failed::

    >>> result = tree.validate({})
    >>> result.is_valid
    False
    >>> result.errors
    [adapters.exceptions.ValidationError: ('missing data: username', None)]

    >>> result = tree.validate({'username': 'bob'})
    >>> result.is_valid
    False
    >>> result.errors
    [adapters.exceptions.ValidationError: ('username must have at least 5 characters', 'username')]

    >>> result = tree.validate({'username': 'robert'})
    >>> result.is_valid
    False
    >>> result.errors
    [adapters.exceptions.ValidationError: ('username must start with capital letter', 'username')]

    >>> result = tree.validate({'username': 'Robert'})
    >>> result.is_valid
    True
    >>> result.errors
    []
    >>> result.data
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

    >>> tree = UppercaseUsername.make_tree()
    >>> result = tree.validate({'username': 'foobar'})
    >>> result.data
    {'username': 'foobar', 'username_uppercase': 'FOOBAR'}

Now, the real power in validation nodes lies in the fact that they can *depend*
on each other. This enables you to have a hierarchy of many different nodes that
can fail independently. Let's now create a new validation node
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

Again, we have to create a tree and then call the
:meth:`~ValidationTree.validate()` method on it::

    >>> tree = ValidatePerson.make_tree()
    >>> result = tree.validate({'username': 'FB1234', 'name': 'Foo Bar'})
    >>> result.is_valid
    True

Of course, it gets more interesting when the validation fails::

    >>> result = tree.validate({'username': 'fb1234'})
    >>> result.is_valid
    False
    >>> result.errors
    [adapters.exceptions.ValidationError('username must start with capital letter', 'username')]

Here the validation on the node ``ValidateUsername`` failed and generated the
error you see. Because the first node failed and ``ValidatePerson`` depends on
it, ``ValidatePerson``'s validation was not executed. ::

    >>> result = tree.validate({'username': 'FB1234'})
    >>> result.is_valid
    False
    >>> result.errors
    [adapters.exceptions.ValidationError('missing data: name', None)]

Now the validation on ``ValidateUsername`` was successful, so the validation
continued to ``ValidateName`` and then failed there. Another way to "retry"
validation is to use the :meth:`~ValidationTree.revalidate()` method. In the
following example we use `result` from the previous one::

    >>> result = tree.revalidate(result, {'name': 'Bar Baz'})
    >>> result.is_valid
    False
    >>> result.errors
    [adapters.exceptions.ValidationError('username must contain initials of the name', 'username')]

In that example using :meth:`~ValidationTree.revalidate()` actually skipped the
``ValidateUsername`` node entirely since it was already validated before. And
finally we can make the result valid again::

    >>> result = tree.revalidate(result, {'name': 'Foo Bar'})
    >>> result.is_valid
    True
    >>> result.data
    {'username': 'FB1234', 'name': 'Foo Bar'}


Reference
---------

.. class:: ValidationNode

.. attribute:: ValidationNode.name

.. attribute:: ValidationNode.inputs

.. attribute:: ValidationNode.outputs

.. attribute:: ValidationNode.dependencies

.. method:: ValidationNode.make_tree()

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

.. class:: ValidationResult

.. attribute:: ValidationResult.is_valid
