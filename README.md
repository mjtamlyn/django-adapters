Django adapters
===============

The Python API for Django's forms framework was designed over 10 years ago.
It's a beautiful declarative API which proved so popular it has been copied by
many other Django (and Python) projects, such as Django Rest Framework and
Marshmallow. Unfortunately, it suffers from a few major weaknesses. Most
notably, the declarative API makes it hard and ugly to customize on a
per-request basis, and the resulting object is deeply nested and entangled.
This makes it hard to introspect, and hard to swap certain layers of the
process.

We intend to change the fundamental architecture of forms and serializers,
creating a new type of serializer with a flexible approach to its construction,
and baked in introspectability and composability as the main design goals. We
aim to continue to keep a simple programming interface for simple tasks, but
make it easier to take the pieces apart and put them back together in your own
way. This will make more advanced features easier to build. Examples include:
forms which interact with multiple models, inline forms, GraphQL style APIs,
shared logic between HTML forms and JSON APIs, client side mirrored validation,
and self-describing APIs.
