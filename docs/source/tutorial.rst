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

An adapter may have any attributes, but some are more common than others:

- instance,
- instances,
- initial,
- data,
- rendered,
- input,
- output,

Adapters can define any steps they want, but some are more common:

- instanciate, for example fetch some data, setup Payload instance,
- initialize, set initial data, for example from the Payload's instance,
- validate, fills up the Payload errors, but don't actually change data,
- clean, changes data as adapters see fit and fill up the Payload errors,
- process, save data and other kind of business logic,
- render, render some output like html or json,

Adapters may have other adapters, or map them::

    assert StringAdapter().steps.clean(input=1).output == '1'

    # State can be augmented by passing args to a step, but also when instanciating
    assert StringAdapter(input=1).steps.clean().output == '1'
    # Note that step clones

    assert ListAdapter(datamap=[StringAdapter()], input=[1]).steps.clean().output == ['1']

    # Let's fail validation
    assert DictAdapter(datamap=dict(
        name=StringAdapter(cast=False)
    ), input={'name': 1}).steps.validate().errors == dict(name=['Is not a string'])

    # Instanciating an adapter sets its state and calls its mutate() step
    a = ModelAdapter(instance=Person())
    assert a.datamap == dict(name=[CharFieldAdapter()])

    # Also have a factory to instanciate an Adapter which may adapt to a given state
    assert adapters.factory(queryset=Person.objects.none()).listmap == [PersonAdapter]

That's pretty much it.

Poneying
========

.. code-block:: python

    class NameAdapter(StringAdapter):
         # steps always executed in clean clone !
         def validate(self):
               if allcaps(self.data):
                   self.errors.append('omg poney')

         def clean(self):
               self.data = self.data.capitalize()

    assert NameAdapter(data='AUO').validate().errors == ['omg poney']

    # declarative syntax, without metaclass
    class PersonAdapter(DictAdapter):
        map = dict(
           name=NameAdapter(),
           # instead of methods, AdapterInterface understands list of adapters
           fakename=StringAdapter(clean=[NameAdapter.validate]),
           # instead of methods, AdapterInterface understands list of callbacks
           age=IntAdapter(clean=[is_numeric, cast_int, greater_than(0)]),
           hobbies=adapters.factory(relation=PersonModel.hobbies),
           # the above makes an adapter that accepts relation=RelatedFieldManager
           extra=DictAdapter(map=dict(.......)) # recursiveness
        )
       adapters = [NoBadwordInString(), BootstrapFormAdapter(), RestAdapter()]

       def mutate(self):
           '''called when the adapter is instanciated, or added to an adapter, or before a step executes, to keep fresh'''
           super().mutate() # call other adapters mutate() recursively !
           for key, value in self.map.items(): # introspection
                quacks = getattr(value, 'quack', False)
                if quacks:                     # leads to mutation mutation: new field example
                     self.map.quack_extra = DuckAdapter(option='duckperson')
           super().mutate() # let's do it again in case an adapter has some feature for quack_extra ?

       def process(self):
           super().process() # execute all own and maped adapters process() yes recursive
           self.instance.__dict__ = self.data # if clean passed, we haz self.data !
           self.instance.save()  # or something like that
       process.require_step_success = ['clean']

       def validate(self):
           # call validate() on self.adapters and on mapped adapters, recursion !
           super().validate()
           if something(self.instance):
               # will this be moved in its own adapter? time'll tell
               self.errors.append('something happened')

       def clean(self):
            super().clean() # clean everything
            self.data['alsoadd'] = somesecrets()

       def render(self):
           return my_custom_render_step(self.request, self)
       render.require_variables = ['request']

       def instanciate(self):
            # i should have added ModelAdapter instead of doing this !
            if getattr(self, 'pk', None):
                self.instance = Person.objects.get(pk=self.pk)
           elif getattr(self, 'data', None):
                self.instance = Person(**self.data)
           else:
                self.instance = Person()

       def initialize(self):
            if getattr(self, 'instance', None):
                self.initial = self.instance.__dict__  # lol naive
            else:
                super().initialize()

       def response(self):
          # this would be automatic but is here for the example i'm poneying my way out
          # because where is DjangoRequestResponse adapter ?
          # well not as far as you might think
         if self.adapters.RestAdapter.adapts():  # can self.request.is_ajax or 'MAGIC' in self.request.pathinfo()
               self.adapters.RestAdapter.response() # sets self.response of course !
           if self.adapters.BootstrapFormAdapter.adapts():
               self.adapters.BootstrapFormAdapter.render()  # sets self.rendered of course !
               self.adapters.add('TemplateAdapter', clone=False)
               self.template = 'lol.html'
               # set self.rendered, after using self.rendered in the template of course !
               # but it could use self.instance if it wanted to !
               self.adapters.TemplateAdapter.render()
           else:
               # set some response !
               self.response = Response('wtf you poney !')
       response.require_variables = ['request']

       def adapts(self): # used by factory
           return isinstance(getattr(self, 'instance', None), PersonModel)


    # steps magical call method will actualy clone the adapter
    # and add the new arguments passed to the step to the adapter's state
    # and call mutate on all adapters
    # and call the adapter's method
    # to execute all call super().yourmethod()

    a = PersonAdapter().steps.validate(data={'name':'AOU'})
    assert a.errors = dict(map=dict(name='omg poney'))

    a = a.steps.clean(data={'name':'aoeu'})
    assert not a.instance
    a = a.steps.process()
    assert a.instance.pk
    a = a.steps.response()
    assert a.response

    PersonAdapter(instance=PersonModel()).steps.render(request=request).response
    # or adapters.register(PersoneAdapter); adapters.factory(instance=person).steps.render ... thx to PersonAdapter.adapts !

    class PersonQuerysetAdapter(ListAdapter):
        map = [PersonAdapter] # one PersonAdapter per list item !
        # more steps overrides, more adapters
        def adapts(self):
             # why did i not add QuerySetAdapter ? For the sake of the example and Poney !
             return self.queryset.model == Persone
        adapts.require_variables = 'queryeset'

    adapters.register(PersonListAdapter)
    adapters.factory(queryset=Person.objects.none()) # build adapter for
