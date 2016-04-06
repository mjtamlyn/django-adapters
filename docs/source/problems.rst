========
Problems
========

This document explains the core issues we see with the current state of Django
and the ecosystem, which are the motivation for the project and influence the
design of the resulting architecture.

The modern web speaks multiple encodings and protocols
======================================================

When Django’s forms were designed in the mid 2000s, almost all communication
with a website was encoded in HTML. Data was output by rendering to an HTML
document using a templating system, and this was delivered to the client. Data
was accepted using HTML ``<form>`` tag, and a Django ``Form``.

In the modern web, HTML is still a major player but it shares the limelight
with JSON, with communication generally taking place over some RESTful API. In
the next 10 years of the web, who can say which other commincation encoding or
communication architecture will become the new standard.

Fundamentally, a data driven website such as the ones typically built using
Django handles two major external processes. It delivers a representation of
some data, and it receives requests to modify that data. In the current
ecosystem, there are two distinct libraries most commonly used to achieve these
core goals, and developers may mix and match between them within their
projects. The first is core Django, which excels at rendering rich data into a
document, and at accepting HTML form encoded data, validating it and storing
it. The second is Django Rest Framework, which is optimised for building a
developer friendly API, generally encoded in JSON. These two codebases both do
a good job of their work, but the choice between them for a developer is made
based on how you want to construct the architecture of your website. If you
have built an HTML oriented website and then wish to add an API, you have to
redefine many core parts of your logic in a similar bit subtly different
system.

Django needs to recognise that the web platform has moved on. It speaks
multiple encodings and protocols, and we must make it easy for developers to
build their websites independently of their current choice of encoding. In
particular, the design of core features (such as validation of incoming data)
should not be oriented strongly around one particular encoding. Django should
also have a built in system for translating from the database to an encodable
representation of that data.

Your database structure does match the resources you expose
===========================================================

The design of Django forms (and model forms) came out of a desire to easily
provide an interface to an underlying relational database. A relational
database stores a set of fields together as a single record, and the table can
be desribed as the collection of those fields, with a few extra conditions.
Naturally, the design of forms copied this, and a form is a collection of
fields.

Over time, almost all Django sites will start to diverge in some way from
simply exposing the structure of the database underneath. They may wish to
operate on related parent or child tables as if they are a single resource,
they may represent only certain parts of the tables, and they may expose the
same data in different ways depending on the user or application requesting it.

Both Django forms and DRF serializers allow you to change them by inheritance,
using a metaclass to organise the set of fields, and python inheritance for any
cross-field needs. Django forms provide no easy way to nest resources, or easy
ways to reuse the same logical fields with different rendering rules. DRF
serializers provide more limited ways to include cross field logic. Both
provide a model oriented version which reduces the amount of work and
individual developer needs to do to interact with a single model, but the
adaptability of these are limited when interacting with multiple models, often
resulting in users needing to duplicate code, or reimplement the model binding.
The inheritance pattern also makes it easy to add pieces, but harder to cut
them up, making interfaces where you can read or write only certain parts of the
data harder to build.

Introspectability
=================

If you wish to have a shared engine for data input and output but interact with
it in different ways, then you need to ensure that the structure of that engine
is easily introspectable. Whilst Django forms and DRF serializers do document
some of their internal structure, it is not structured in a way which is easily
serializable to be sent to a client application, or inspected by different
rending platforms. By considering introspection as a top priority, we can make
it easier for an ecosystem of libraries to consume this to build self
describing APIs, browser rendered forms, and mirrored validation. It is
important that not only the core field names and types themselves is
instrospectable, but also the relationships between them for validation and
display logic.

The good parts
==============

The declative API
The programming interface (e.g. is_valid)
