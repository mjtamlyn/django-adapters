=========
Tutornial
=========

Single model
============

Create
------

.. code-block:: python

    from adapters import shortcuts as adaters
    from .models import Person

    model_adapter = adapters.DjangoModelAdapter(Person)
    model_adapter.adapt(Person())

    forms_adapter = adapters.DjangoFormsAdapter(model_adapter)
    json_adapter = adapters.JSONAdapter(model_adapter)

    if request.method == 'POST':
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

Update
------

.. code-block:: python

    from adapters import shortcuts as adaters
    from .models import Person

    model_adapter = adapters.DjangoModelAdapter(Person)
    model_adapter.adapt(Person.objects.get(pk=1))

With inline
===========

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
==================

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
