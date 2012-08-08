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

A `FacetField` is an ordered set of `FacetValue`s, plus a heading.

A `FacetValue` contains the information necessary to render a single facet
option, as part of a list or drop-down.

Setting up a simple facet
-------------------------
Let's say you have an Event model that you want to facet on the type of
event, and whether or not it is free:

    class Event(models.Model):
        title = models.CharField(max_length=100)
        is_free = models.BooleanField()
        type = models.ManyToManyField(EventType)

		class EventFacetGroup(FacetGroup):
				type = facetfields.FacetField()
				is_free = facetfields.BooleanFacetField()

				def queryset(self):
						return Event.objects.all()

		efg = EventFacetGroup()



Which generates all the FacetItems, starting with "All" items.

Each FacetItem has a `render` method which renders an html link.

    >>> facets = NumberFacet().get_facets()
    >>> facets.next().render()
    <a href="?acts=3">3 <span class="count">(42)</span></a>

Combining Facets
----------------
Calling get_facets() on its own stops being useful if you've chosen other facets elsewhere. Each facet needs to be aware of the other facets that have been chosen.

Each facet also needs to generate links that don't turn off the other facets.

Each facet also needs an "All" item that turns the facet off, it was previously chosen.

To accomplish all of these things, you need to start passing `request` around.

    >>> facets = NumberFacet().get_facets(request=r) # assume a request `r` that has a GET param attached that selects a 'free' facet elsewhere.
    >>> facets.next().render()
    <a href="?acts=3&free=y">3 <span class="count">(22)</span></a>

Applying Facets
---------------
All of the facets can be applied for a given request, like this:

qs = FacetFactory.apply_filter(pool=Event.objects.all(), request=get_request)

qs now contains the Event objects that match the facets specified in the request.

The FacetFactory class has a registry of all the Facets that exist, and applies any that match the GET query.

Facets on ForeignKeys
---------------------
    class Venue(models.Model):
        title = models.CharField(max_length=100)
        slug = models.SlugField(max_length=100)

    class Event(models.Model):
        title = models.CharField(max_length=100)
        venue = models.ForeignKeyField(Venue)

can be faceted on Venue like this:

class VenueFacet(FacetFactory):
    pool = Event.objects.all()
    GET_key = 'venue'
    model_field = 'venue__slug'
    model_field_for_label = 'venue__title'
    # optionally
    model_field_for_ordering = 'venue__title'


FacetFactory Variations
-----------------------
There are a few variations defined in facetfactories.py. They all override one or more methods of FacetFactory.

* SlugFacetFactory produces lowercase GET values, and does an iexact comparison for facet matching.

* BooleanFacetFactory produces "yes" and "no" labels and "y" and "n" GET values, instead of True and False.

* M2MFacetFactory takes an extra parameter, `m2m_field`, that indicates a ManyToManyField to use for the facets instead. model_field and model_field_for_label act on the related model, not the Facet's pool.

The future
----------
At the moment, there can only be one set of facets per site. In the future we will introduce a facet registry. Each registry will contain the pool and the relevant facets to apply.