========
Tutorial
========

What's the point
================

It seems to me that what adapters tries to do is invent a new pattern to
solve the kind of problems we usually deal with as developers:

- fetch data from some source, using various python libraries for example,
  converting settings into things like API urls and whatnot,
- make a friendly data submission interface striving to help the user fix his
  data input until valid, the more friendly it is, the less Humans will be
  waiting for our answers on how exactly it is usable: iterative validation
- process the valid data which means executing various steps, from writing a
  file to sending an email or triggering a channels job, and outputing
  something, an json dump, an html body, a response object, or something

What's the story
================

In short, we create a Payload that will traverse several steps, what happens
during a Step is defined by the Adapters attached to the Payload, how they are
going to be executed is defined by the Steps themselves.

Payload may have any attributes, but some are more common than others:

- instance,
- instances,
- initial,
- data,
- rendered,

You can attach Adapters to a Payload, but also map them to keys in case Payload
data expects a dict of data ... which become Payloads on their own, or attach
Adapters to Payload's list items in case it expects a List of data. Payloads
are infinitely recursive in theory.

Adapters can define any steps they want, but some are more common:

- instanciate, for example fetch some data, setup Payload instance,
- initialize, set initial data, for example from the Payload's instance,
- validate, fills up the Payload errors, but don't actually change data,
- clean, changes data as adapters see fit and fill up the Payload errors,
- process, save data and other kind of business logic,
- render, render some output like html or json,

If Payload is data, Adapters is a bunch of features, Steps is the orchestrator.

Getting started
===============

You can create a Payload from the factory::

    p = Payloads.factory(initial={'name': ''})

The factory figured we were going to deal with a dict Payload::

    assert 'Dict' in p.adapters.keys()

And maped a subPayload for the 'name' key with a string adapter::

    assert 'String' in p.map.name.adapters.keys()

Everytime we execute a step it will clone the Payload and execute the step on
it::

    assert p.steps.validate('foo') !== p
    assert p.steps.validate('foo').errors == {'self': ['Should be a dict!']}
    assert p.steps.validate({'name': ''}).errors == {'map': {'name': ['required!']}}

Now that we have a Payload map, we can create a django form::

    f = p.adapters.add('django.forms.Form')

Adding an adapter calls its post_add() method which allows it to issue Payload
or other adapter mutations based on introspection, that's why add() returns a
clone of the Payload::

    assert f.adapters.get('django.forms.Form').form == p.form
    assert 'django.forms.fields.CharField' in f.map.name.adapters.keys()

Both adapters of the Payload, share the same Payload::

    assert f.adapters.first().Payload == f.adapters.last().Payload == p
    assert f.adapters.first().Payload.map == f.map

We can also render the form using the form adapter::

    assert f.steps.render('html').rendered == '<an awesome form>'

But given the generic nature of adapters, it might as well return a response
from a request::

    f = f.adapters.add('django.views.generic.FormView', template_name='form.html')
    assert f.steps.process_request(request).response.status_code == 200

If we want a different form rendering::

    f = f.adapters.remove('django.forms.Form')
    f = f.adapters.add('elementUi.Form')

An adapter can be replaced with poney magic, in which case it's your
responsibility to clone first if you see fit::

    n = f.clone()
    n.map.name.adapters.String.required = False
    assert not n.validate({'name': ''}).errors

You can also reset adapters on a Payload for a specific step::

    n.clone().map.name.steps.validation.adapters = [
        is_numeric, cast_to_int, greater_than(0)]

Let's have another adapter for JSON::

    j = p.adapters.add('json.Adapter')
    assert j.validate('[]').errors == {'self': ['Must be dict']}
    assert not j.validate('{"name": "foo"}').errors

What about some friendly JSON api view like with DRF::

    j = j.adapters.add('json.DjangoRequestResponse')
    j.steps.process_request(request).response.status_code == 200

An adapter can proudly represent their family::

    adapters.register(DjangoModelAdapter)
    # that will attach when factoring a Payload with instance=djangomodel

And serve their dear users::

    p = Payloads.factory(instance=Person.objects.get(pk=1))

    assert 'DjangoModelAdapter' in p.adapters

    assert p.instance.pk == 1
    assert p.initial == {'name': 'sly'}

    # DjangoModelAdapter populated its .map from introspection of the model
    assert 'StringAdapter' in p.map.name.adapters

Custom adapters can mutate the Payload structure::

    # Example to add an adapter which will just remove fields from map
    p = p.add(UnauthenticatedUserPersonFields)

    class UnauthenticatedUserPersonFields(AdapterInterface):
        def post_add(self):
            # Adding an adapter calls its post_add() method, if exists
            del self.map.admin_only_field_name

Or just add custom validation::

    class UnauthenticatedUserPersonFields(AdapterInterface):
        def validate(self):
            if not self.Payload.request.user.is_authenticated:
                if 'admin_only_field_name' in self.Payload.request.POST:
                    self.errors.append('Posting unauthorized field!')

Payload also supports list maping, in which case map will be a list of adapters
to execute against each item in the list::

    p = Payload.factory(relation=person.pet_set)
    assert 'RelatedFieldAdapter' in p.adapters # for the list
    # map is not a dict ! but a list:
    assert 'DjangoModelAdapter' in p.map.adapters # for items

Any attribute which is an adapter will be **mapped** in declarative::

    class YourStringAdapter(adapters.Adapter):
        def validate(self, data):
            return True in data in self.parent.Payload.instance['otherfield']

        def clean(self, data):
            return data + self.parent.Payload.instance['otherfield']  # whatever


    class YourPayload(Payload):
        # this will be self.map.somefield.adapters !
        somefield = YourStringAdapter()
        listfield = ListAdapter(
            adapters=[FiveItems], # adapters for the list itself!
            map=[StringAdapter]   # adapters for list items!
        )
        # demonstrate nesting !
        dictfield = DictAdapter(
            map=dict(
                name=[StringAdapter],
                extra=DictAdapter(
                    map=dict(
                        hobbies=ListAdapter(
                            map=[HobbyAdapter]
                        ),
                    )
                )
            )
        )
        modelchoice = [ModelAdapter(model=SomeModel, fields=['onlythisfield'])]

        class Meta:
            # adapter still takes other adapters !
            adapters = (DjangoModel, DjangoForm, ReactForm)
