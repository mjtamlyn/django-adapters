========
Tutorial
========

adapter = Adapter()
===================

An adapter has adapters, because everything is an adapter::

    a.adapters = [DjangoModelAdapter(Person.objects.get(pk=1)]

An adapter can have a data map like a dict, mapping keys to .. adapters::

    adapter.map.name.adapters.add('adapters.string.String')

An adapter has steps, executing methods on its own clone, and adapters::

    # adapter.steps.{initiate,validate,clean,process,render}
    adapter = adapter.steps.validate({})

An adapter is also the payload of their little story, with properties::

    # adapter.{instance,initial,data,errors,output}
    assert adapter.errors = {
        'map': {
            'name': ['Required !'],
        }
    }

An adapter can be replaced with poney magic::

    adapter.map.name.adapters.String.required = False

An adapter can proudly represent their family::

    adapters.register(DjangoModelAdapter)

Then serve their dear users::

    adapter = adapters.factory(Person.objects.get(pk=1))
    assert adapter.instance.pk == 1
    assert adapter.initial == {'name': 'sly'}

And be lists too::

    adapter = adapters.factory(person.pet_set)
    assert QuerySetAdapter in adapter.adapters  # for data
    assert ModelAdapter in adapters.map.adapters  # for data items

Story of a Pythonesque IOC bootstrapping for avid users
=======================================================

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
        instance=lambda self: (
            # warning ! self.initial maps to adapter.initial because this is an
            # adapter adapter not a map adapter !
            self.instance = self.instance or Person.objects.filter(
                pk=self.data['pk']).first()
        )
        initial=lambda self: (
            self.initial = self.initial # something like that
            or copy(self.instance.__dict__)
            if self.instance else None
        ),
        process=lambda self: (
            self.instance.__dict__.update(self.data) # warning: this is not real code !
            and self.instance.save()
        ),
        # if we wanted to enforce, wed drop the 'or' and push last!
        ordering=adapters.APPEND

        # instanciate() creates a clone, throw away test !
    ).steps.instanciate().instance == Person(pk=1)

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
    assert a.validate({'name': 'aoeu'}).errors = {
        'map': {
            'email': ['required'],
        }
    }

    a = a.map.email.adapters.add(
        'FunkyInitialEmail',
        # warning ! self.initial maps to adapter.initial['email'] !
        # because this adapter is constructed in a map with key 'email' !
        initial=lambda self: self.initial = self.initial or 'sly@stonefamily.com'
        # If this didn't have the or we could set the order
        # but the or makes it so that even APPEND would work so who care !
        # it's here for the example because it's fun !
        ordering=adapters.PREPEND
    )

    a = a.steps.initial() # clone !

    assert a.initial = {'name': 'hello', 'email': 'foo@bar.com'}
    assert a.instance == Person(pk=1)

    # warning ! setting adapter on adapter *map* ! self.data maps to the data
    # on the map owner's data !
    a = a.map.name.adapters.add(
        'LowerCase',
        # this will set adapter.data['name'], bound to self.data !
        # because this creates a *map* adapter on the fly for adapter !
        clean=lambda self: self.data = self.data.lower()
    )

    # clean clones 4 ur clean clone !
    assert a.steps.clean({'name': 'AOE'}).data['name'] == 'aoe'

    # Time to show off for some user love !
    assert a.adapters.add('elementui.Form').steps.render().output == '<an awesome form>'

    # So yeah, this kind of presentational adapters will love visiting a's map
    # and add()'s adapters the see fit !
    assert a.adapters.add('googlemdc.Form').steps.render().output == '<an awesome form>'

    # send welcome email to new users !
    assert a.adapters.add(
        'WelcomeEmail',
        # self.instance maps to adapter.instance because this is not added in a
        # map ! If you can have idempotent processes then you are a smart rascal !
        process=lamba self: ensure_mail_sent(self.instance)
    ).steps.process() # remember the first adapter we added, it will call instance.save() !

    # Now to some silly adapters we'll just derive from and instanciate like poneys !
    a = a.adapters.add(
        'PlatformServiceFilter',
        # This is a two way filter ! add() calls mutate() like a poney !
        mutate=lambda self: (
            self.adapters.add(
                'ServicePlatformFilter',
                # And invent magic steps like a little poney ! Probably should be called by a.steps.clean() !
                # Some validations will only by doable after clean, and triggered only by value change !
                change=lambda self: (
                    self.data['service'] in self.data['platform'].service_set.all()
                    or raise Error('Service not compatible with platform you little rascal !')
                ),
                clone=False, # inplace like a magic poney !
            )
        ),
        # On value change callback because client + server = <3 <3 <3
        change=lambda self: (
            self.data['platform'] in self.data['service'].platform_set.all()
            or raise Error('Platform not compatible with service you little rascal !')
        ),
        process=lambda self: PlatformService.objects.update_or_create(
            service=self.data['service'],
            platform=self.data['platform']
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
    class AutocompleteAdapter(Adapter):
        def get_url(self):
            try:
                rel_model = self.instance._meta.get_field_by_name(self.name).rel.to
            except: # risk taking yay lets spice that up then
                return

            return get_model_autocomplete(rel_model)

        def adapts(self):
            return True if self.get_url()

        def mutate(self): # mutates, if adapts !
            """
            i'm too tired for that last bit sorry """
            self.map.set(self.field.name, adapters.add(
            # Let's consider Attribut
            # i don't remember what's the incantation with _meta rel that doesn't spawn over lines of code
            rel_model = get_rel_model(self.instance, self.name)
            rel = gettr(self.instance._he, self.name)

            if re.match(self.data, 'https://soundcloud.com.*'):
    # For when the factory factorizes for a ForeignKey !
    adapters.register(ForeignKey)

Declarative
-----------

Any attribute which is an adapter will be **mapped** in declarative::

    class YourStringAdapter(adapters.Adapter):
        def validate(self, data):
            return True in data in self.parent.instance['otherfield']

        def clean(self, data):
            return data + self.parent.instance['otherfield']  # whatever


    class YourAdapter(adapters.Declarative):
        # this will be self.map.somefield ! We only take the validate method !
        somefield = YourStringAdapter(adapters=moreadapters, steps=['validate'])

        class Meta:
            # adapter still takes other adapters !
            adapters = (DjangoModel, DjangoForm)
