================
GLAMkit-facettools
================

A tool for dealing with facets in collections. It is part of the `GLAMkit project <http://glamkit.org/>`_. For more information, see the `documentation <http://docs.glamkit.org/stopspam/>`_.

View a full list of `GLAMkit components <http://docs.glamkit.org/components/>`_.

Approach
==========

Facets present ways of narrowing down an item selection, by showing what the
options are, and how many results will be produced.

This module does most of the legwork in setting up facets for collections.

The emphasis is on performance, at the occasional expense of memory.

Refer to tests.py for more examples of behaviour.

Overview
--------
A `FacetGroup` is an ordered set of `FacetField`s on a particular collection.

A `FacetField` is an ordered set of `FacetLabel`s, plus a heading.

A `FacetLabel` contains the information necessary to render a single facet
option, as part of a list or drop-down.
