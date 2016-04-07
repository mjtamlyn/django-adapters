========
Research
========
This presents an overview of existing packages that might serve as inspiration or possibly could be plugged in.

Validation
==========
An (incomplete) overview of existing validation packages (in alphabetical order).

`Cerberus <http://docs.python-cerberus.org/>`_
----------------------------------------------
*Cerberus is a lightweight and extensible data validation library for Python.*

.. code-block:: python

    >>> schema = {'name': {'type': 'string'}}
    >>> v = Validator(schema)

    >>> document = {'name': 'john doe'}
    >>> v.validate(document)
    True


`Chainable Validators <https://github.com/Outernet-Project/chainable-validators>`_
----------------------------------------------------------------------------------

.. code-block:: python

    >>> import re
    >>> from validator import *
    >>> spec = {
    ...     'foo': [required, istype(int)],
    ...     'bar': [optional, match(re.compile(r'te.*')],
    ...     'baz': [optional, boolean]
    ... }


`Colander <http://docs.pylonsproject.org/projects/colander/>`_
--------------------------------------------------------------
*A serialization/deserialization/validation library for strings, mappings and lists.*

.. code-block:: python

    import colander

    class Friend(colander.TupleSchema):
        rank = colander.SchemaNode(colander.Int(),
                                  validator=colander.Range(0, 9999))
        name = colander.SchemaNode(colander.String())

    class Phone(colander.MappingSchema):
        location = colander.SchemaNode(colander.String(),
                                      validator=colander.OneOf(['home', 'work']))
        number = colander.SchemaNode(colander.String())

    class Friends(colander.SequenceSchema):
        friend = Friend()

    class Phones(colander.SequenceSchema):
        phone = Phone()

    class Person(colander.MappingSchema):
        name = colander.SchemaNode(colander.String())
        age = colander.SchemaNode(colander.Int(),
                                 validator=colander.Range(0, 200))
        friends = Friends()
        phones = Phones()


`formencode.validator <http://www.formencode.org/en/latest/Validator.html>`_
----------------------------------------------------------------------------
*A validation library for Python.*

.. code-block:: python

    >>> class Registration(formencode.Schema):
    ...     first_name = validators.ByteString(not_empty=True)
    ...     last_name = validators.ByteString(not_empty=True)
    ...     email = validators.Email(resolve_domain=True)
    ...     username = formencode.All(validators.PlainText(),
    ...                               UniqueUsername())
    ...     password = SecurePassword()
    ...     password_confirm = validators.ByteString()
    ...     chained_validators = [validators.FieldsMatch(
    ...         'password', 'password_confirm')]


`Gladiator <https://github.com/laco/gladiator>`_
------------------------------------------------
*Gladiator is a Data Validation Framework for Python3 *

.. code-block:: python

    import gladiator as gl

    registration_form_validator = (
        ('email', gl.required, gl.format_email),
        ('pw', gl.required, gl.length_min(5)),
        ('name', gl.required, gl.type_(str)),
        ('birth_year', gl.required, gl.type_(int), gl.value_max(2014 - 18))
    )

    valid_test_data = {
        'email': 'test@example.com',
        'pw': 'password123',
        'name': 'Test Username',
        'birth_year': 1984
    }

    result = gl.validate(registration_form_validator, valid_test_data)
    assert result.success is True


`good <https://github.com/kolypto/py-good>`_
--------------------------------------------
*Slim yet handsome validation library.*

.. code-block:: python

    from good import Schema, Entire

    def maxkeys(n):
        # Return a validator function
        def validator(d):
            # `d` is the dictionary.
            # Validate it
            assert len(d) <= 3, 'Dict size should be <= 3'
            # Return the value since all callable schemas should do that
            return d
        return validator

    schema = Schema({
        str: int,
        Entire: maxkeys(3)
    })


`incoming <https://incoming.readthedocs.org/>`_
-----------------------------------------------
*JSON validation framework for Python.*

.. code-block:: python

    >>> class AddressValidator(PayloadValidator):
    ...     street = datatypes.String()
    ...     country = datatypes.String()
    ...
    >>> class PersonValidator(PayloadValidator):
    ...     name = datatypes.String()
    ...     age = datatypes.Integer()
    ...     address = datatypes.JSON(AddressValidator)
    ...
    >>> PersonValidator().validate(dict(name='Some name', age=19, address=dict(street='Brannan, SF', country='USA')))
    (True, None)
    >>>
    >>> PersonValidator().validate(dict(name='Some name', age=19, address=dict(street='Brannan, SF', country=0)))
    (False, {'address': ['Invalid data. Expected JSON.', {'country': ['Invalid data. Expected a string.']}]})


`Kanone <https://github.com/doncatnip/kanone>`_
-----------------------------------------------
*A general purpose validation library*

.. code-block:: python

    >>> from kanone import *
    >>> HelloSchema = Schema\
        ( 'nick'
            , String() & Len(max=20)
        , 'email'
            , web.Email()
        , 'email_confirm'
            , Match( Field('.email'), ignoreCase=True )
        )
    >>> context = HelloSchema.context\
        (   { 'nick':'bob'
            , 'email':'Bob@Some.Domain.Org'
            , 'email_confirm': 'BOB@Some.domain.org'
            }
        )
    >>> context('nick').result
    u'bob'
    >>> context('email').result
    u'Bob@some.domain.org'


`lasso <https://lasso.readthedocs.org/en/latest/>`_
---------------------------------------------------
*Lightweight module to define serializable, schema-validated classes*

.. code-block:: python

    >>> class Name(lasso.Schemed):
    ...     __schema__ = { "first": str, "family": str }
    ...
    >>> class User(lasso.Schemed):
    ...     __schema__ = { "name": Name, "email": str }
    ...
    >>> jdoe = User(name=Name(first="John", family="Doe"),
    ...             email="j@doe.org")
    ...


`marshmallow: simplified object serialization <https://marshmallow.readthedocs.org/>`_
--------------------------------------------------------------------------------------
*marshmallow is an ORM/ODM/framework-agnostic library for converting complex datatypes, such as objects, to and from
 native Python datatypes.*

.. code-block:: python

    from marshmallow import Schema, fields

    class ArtistSchema(Schema):
        name = fields.Str()

    class AlbumSchema(Schema):
        title = fields.Str()
        artist = fields.Nested(ArtistSchema)

    schema = AlbumSchema()
    result = schema.dump(album)
    print(result.data)


* `django-rest-marshmallow <http://tomchristie.github.io/django-rest-marshmallow>`_: Marshmallow schemas for Django REST framework
* `marshmallow-form <https://github.com/podhmo/marshmallow-form>`_: a wrapper of marshmallow for form library like behavior
* `marshmallow-validators <https://marshmallow-validators.readthedocs.org/>`_: Use 3rd-party validators (e.g. from WTForms and colander) with marshmallow
* `webargs <https://webargs.readthedocs.org/>`_: A friendly library for parsing HTTP request arguments


`Naval <https://github.com/leforestier/naval>`_
-----------------------------------------------
*Python validation library with error messages in multiple languages and a readable syntax.*

.. code-block:: python

    >>> from naval import *
    >>> from passlib.hash import bcrypt # we're going to use the passlib library to encrypt passwords

    >>> registration_form = Schema(
            ['username', Type(str), Length(min=3, max=16)],
            ['password', Type(str)],
            ['password2'],
            [
                Assert(
                    (lambda d: d['password'] == d['password2']),
                    error_message = "Passwords don't match"
                )
            ],
            ['password', lambda s: s.encode('utf-8'), bcrypt.encrypt, Save],
            ['password2', Delete],
            ['email', Email]
        )

    >>> registration_form.validate({
            'email': 'the-king@example.com',
            'username': 'TheKing',
            'password': 'hackme',
            'password2': 'hackme'
        })
    {'email': 'the-king@example.com',
     'password': '$2a$12$JT2UlXP0REt3EX7kGIFGV.5uKPQJL4phDRpfcplW91sJAyB8RuKwm',
     'username': 'TheKing'}


`notario <http://notario.cafepais.com/>`_
-----------------------------------------
*Validation of Python dictionaries*

.. code-block:: python

    >>> data = {'main': {'foo': 'bar'}}
    >>> schema = ('main', MultiRecursive(('foo', 1), ('foo', 'bar')))
    >>> validate(data, schema)


`schema <https://github.com/keleshev/schema>`_
----------------------------------------------
*Schema validation just got Pythonic*

.. code-block:: python

    >>> from schema import Schema, And, Use, Optional

    >>> schema = Schema([{'name': And(str, len),
    ...                   'age':  And(Use(int), lambda n: 18 <= n <= 99),
    ...                   Optional('sex'): And(str, Use(str.lower),
    ...                                        lambda s: s in ('male', 'female'))}])

    >>> data = [{'name': 'Sue', 'age': '28', 'sex': 'FEMALE'},
    ...         {'name': 'Sam', 'age': '42'},
    ...         {'name': 'Sacha', 'age': '20', 'sex': 'Male'}]

    >>> validated = schema.validate(data)

    >>> assert validated == [{'name': 'Sue', 'age': 28, 'sex': 'female'},
    ...                      {'name': 'Sam', 'age': 42},
    ...                      {'name': 'Sacha', 'age' : 20, 'sex': 'male'}]


`Schematics <https://schematics.readthedocs.org/>`_
---------------------------------------------------
*Python Data Structures for Humans™.*

.. code-block:: python

    >>> from schematics.models import Model
    >>> from schematics.types import StringType
    >>> class Person(Model):
    ...     name = StringType()
    ...     bio = StringType(required=True)
    ...
    >>> p = Person()
    >>> p.name = 'Paul Eipper'
    >>> p.validate()
    Traceback (most recent call last):
    ...
    ModelValidationError: {'bio': [u'This field is required.']}


`sigma.core <https://github.com/pysigma/core>`_
-----------------------------------------------
*sigma.core is a validation framework.*

.. code-block:: python

    from sigma.core import Model, ErrorContainer, asdict, validate
    from sigma.standard import Field


    class User(Model):
        id = Field(type=int, size=(5, 10))
        password = Field(type=str, length=(8, 15))

    user = User()
    user.id = 5
    user.password = "12345678"
    asdict(user)  # {"id": 5, "password": "12345678"}


`val <https://github.com/thisfred/val>`_
----------------------------------------
*A validator for arbitrary Python objects.*

.. code-block:: python

    >>> from val import Schema
    >>> sub_schema = Schema({'foo': str, str: int})
    >>> schema = Schema(
    ...     {'key1': sub_schema,
    ...      'key2': sub_schema,
    ...      str: sub_schema})

    >>> schema.validates({
    ...     'key1': {'foo': 'bar'},
    ...     'key2': {'foo': 'qux', 'baz': 43},
    ...     'whatever': {'foo': 'doo', 'fsck': 22, 'tsk': 2992}})
    True


`valhalla <https://github.com/petermelias/valhalla>`_
-----------------------------------------------------
*Minimalist validation library with focus on API brevity and simplicity. 40+ filters primitive and composed.*

.. code-block:: python

    my_definition = {
        'email': ['require', ('alt', 'email_address'), 'email'], # email address with alternate name
        'age': ['require', 'numeric', ('range', 13, 100)] # age must be numeric between 13 and 100
        'password': [('text', 10, 50)],
        'password_confirm': [('match', 'password')]
    }

    s = Schema.from_dict(my_definition)
    s.validate(some_data) # Bam!



`valideer <https://github.com/podio/valideer>`_
-----------------------------------------------
*Lightweight data validation and adaptation Python library.*

.. code-block:: python

    >>> import valideer as V
    >>> product_schema = {
    >>>     "+id": "number",
    >>>     "+name": "string",
    >>>     "+price": V.Range("number", min_value=0),
    >>>     "tags": ["string"],
    >>>     "stock": {
    >>>         "warehouse": "number",
    >>>         "retail": "number",
    >>>     }
    >>> }
    >>> validator = V.parse(product_schema)


`Validation <https://validation-py.readthedocs.org/>`_
------------------------------------------------------
*Validation is a small python library to validate python data structures.*

.. code-block:: python

    import validation

    # Build the validation model

    user_validator = validation.Dict()
    user_validator.required['_id'] = validation.StringUUID()
    user_validator.required['name'] = validation.String()
    user_validator.required['gender'] = validation.Choice(choices=['male', 'female'])
    hobbies = validation.List()
    hobbies.validator = validation.String()
    user_validator.optional['hobbies'] = validation.List()

    # two valid user objects

    john = {
        '_id': 'e7a5ff1c-ee5e-4ca9-a3d3-0106dd826dcd',
        'name': 'John',
        'gender': 'male',
        'hobbies:': [
            'python',
            'blarg',
            'blub'
        ]
    }

    paula = {
        '_id': 'e7a5ff1c-ee5e-4ca9-a3d3-0106dd826dcd',
        'name': 'Paula',
        'gender': 'female',
    }

    # an not valid one

    weirdo = {
        '_id': 'e7a5ff1c-ee5e-4ca9-a3d3-0106dd826dcd',
        'name': 'Weirdo',
        'gender': 'all of them',
        'hobbies:': [
            'mitosis'
        ]
    }

    for user in [john, paula, weirdo]:
        try:
            # None is returned of the user is valid user_validator.validate(john)
        except validation.ValidationError as err:
            # a exception is raised, if the object is invalid # the exception message contains the first failed element print(err)



`Validator <https://validatorpy.readthedocs.org/>`_
---------------------------------------------------
*A library for validating that dictionary values meet certain sets of parameters. Much like form validators, but for dicts.*

.. code-block:: python

    from validator import Required, Not, Truthy, Blank, Range, Equals, In, validate

    # let's say that my dictionary needs to meet the following rules...
    rules = {
        "foo": [Required, Equals(123)],
        "bar": [Required, Truthy()],
        "baz": [In(["spam", "eggs", "bacon"])],
        "qux": [Not(Range(1, 100))] # by default, Range is inclusive
    }

    # then this following dict would pass:
    passes = {
        "foo": 123,
        "bar": True, # or a non-empty string, or a non-zero int, etc...
        "baz": "spam",
        "qux": 101
    }
    print validate(rules, passes)
    # (True, {})

    # but this one would fail
    fails = {
        "foo": 321,
        "bar": False, # or 0, or [], or an empty string, etc...
        "baz": "barf",
        "qux": 99
    }
    print validate(rules, fails)
    # (False,
    #  {
    #  'foo': ["must be equal to '123'"],
    #  'bar': ['must be True-equivalent value'],
    #  'baz': ["must be one of ['spam', 'eggs', 'bacon']"],
    #  'qux': ['must not fall between 1 and 100']
    #  })


`Validators <https://validators.readthedocs.org/>`_
---------------------------------------------------
*Python Data Validation for Humans™.*

.. code-block:: python

    >>> import validators

    >>> validators.email('someone@example.com')
    True


`voluptuous <https://github.com/alecthomas/voluptuous>`_
--------------------------------------------------------
*Voluptuous, despite the name, is a Python data validation library. It is primarily intended for validating data coming into Python as JSON, YAML, etc.*

.. code-block:: python

    >>> from voluptuous import Required, All, Length, Range
    >>> schema = Schema({
    ...   Required('q'): All(str, Length(min=1)),
    ...   Required('per_page', default=5): All(int, Range(min=1, max=20)),
    ...   'page': All(int, Range(min=0)),
    ... })


`WTForms <https://wtforms.readthedocs.org/>`_
---------------------------------------------
*A flexible forms validation and rendering library for Python.*

.. code-block:: python

    from wtforms import Form, BooleanField, StringField, validators

    class RegistrationForm(Form):
        username     = StringField('Username', [validators.Length(min=4, max=25)])
        email        = StringField('Email Address', [validators.Length(min=6, max=35)])
        accept_rules = BooleanField('I accept the site rules', [validators.InputRequired()])

    def register(request):
        form = RegistrationForm(request.POST)
        if request.method == 'POST' and form.validate():
            user = User()
            user.username = form.username.data
            user.email = form.email.data
            user.save()
            redirect('register')
        return render_response('register.html', form=form)


