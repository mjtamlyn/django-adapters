==========
Components
==========

This document describes all components or "steps" that django-adapters has.
They are closely related to existing concepts of ``django.forms`` and
``django.core.serializers`` and borrows ideas from Django Rest Framework (DRF).

Each section explains its scope and what exactly it should and shouldn't do and
know about. It also explains how the specific step currently works in Django or
DRF and gives hints how that step could be implemented in the future.

The components are supposed to be independent from each other and it should be
easy to customize one of it without having to touch or even breaking any other
component. Ideally you should also be able to replace a component entirely, e.g.
with an external library.

Additionally introspection of the components should be possible even within
components. This ensures that components can be independent from each other
while still being generic enough to make reuse of code easier.


Construction
============

The construction step determines the shape and all the pieces of the resulting
serializer. It always precedes the other steps and can't be skipped. Also once
this step is finished the list of fields that is available to the other steps is
frozen and *can't be changed* anymore. This means that if you need a differently
shaped serializer you will have to run this step again. Still, it should be easy
to modify the set of fields on a per-request basis.

Validation of any kind, loading and storing data is *not* part of this step, it
merely constructs an *immutable* data structure that contains and describes all
the used components. It basically collects all information about all other steps
for a particular serializer and combines that.

How it is currently done
------------------------

The list of fields in a form or a DRF serializer is generally specified
declaratively:

.. code-block:: python

    class BlogPostForm(Form):
        title = CharField(max_length=200)
        content = CharField()
        publish_date = DateTimeField()


In the background this currently retains the order of the fields however that
should not be necessary in the construction phase.

The best and recommended way to dynamically change the fields of a form is to
override ``Form.__init__()`` and manually set or modify ``self.fields``.

How it could be done
--------------------

Currently most of the logic of assembling form fields (apart from those coming
from ``Form.__init__()`` if you overrode that) is done in a meta class. This
meta class could be documented and exposed as public API to be able to easily
subclass it. The disadvantage with this approach is that you can't easily pass
any custom arguments to class creation (i.e., the meta class' ``__new__()`` and
``__init__()``). However those are often needed with ``request.user`` being one
of the examples.

Another solution is to use a factory function that can take a variable number of
arguments and returns a new class similar to how ``formset_factory()`` currently
works.

In essence there should be a API that creates the underlying data structure that
in turn can be used by different "helper"-APIs like a
``DeclarativeMetaClassSerializerConstructor`` or a
``FactoryFunctionSerializerConstructor``. The underlying data structure itself
should also have an API to easily create slightly modified (i.e., add this
field, remove that field, add this validator) clones of itself.

How adapters do construction
----------------------------

If going through the adapters.factory method for a django model, it will
automatically return a DjangoModelAdapter and fill up its .map with other
adapters per field::

    a = adapters.factory(Person.objects.get(pk=1))

Then you can modify the tree::

    a = a.map.set('password_confirm', PasswordConfirmFieldAdapter())

Or add another adapter that will add it for you::

    a = a.adapters.add(PasswordConfirmationFormAdapter())
    # when added, PasswordConfirmationFormAdapter will add a
    # PasswordConfirmFieldAdapter in .map.password_confirm.adapters

In this case, you probably want to add the DjangoForm adapter::

    a = a.add('django.Form')

Which will add form field adapters to the map. Of course you can also have
other forms::

    a = a.add('elementui.Form')

Existing Data
=============

All data that is provided by the system in one way or another and was not input
by the user is called "existing data". This includes but is not limited to field
defaults, initial data and model instances. This step describes the process of
collecting the existing data from all sources. The goal is to have an API that
makes it possible to easily add more sources of existing data and to customize
it on a per-request basis, e.g. "fetch the existing data from source A if user
is admin, otherwise fetch it from source B".

How it is currently done
------------------------

Form field defaults can be specified with the ``initial`` argument to
``Field()``:

.. code-block:: python

    title = CharField(
        max_length=200,
        initial='Enter your awesome title here!'
    )


It is also possible to pass a dictionary of initial data to ``Form.__init__()``:

.. code-block:: python

    my_initial_data = {'title': 'Enter your awesome title here!'}
    form = BlogPostForm(initial=my_initial_data)



Model instance data can also be loaded by passing it to a ``ModelForm`` with
the ``instance`` argument:

.. code-block:: python

    form = MyModelForm(instance=existing_instance)

How it could be done
--------------------

See "How it could be done" on the section "New Data".

The factory helps with existing data
------------------------------------

The adapters.factory will try to return the best registered adapter for a data.
For example::

    assert isinstance(adapters.factory(Person()), DjangoModelAdapter)

    class PersonAdapter(DeclarativeAdapter):
        name = StringAdapter(...)

        class Meta:
            adapters = [PersonWelcomeEmail]

    assert PersonAdapter.map.name == StringAdapter
    # PersonWelcomeEmail will be in PersonAdapter.adapters

New Data
========

All data that is provided by external sources (e.g. an HTML form submitted by a
user or POSTed JSON data) is called "new data". For the moment we'll call them
"Input Serializers". An Input Serializer must follow a documented API that
allows data of all kinds and shapes to be converted to a universal data
structure. That data structure then serves a data source for other components.

How it is currently done
------------------------

In Django Forms user data is passed to a form instance via the ``data`` and
``files`` argument:

.. code-block:: python

    form = BlogPostForm(data=request.POST, files=request.FILES)


The conversion to a "universal" data structure then happens in
``Widget.value_from_datadict()``. This method handles all potential oddities of
an HTML form, like multiple input fields with the same name or different input
fields belonging to one logical field.

DRF uses the ``data`` argument to a Serializer:

.. code-block:: python

    serializer = BlogPostSerializer(data=json_data)


How it could be done
--------------------

At first the universal data structure has to be defined. It should not be
opinionated about how the input data looked like and ideally should be usable
not only with new data but with existing data as well. It should be universal in
a way that is independent of how the serializer received the data, i.e. the type
of the data returned from a JSON serializer should be similar or identical to
the one returned from an HTML form serializer.

Then an API must be established that lets you modify the loading of existing or
new data easily.

Data in adapters
----------------

In terms of data, adapters have several attributes, including::

- instance
- initial
- data
- output

They can be modified during each step, that's why a step returns a clone.

Steps like instanciate or initialize, if executed, may for example fetch data
from an API or database.

Adapters are a silly tree of python objects and act as shared payload, all the
logic is executed by steps, you can add your own steps to if the default ones
are not enough for you.

Cleaning
========

The cleaning step comprises validating field values (e.g. field ``name`` must
have between 5 and 10 alphanumerical characters or field ``publish_date`` must
be in the future) and cross field validation (e.g. if field A is set field B
must be unset and vice versa, or field ``first_number`` and field
``second_number`` added up must be smaller than 100).

This component works only with the universal data structure mentioned before and
should not fetch additional data itself. It should however be possible for the
validation component to be influenced by the environment (a user's permission,
current time, etc.) and change its logic based on that.

Besides validation every validation step is also allowed to change the data in a
structural way to make coercing of values possible. Examples are casting a
string to an integer or normalizing a unicode string. Validation combined with
coercing values is called "cleaning".


How it is currently done
------------------------

Currently there are many ways to specify field validation in Django. The easiest
is to pass validator functions to the field via the ``validators`` argument:

.. code-block:: python

    title = CharField(validators=[
        validate_illegal_characters,
        validate_banned_words,
    ])


Where the validation functions just take a value and raise a ``ValidationError``
if applicable.

Custom fields can also override ``clean()``. This method can also change the
value that is validated.

.. code-block:: python

    class TitleField(CharField):
        def clean(self, value):
            value = super().clean(value)
            if not value.startswith('Title'):
                # all titles must start with "Title"
                value = 'Title ' + value
            if len(value.split()) > 5:
                raise ValidationError(
                    'title must not contain more than 5 words'
                )
            return value


It is also possible to define field validators on a form by adding
``clean_<field_name>()`` methods to it:

.. code-block:: python

    class BlogPostForm(Form):
        title = CharField()
        content = CharField()

        def clean_title(self):
            title = self.cleaned_data['title']
            if 'buzzword' in title.lower():
                raise ValidationError('invalid word')
            return title


Just like a field's ``clean()`` method this method can also change the value.

Cross field validation is made possible by overriding ``Form.clean()``:

.. code-block:: python

    class NumbersForm(Form):
        first_number = IntegerField()
        second_number = IntegerField()

        def clean(self):
            data = super().clean()
            if data['first_number'] + data['second_number'] > 100:
                raise ValidationError(
                    'sum of numbers must be smaller than 100'
                )
            return data


It is also possible to validate on the model level by calling ``full_clean()``
on the model instance. This calls all validator functions that were passed to
the model field just like for form fields. It is also possible to override
``clean()`` on the model. Furthermore ``Model.full_clean()`` is called from
a model form's ``full_clean()`` method.


How it could be done
--------------------

There are several libraries that explicitly deal with validation in Django.

How cleaning works in adapters
------------------------------

Adapters have a default clean step logic baked in, but you can override it with
your own::

    a.steps.validate = your_validate

But you can also enhance the default logic without replacing it::

    a.steps.validate.adapters = (list of adapters or callbacks)

When passed callbacks, it will make it an Adapter with only validation.

When passed adapters, it will use their validate method only.

Rendering
=========

Serializer renderers receive the underlying data structure and the current state
of the serializer data and present them to the outside world. This could be as
an HTML form, a JSON object or something completely different.

How it is currently done
------------------------

Django uses the ``Widget`` class to render HTML form input elements. There is
also the ``BoundField`` class that can be used in templates to customize how
they are displayed. Several options like ``help_text`` or ``verbose_name`` are
handed down from the form field to the widget or the bound field. A bound field
can be retrieved with ``Form.__getitem__()``:

.. code-block:: python

    >>> form = BlogPostForm()
    >>> print(form['title'])
    <input type="text" name="title" />


Rendering JSON can be done by using DRF's renderers:

.. code-block:: python

    >>> data = {'foo': 123, 'bar': 456}
    >>> renderer = JSONRender()
    >>> print(renderer.render(data))
    {"foo": 123, "bar": 456}


How it could be done
--------------------

There are several libraries that deal with rendering and serialization of data
in Django.

Rendering in adapters
---------------------

Rendering is an optional step which uses all render methods of adapters and
which can be decorated or redefined like every step.

That step will populate the adapter.render variable, in a clone of course as
with every step execution.

Adapters without the render() method won't be executed. At the end of the day
of course the step has the final word on what to execute and how, and by
default it'll try to use the render() method of each adapter, which might in
turn render its map, by executing the render() metod of each adapter it has in
its map. Which, in turn, should execute the render() method of every adapters
composing itself.

We could have more steps than just render() and have render_html(),
render_json() too.

Data Output
===========

Eventually after validating all the data that came in from different sources you
want to do actually do something with the data, like saving it to the database
in a single or multiple model instances, creating a file, sending an email,
running a command, etc.

This last step is called "Data Output". It takes the universal data structure
and then does whatever it wants with the data. It can't change any values or add
or remove fields but can only read them.

How it is currently done
------------------------

When using forms, the code for the data output is usually written directly into
the view by using ``form.cleaned_data``:

.. code-block:: python

    def send_mail(request):
        form = SendMailForm(data=request.POST)
        if form.is_valid():
            send_mail(
                subject=form.cleaned_data['subject'],
                message=form.cleaned_data['message'],
                from_email='django@example.com',
                recipient_list=[form.cleaned_data['recipient']]
            )
            return redirect('success_page')
        else:
            context = {'form': form}
            return render(request, 'send_mail.html', form)


If you are working with model forms you can use ``form.save()`` to save the data
to the database.


How it could be done
--------------------

There should be a way to specify actions that should be executed after all
previous steps were completed successfully. This makes it easier to encapsulate
the "Data Output" functionality and reduces duplication of code.

In adapters
-----------

.. code-block:: python

    class SendMailAdapter(AdapterInterface):
        def process(self):
            send_mail(
                subject=self.data['subject'],
                message=self.data['message'],
                from_email='django@example.com',
                recipient_list=[self.data['recipient']]
            )

        def response(self):
            if self.is_valid:
                self.response = redirect('success_page')
            self.response = render(self.request, 'send_mail.html', self.rendered)


    a = adapters.factory(SendMailForm)  # DjangoFormAdapter
    a = a.adapters.add(SendMailAdapter)
    a = a.steps.validate(request.POST)
    if not a.allerrors:
        a.process()
    return a.steps.response().response

    # Of course, you could have a formview step that would do this little logic
    # with this kind of IOC anything is possible, like, shooting yourself in
    # the foot
