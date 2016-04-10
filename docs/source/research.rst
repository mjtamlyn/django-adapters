========
Research
========
This presents an overview of existing packages that might serve as inspiration or possibly could be plugged in.


Validation
==========

(here goes the validation part, from PR#21)


Serialization
=============

Sorted by most interesting first:


`serpy <https://github.com/clarkduvall/serpy>`_
------------------------------------------------

serpy is a super simple object serialization framework built for speed. serpy
serializes complex datatypes (Django Models, custom classes, ...) to simple
native types (dicts, lists, strings, ...). The native types can easily be
converted to JSON or any other format needed.

`Docs <http://serpy.readthedocs.org/en/latest/>`_


Marshmallow
------------

Already mentioned above, things that were not included there:

`Ecosystem <https://github.com/marshmallow-code/marshmallow/wiki/Ecosystem>`_

`marshmallow-jsonapi <https://pypi.python.org/pypi/marshmallow-jsonapi/0.4.2>`_

`marshmallow-polyfield <https://github.com/Bachmann1234/marshmallow-polyfield>`_


`jsonmodels <https://github.com/beregond/jsonmodels>`_
-------------------------------------------------------

jsonmodels is library to make it easier for you to deal with structures that
are converted to, or read from JSON.

Similar to django models, but for JSON.


`django-json-schema <https://github.com/zbyte64/django-jsonschema>`_
---------------------------------------------------------------------

Old project, looks unmaintained (last/all commits made in Apr 2013). Converts
django forms to JSONSchemas.


`jsonmapping <https://github.com/pudo/jsonmapping>`_
-----------------------------------------------------

To transform flat data structures into nested object graphs matching JSON
schema definitions, this package defines a mapping language. It defines how the
columns of a source data set (e.g. a CSV file, database table) are to be
converted to the fields of a JSON schema.


`alchemyjsonschema <https://github.com/podhmo/alchemyjsonschema>`_
------------------------------------------------------------------
Converts SQLAlchemy models to JSONSchema. Good output format for inspiration.
Example:

.. code-block:: python

    import pprint as pp
    from alchemyjsonschema import SchemaFactory
    from alchemyjsonschema import AlsoChildrenWalker

    factory = SchemaFactory(AlsoChildrenWalker)
    pp.pprint(factory(User))

    """
    {'definitions': {'Group': {'properties': {'pk': {'description': 'primary key',
                                                     'type': 'integer'},
                                              'name': {'maxLength': 255,
                                                       'type': 'string'}},
                               'type': 'object'}},
     'properties': {'pk': {'description': 'primary key', 'type': 'integer'},
                    'name': {'maxLength': 255, 'type': 'string'},
                    'group': {'$ref': '#/definitions/Group'}},
     'required': ['pk'],
     'title': 'User',
     'type': 'object'}
    """

`see more examples <https://github.com/podhmo/alchemyjsonschema>`_


`jsonpickle <https://github.com/jsonpickle/jsonpickle>`_
--------------------------------------------------------

jsonpickle is a library for the two-way conversion of complex Python objects
and JSON. jsonpickle builds upon the existing JSON encoders, such as
simplejson, json, and demjson.


`python-rapidjson <https://github.com/kenrobbins/python-rapidjson>`_
--------------------------------------------------------------------

Python wrapper around RapidJSON. RapidJSON is an extremely fast C++ json
serialization library.

Python3 only.


`drf-fast-serializer <https://github.com/akaariai/drf-fast-serializer>`_
------------------------------------------------------------------------

Faster serializer mixin for DRF.


`metamagic.json <https://github.com/sprymix/metamagic.json>`_
--------------------------------------------------------------

An ultra-fast Python 3 implementation of a JSON encoder for Python objects
designed to be compatible with native JSON decoders in various web browsers.


`anyjson <https://bitbucket.org/runeh/anyjson/>`_
--------------------------------------------------

Anyjson loads whichever is the fastest JSON module installed and provides a
uniform API regardless of which JSON implementation is used.


Additional resources
====================

Links to repositories, articles, blogposts, and other things that might be
interesting.

https://github.com/WiserTogether/django-remote-forms

https://engineering.betterworks.com/2015/09/04/ditching-django-rest-framework-serializers-for-serpy/
