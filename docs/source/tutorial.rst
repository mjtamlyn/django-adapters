========
Tutorial
========

Adapters on their own (no chaining)
===================================

Just JSON
---------

.. code-block:: python


    from adapters import shortcuts as adapters

    adapter = adapters.json.Adapter()

    adapter.field_add(adapters.fields.String('name'))
    adapter.field_add(adapters.fields.Email('email', required=False))

    adapter.validators_add(
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

Declarative ? easy:

.. code-block:: python

    class YourJsonAdapter(adapters.json.Adapter):
        name = adapters.fields.String()
        email = adapters.fields.Email()

        name_email = adapters.Validator(
            lambda data: data['name'] in data['email'],
            'Your name must be in your email', # example is silly, but short !
        )

Just a form
-----------

.. code-block:: python

    from adapters import shortcuts as adapters

    adapter = adapters.django.Form()

    adapter.field_add(adapters.fields.String('name'))
    adapter.field_add(adapters.fields.Email('email', required=False))
    adapter.field_add(adapters.fields.MultipleChoice('hobbies',
        ('python', 'Python'),
        ('django', 'Django'),
        ('archery', 'Archery'),
    ))
    adapter.field_add(adapters.fields.Password('password'))
    adapter.field_add(adapters.fields.Password('password_confirm'))
    # alternative to adding fields would be: adapter.adapt(YourExistingForm)

    adapter.validators_add(
        lambda data: data['password'] == data['password_confirm'],
        'Passwords should be the same'
    )
    # alternative: validators_add(
    #     adapters.validators.ValueEqual('password_confirm', adapters.fields.Field('password')))

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

    from adapters import shortcuts as adapters

    class Person(models.Model):
        name = models.CharField(blank=False)

    adapter = adapters.django.Model(Person)
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

    from adapters import shortcuts as adapters
    from .models import Person

    model_adapter = adapters.django.Model(Person)
    model_adapter.adapt(Person())

    forms_adapter = adapters.django.Forms(model_adapter)
    assert form_adapter.fields == model_adapter.fields

    json_adapter = adapters.json.Adapter(model_adapter)
    assert json_adapter.fields == model_adapter.fields

    # another option, would be:
    # json_adapter = adapters.json.Adapter(forms_adapter)
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

    from adapters import shortcuts as adapters
    from .models import Person

    model_adapter = adapters.django.Model(Person)
    model_adapter.adapt(Person.objects.get(pk=1))

    assert model_adapter.initial = {'name': 'hello'}

With inline
-----------

.. code-block:: python

    from adapters import shortcuts as adapters
    from .models import Person, Pet

    pet_model_adapter = adapters.django.Relation(Person.pet_set)
    model_adapter = adapters.django.Model(Person, dict(
        pet_set=pet_model_adapter
    ))
    model_adapter.adapt(Person())

    form_adapter = adapters.django.Form(model_adapter)
    # rest is the same

But if you want to define your own form for the inline, it's the same pattern:

.. code-block:: python

    pet_form_adapter = adapters.List(adapters.django.Form(pet_model_adapter))
    form_adapter = adapters.django.FormsAdapter(model_adapter, dict(
        pet_set=pet_form_adapter,
    ))

With nested inline
------------------

.. code-block:: python

    from adapters import shortcuts as adapters
    from .models import Person, Pet, Toy

    toy_model_adapter = adapters.django.Model(Pet.toy_set)
    pet_model_adapter = adapters.django.ModelListAdapter(Person.pet_set, dict(
        toy_set=adapter.List(toy_model_adapter),
    ))
    model_adapter = adapters.django.Model(Person, dict(
        pet_set=adapters.List(pet_model_adapter)
    ))
    # should work both in create and update mode
    model_adapter.adapt(Person.objects.filter(pk=1) or Person())

    form_adapter = adapters.django.Form(model_adapter)
    json_adapter = adapters.json.Adapter(model_adapter)
    # rest is the same

But if we want to override defaults, same as above:

.. code-block:: python

    toy_json_adapter = adapters.json.Adapter(toy_model_adapter)
    pet_json_adapter = adapters.json.Adapter(pet_model_adapter, dict(
        toy_set=adapters.List(toy_json_adapter),
    ))
    json_adapter = adapters.json.Adapter(model_adapter, dict(
        pet_set=adapters.List(pet_json_adapter),
    ))


    toy_form_adapter = adapters.django.Form(toy_model_adapter)
    pet_form_adapter = adapters.django.Form(pet_model_adapter, dict(
        toy_set=adapters.List(toy_form_adapter),
    ))
    form_adapter = adapters.django.Form(model_adapter, dict(
        pet_set=adapters.List(pet_form_adapter),
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

    from adapters import shortcuts as adapters

    # for the example use the base adapter which just deals with the schema and
    # data
    adapter = adapters.Adapter()

    adapter.field_add(adapters.fields.Choice('platform', (
        ('linux', 'Linux'),
        ('windows', 'Windows'),
    )))
    adapter.field_add(adapters.fields.Choice('service', (
        ('support', 'Support'),
        ('format', 'Format'),
    ))

    adapter.mutation_add(
        adapters.mutations.ChoiceRemove(
            'service', ['support'],
        ),
        conditions=[
            adapters.validators.ValueEqual('platform', 'windows'),
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

    adapter.mutation_add(
        adapters.mutations.FieldRemove('service'),
        conditions=[
            adapters.validators.ValueEqual('platform', 'windows'),
        ]
    )

    # Should play mutations before executing validation
    adapter.validate({'service': 'support', 'platform': 'windows'})

    assert adapter.errors == dict(
        non_field=['support is not a field if platform is windows'],
    )

Dynamic fields
--------------

.. code-block:: python

    from adapters import shortcuts as adapters

    adapter = adapters.django.FormsAdapter()

    adapter.field_add(adapters.fields.Choice('role', (
        ('archer', 'Archer'),
        ('musician', 'Musician'),
    ))
    adapter.field_add(
        adapters.fields.django.ModelMultipleChoice('hobbies', Hobby.objects.all())
    )
    adapter.mutation_add(
        adapters.mutations.ModelChoice(
            'hobbies',
            lambda a: Hobby.objects.filter(
                role=a.processed_data['role']
            )
        )
    )

This means that if there is any frontend, it should refresh "hobbies" list
every time a value changes, and clear the field value if set and incompatible.

If we want to declare which field has that side effect and update the hobbies
list only when that field changes:

.. code-block:: python

    adapter.mutation_add(
        adapters.mutations.ModelChoice(
            'hobbies',
            lambda a: Hobby.objects.filter(
                role=a.processed_data['role']
            ),
            triggers=adapters.events.Input('role'),
        )
    )

Or, we could also have a higher level mutation which can do this with less
code:

.. code-block:: python

    adapter.mutation_add(
        adapters.mutations.ModelChoiceFilter(
            'hobbies', # field to mutate
            'role', # filter argument name
            'role', # field name for filter argument value
        )
    )

Or even, DRYer:

.. code-block:: python

    adapter.mutation_add(
        adapters.mutations.ModelChoiceFilter(
            'hobbies', # field to mutate
            'role', # one arg only ? will do role=data['role'] !
        )
    )

With autocompletion please dear:

.. code-block:: python

    from adapters import shortcuts as adapters
    from .models import Person

    model_adapter = adapters.django.ModelAdapter(Person)
    form_adapter = adapters.django.FormsAdapter(model_adapter)

    adapter.mutation_add(
        adapters.mutations.ModelChoice(
            'hobbies',
            lambda a: Hobby.objects.filter(
                role=a.processed_data['role']
            )
        )
    )

    # this will add field on form_adapter, but leave model_adapter's generated
    # field:
    form_adapter.field_add(
        adapters.fields.django.ModelMultipleAutocomplete('hobbies', Hobby.objects.all())
    )

Level 3 Hacking API Daydream
============================

Hooooking schema declaration !
------------------------------

Your app provides a widget with splidid.js, in splindid/apps.py you add:

.. code-block:: python

    from adapters.signals import field_initialize

    def splindid_field_initialize(sender, field, **kwargs):
        autocomplete_url = splindid.find_url_for_model(model)

        if autocomplete_url:
            # decorate field with SplendidField
            return SplindidField(field, autocomplete_url)

    # already a little exciting
    field_initialize.connect(splindid_field_initialize,
        sender=adapters.django.ModelChoiceField)

Mind blowing declarative API !
------------------------------

.. code-block:: python

    class YourFormAdapter(adapters.django.adapters.Model):
        class Meta:
            model = Order

        def field_initialize(self, field):
            """This is called by Adapter every time a field is added.

            And a field can be added with field_add(), but also if a parent
            adapter is passed to __init__() !
            """
            super().field_initialize(field)

        name = adapters.fields.String(help_text='Your real name')

        name_email = adapters.Validator(
            lambda data: data['name'] in data['email'],
            'Your name must be in your email', # example is silly, but short !
        )

        # Comply with
        #
        #    Order.limit_choices_to =
        #       lambda self: Service.objects.filter(platform=self.platform)
        #
        # oh god i'm excited to hack client side for this **once** **and**
        # **for** **all**
        service_filter = adapters.mutations.ModelChoiceFilter('platform', 'service')
