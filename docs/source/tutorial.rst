========
Tutorial
========

adapter = Adapter()
===================

An adapter has adapters, because everything is an adapter::

    a.adapters = [DjangoModelAdapter(Person.objects.get(pk=1))]

Adapters of an adapter share the same payload::

    a.adapters.DjangoModelAdapter.payload == a.payload
    # a.payload.{instance,initial,data,errors,output,etc... add your own!}

An adapter can also map adapters, in which case it will work with dicts in
payload.{data,initial}, mapping keys to .. adapters::

    a.map.name.adapters.add('adapters.string.String')

An adapter has steps, which may have side effects on the payload and the
structure, so steps must return a clone (thx Ian !)::

    a = a.steps.validate({})

Executing a step may add errors, in which case it is considered the step
failed::

    assert a.errors = {
        'map': {
            'name': ['Required !'],
        }
    }

An adapter can be replaced with poney magic, in which case it's your
responsibility to clone first if you see fit::

    a.map.name.adapters.String.required = False

An adapter can proudly represent their family::

    adapters.register(DjangoModelAdapter)

And serve their dear users::

    a = adapters.factory(instance=Person.objects.get(pk=1))

    assert isinstance(a, DjangoModelAdapter)

    assert a.payload.instance.pk == 1
    assert a.payload.initial == {'name': 'sly'}

    # DjangoModelAdapter populated its .map from introspection of the model
    assert isinstance(a.map.name, StringAdapter)

Custom adapters can do anything::

    # Example to add an adapter which will just remove fields from map
    a = a.add(UnauthenticatedUserPersonFields)

    class UnauthenticatedUserPersonFields(AdapterInterface):
        def post_add(self):
            # Adding an adapter calls its post_add() method, if exists
            del self.parent.map.admin_only_field_name

And be lists too::

    adapter = adapters.factory(person.pet_set)
    assert adapter.listmap  # this has listmap instead of map

And still have adapters on itself, and for items::

    assert isinstance(adapter, RelatedFieldAdapter)
    assert isinstance(adapter.listmap.adapters[0], DjangoModelAdapter)

Pattern
=======

An adapter adapts a node in a data tree. Adapters which are on the same node
shares their **errors**, **map** and **payload**. This defines a structure.

An adapter has **steps**, an orchestration object which allows breaking down
logic in several steps from adapters from different libraries, a critical piece
of the pattern, as it encapsulate the various IOC logics.

You can have your own steps or build them on the fly just like the adapter
structure.

Adapters are designed for reusability and register themselves, acheiving a
certain isomorphism, that will bring more DRYness than ever, and help us win
against tech debt (ie. code same logic in python and js).

Story of a Pythonesque IOC bootstrapping for avidusers
------------------------------------------------------

IN this story a Django user seems to have an adventure with an IOC pattern
which takes no pride in generating adapter types on the fly to build a multi
step IOC tree that should be able to translate between languages, like
javascript.

.. warning:: It's design to not get in your way, not to prevent your rm -rf /

.. code-block:: python

    from adapters import Adapter
    from adapters.strings import String, Email
    from adapters.exceptions import Error

    # Let's bootstrap from scratch
    a = adapters.Adapter()

    a = a.add(  # this creates and instanciates an Adapter !
        'PersonModel',
        instanciate=lambda self: (
            self.payload.instance = self.payload.instance or Person.objects.filter(
                pk=self.data['pk']).first()
        )
        initialize=lambda self: (
            self.payload.initial = self.payload.initial # something like that
            or copy(self.payload.instance.__dict__)
            if self.payload.instance else None
        ),
        process=lambda self: (
            self.payload.instance.__dict__.update(self.data) # warning: this is not real code !
            and self.payload.instance.save()
        ),
        # if we wanted to enforce, wed drop the 'or' and push last!
        ordering=adapters.APPEND

        # instanciate() creates a clone, throw away test !
    ).steps.instanciate().payload.instance == Person(pk=1)

    # Let's map adapters to for when data is a dict !

    # Factory for string returns a String Adapter !
    a = a.map.add('name', '')

    # Like a happy Poney on a completely different yet compatible syntax !
    a = a.map.add(Email(name='email', required=False))

    a = a.validate({'email': 'bar'})

    assert a.errors = {
        'map': {
            'email': ['not valid'],
            'name': ['required'],
        }
    }

    # mutation on the go for hacking poneys !
    a.map.email.required = True
    assert a.validate(data={'name': 'aoeu'}).errors = {
        'map': {
            'email': ['required'],
        }
    }

    a = a.map.email.adapters.add(
        'FunkyInitialEmail',
        # self.payload.initial maps to a.map.email.payloadd.initial['email'] !
        # because this adapter is constructed in a map with key 'email' !
        initial=lambda self: self.payload.initial = (
            self.payload.initial or 'sly@stonefamily.com')
    )

    a = a.steps.initialize() # clones !

    assert a.payload.initial = {'name': 'hello', 'email': 'foo@bar.com'}
    assert a.payload.instance == Person(pk=1)

    # warning ! setting adapter on adapter *map* ! self.data maps to the data
    # on the map owner's data !
    a = a.map.name.adapters.add(
        'LowerCase',
        # this will set adapter.data['name'], bound to self.data !
        # because this creates a *map* adapter on the fly for adapter !
        clean=lambda self: self.payload.data = self.payload.data.lower()
    )

    # clean clones 4 ur clean clone !
    assert a.steps.clean(data={'name': 'AOE'}).data['name'] == 'aoe'

    # Time to show off for some user love !
    assert a.adapters.add('elementui.Form').steps.render().payload.rendered == '<an awesome form>'

    # So yeah, this kind of presentational adapters will love visiting a's map
    # and add()'s adapters the see fit !
    assert a.adapters.add('googlemdc.Form').steps.render().payload.rendered == '<an awesome form>'

    # Let's just make an HTTP response !
    assert a.adapters.add('django.ProcessFormResponse').steps.process().payload.response

    # send welcome email to new users !
    assert a.adapters.add(
        'WelcomeEmail',
        # self.payload.instance maps to adapter.payload.instance because this
        # is not added in a map ! If you can have idempotent processes then you
        # are a smart poney maybe !
        process=lamba self: ensure_mail_sent(self.payload.instance)
    ).steps.process() # remember the first adapter we added, it will call instance.save() !

    # Now to some silly adapters we'll just derive from and instanciate like poneys !
    a = a.adapters.add(
        'PlatformServiceFilter',
        # This is a two way filter ! add() calls post_add() like a poney !
        post_add=lambda self: (
            self.adapters.add(
                'ServicePlatformFilter',
                # And invent magic steps like a little poney !
                # Some validations will only by doable after clean, and triggered only by value change !
                change=lambda self: (
                    self.payload.data['service'] in self.payload.data['platform'].service_set.all()
                    or raise Error('Service not compatible with platform you little rascal !')
                ),
                clone=False, # inplace like a magic poney !
            )
        ),
        # On value change callback because client + server = <3 <3 <3
        change=lambda self: (
            self.payload.data['platform'] in self.data.payload['service'].platform_set.all()
            or raise Error('Platform not compatible with service you little rascal !')
        ),
        process=lambda self: PlatformService.objects.update_or_create(
            service=self.payload.data['service'],
            platform=self.payload.data['platform']
        )
    )

    # But the above is too much boilerplate code ! No problem for Django has a DRY trick !
    del a.adapters.PlatformServiceFilter

    # Django comes to the rescue once again !
    a = a.adapters.add(
        'django.ModelChoiceFilter',
        Platform.service,
        **options, # i have no idea but that's going to be something for sure !
    )

    # Ok let's add a autocomplete widget !
    class AutocompleteFormAdapter(AdapterInterface):
        def get_url(self):
            try:
                rel_model = self.payload.instance._meta.get_field_by_name(self.name).rel.to
            except: # risk taking yay lets spice that up then
                return

            return get_model_autocomplete(rel_model)

        def adapts(self):
            return True if self.get_url()

        def post_add(self): # mutates, if adapts then will be added !
            for field in self.find_compatible_fields(self.payload.instance):
                # ok self.payload **and** self.map will be shared with other
                # adapters of the same node !
                self.map[field.name].adapters.add(AutocompleteForeignKeyAdapter())

    # For when the factory factorizes for a ForeignKey !
    adapters.register(ForeignKey)

Declarative
-----------

Any attribute which is an adapter will be **mapped** in declarative::

    class YourStringAdapter(adapters.Adapter):
        def validate(self, data):
            return True in data in self.parent.payload.instance['otherfield']

        def clean(self, data):
            return data + self.parent.payload.instance['otherfield']  # whatever


    class YourAdapter(adapters.Declarative):
        # this will be self.map.somefield ! We only take the validate method !
        somefield = YourStringAdapter(adapters=moreadapters, steps=['validate'])

        class Meta:
            # adapter still takes other adapters !
            adapters = (DjangoModel, DjangoForm)

Mixing steps
------------

Sometimes you are going to want to add cleaners in a validation chain. In this
case, instead of adding to adapters, you can add to the step::

    # setter magic will happen
    StringAdapter().steps.validate.adapters = (IntAdapter.is_numeric, IntAdapter.typecast, IntAdapter(greater_than=0).steps('validation'))
    # shortcut with a setter
    StringAdapter().validators = ...
    # but using that shortcut does not emphasize on the ability to add custom
    # steps !

In this case, Adapter will iterate over validators, and make an Adapter only
for validation with each. Poney magic garanteed for this to even have a chance
to work.
