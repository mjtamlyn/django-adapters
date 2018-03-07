========
Tutorial
========

Adapters on their own (no chaining)
===================================

Just JSON
---------

.. code-block:: python


    from adapters import shortcuts as adaters

    adapter = adapters.JSONAdapter()

    adapter.add_field(adapters.String('name'))
    adapter.add_field(adapters.Email('email', required=False))

    adapter.add_validation(
        lambda data: data['name'] in data['email'],
        'Your name must be in your email', # example is silly, but short !
    )

    adapter.validate({'name': 'foo', 'email': 'bar@'})

    assert adapter.errors == dict(
        non_field=['Your name must be in your email']
        email=['Must be a valid email'],
    )

    adapter.validate({'name': 'foo', 'email': 'foo@example.com'})

    assert not adapter.errors

    # doesn't do anything, we don't have any persistence adapter in this example !
    # but, you could send an email or something if you want in your subclass ;)
    adapter.process()

    adapter.output()  # output in JSON


Just a form
-----------

.. code-block:: python

    from adapters import shortcuts as adaters

    adapter = adapters.DjangoFormsAdapter()

    adapter.add_field(adapters.String('name'))
    adapter.add_field(adapters.Email('email', required=False))
    adapter.add_field(adapters.MultipleChoice('hobbies',
        ('python', 'Python'),
        ('django', 'Django'),
        ('archery', 'Archery'),
    ))
    adapter.add_field(adapters.Password('password'))
    adapter.add_field(adapters.Password('password_confirm'))

    adapter.add_validation(
        lambda data: data['password'] == data['password_confirm'],
        'Passwords should be the same'
    )

    adapter.validate({
        'name': 'hello',
        'email': 'foo',
        'hobbies': ['archery', 'music'],
        'password': 'foo',
        'password_confirm': 'bar'
    })

    assert adapter.errors == dict(
        non_field=['Passwords should be the same'],
        hobbies=['music is not a valid choice'],
        email=['Must be a valid email'],
    )

    adapter.validate({
        'name': 'hello',
        'hobbies': ['archery', 'django'],
        'password': 'foo',
        'password_confirm': 'foo'
    })

    assert not adapter.errors

    # doesn't do anything, we don't have any persistence adapter in this example !
    # but, you could send an email or something if you want in your subclass ;)
    adapter.process()

    adapter.layout = (
        ('name', 'email'),
        'password',
        'password_confirm',
    )
    form.output() # HTML form !

Just model
----------

.. code-block:: python

    from adapters import shortcuts as adaters

    class Person(models.Model):
        name = models.CharField(blank=False)

    adapter = adapters.DjangoModelAdapter(Person)
    adapter.adapt(Person())

    adapter.validate({
        'name': '',
    })

    assert adapter.errors == dict(
        name=['Must not be blank'],
    )

    adapter.validate({
        'name': 'hello',
    })

    assert not adapter.errors

    result = adapter.process()
    assert result.pk
    assert respolt.name == 'hello'

Chaining adapters
=================

All the fun happens when composing adapters with each other and build a tree.

Create
------

.. code-block:: python

    from adapters import shortcuts as adaters
    from .models import Person

    model_adapter = adapters.DjangoModelAdapter(Person)
    model_adapter.adapt(Person())

    forms_adapter = adapters.DjangoFormsAdapter(model_adapter)
    assert form_adapter.fields == model_adapter.fields

    json_adapter = adapters.JSONAdapter(model_adapter)
    assert json_adapter.fields == model_adapter.fields

    # another option, would be:
    # json_adapter = adapters.JSONAdapter(forms_adapter)
    # in this example it would result in the same

    if request.method == 'POST':
        # We'll switch presentational adapter here, cause they both have the
        # same persistence adapter so for db business logic we'll have the same
        if request.is_ajax():
            adapter = json_adapter
            data = request.json()
        else:
            adapter = forms_adapter
            data = request.POST

        # should propagate in the adapter chain ! yay
        processed_data, errors = adapter.validate(data)

        if not errors:
            result = adapter.process(adapter.processed_data)
            assert result.pk # you have created a model


    if request.is_ajax():
        # return HTML form string with your layout
        return forms_adapter.output(layout)
    else:
        # return JSON interface, errors and all
        return json_adapter.output()

Update
------

.. code-block:: python

    from adapters import shortcuts as adaters
    from .models import Person

    model_adapter = adapters.DjangoModelAdapter(Person)
    model_adapter.adapt(Person.objects.get(pk=1))

    assert model_adapter.initial = {'name': 'hello'}

With inline
-----------

.. code-block:: python

    from adapters import shortcuts as adaters
    from .models import Person, Pet

    pet_model_adapter = adapters.DjangoModelListAdapter(Person.pet_set)
    model_adapter = adapters.DjangoModelAdapter(Person, dict(
        pet_set=pet_model_adapter
    ))
    model_adapter.adapt(Person())

    form_adapter = adapters.DjangoFormsAdapter(model_adapter)
    # rest is the same

But if you want to define your own form for the inline, it's the same pattern:

.. code-block:: python

    pet_form_adapter = adapters.DjangoFormListAdapter(pet_model_adapter)
    form_adapter = adapters.DjangoFormsAdapter(model_adapter, dict(
        pet_set=pet_form_adapter
    ))

Same principle for JSONAdapter.

With nested inline
------------------

.. code-block:: python

    from adapters import shortcuts as adaters
    from .models import Person, Pet, Toy

    toy_model_adapter = adapters.DjangoModelListAdapter(Pet.toy_set)
    pet_model_adapter = adapters.DjangoModelListAdapter(Person.pet_set, dict(
        toy_set=toy_model_adapter,
    ))
    model_adapter = adapters.DjangoModelAdapter(Person, dict(
        pet_set=pet_model_adapter
    ))
    # should work both in create and update mode
    model_adapter.adapt(Person.objects.filter(pk=1) or Person())

    form_adapter = adapters.DjangoFormsAdapter(model_adapter)
    json_adapter = adapters.JSONAdapter(model_adapter)
    # rest is the same

But if we want to override defaults, same as above:

.. code-block:: python

    toy_json_adapter = adapters.JSONListAdapter(toy_model_adapter)
    pet_json_adapter = adapters.JSONListAdapter(pet_model_adapter, dict(
        toy_set=toy_json_adapter,
    ))
    json_adapter = adapters.JSONAdapter(model_adapter, dict(
        pet_set=pet_json_adapter,
    ))

    toy_json_adapter = adapters.DjangoFormListAdapter(toy_model_adapter)
    pet_json_adapter = adapters.DjangoFormListAdapter(pet_model_adapter, dict(
        toy_set=toy_json_adapter,
    ))
    json_adapter = adapters.DjangoFormAdapter(model_adapter, dict(
        pet_set=pet_json_adapter,
    ))

Schema Mutations
================

Going beyond what you've ever seen, inspired from schematics blacklist feature,
in an extensible way like yourlabs/facond.

Removing a choice based on the value of another field
-----------------------------------------------------

Consider such a Linux shop which offers support and format of computers with
Linux, and only Format for computers with Windows, they make a beautiful Web
2.0 form::

    Platform: [ ] Linux [ ] Windows
    Service: [ ] Support [ ] Format

The form should look either like this::

    Platform: [ ] Linux [X] Windows
    Service: [ ] Format

Or that::

    Platform: [X] Linux [ ] Windows
    Service: [ ] Support [ ] Format

But, God forbids, a user shouldn't **ever** be able to select both "Windows"
and "Support", we don't want this to happen **or kittens will die**::

    Platform: [ ] Linux [X] Windows
    Service: [X] Support [ ] Format

We want to ensure this behaves properly during initial rendering,
validation, rerendering, and of course live in the browser.<Paste>

.. code-block:: python

    from adapters import shortcuts as adaters

    # for the example use the base adapter which just deals with the schema and
    # data
    adapter = adapters.Adapter()

    adapter.add_field(adapters.Choice('platform', (
        ('linux', 'Linux'),
        ('windows', 'Windows'),
    )))
    adapter.add_field(adapters.Choice('service', (
        ('support', 'Support'),
        ('format', 'Format'),
    ))

    adapter.add_mutation(
        adapters.ChoiceExcludeMutation(
            'service', ['support'],
        ),
        conditions=[
            adapters.ValueEqual('platform', 'windows'),
        ]
    )

    # Should play mutations before executing validation
    adapter.validate({'service': 'support', 'platform': 'windows'})

    assert adapter.errors == dict(
        service=['support is not a valid choice if platform is windows'],
        platform=['platform is not a valid choice if service is windows'],
    )

Removing a field based on the value of another field
----------------------------------------------------

Another example, to remove field "service" for platform=windows, in this case
we have 2 possibilities::

    Platform: [X] Linux [ ] Windows
    Service: [ ] Format [ ] Support

Or::

    Platform: [ ] Linux [X] Windows

So, we have the same as above, except we add a different mutation:

.. code-block:: python

    adapter.add_mutation(
        adapters.FieldRemoveMutation('service'),
        conditions=[
            adapters.ValueEqual('platform', 'windows'),
        ]
    )

    # Should play mutations before executing validation
    adapter.validate({'service': 'support', 'platform': 'windows'})

    assert adapter.errors == dict(
        non_field=['support is not a field if platform is windows'],
    )
