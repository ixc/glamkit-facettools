from django.shortcuts import render_to_response
from django.template.context import RequestContext

"""
This code is supplied as an example. It won't work without ShopItemFacetGroup.
It's simple enough to adapt to your own view, right?
"""

"""
def faceted_list(request):

    facet_group = ShopItemFacetGroup()
    facet_group.rebuild_index()
    facet_group.apply_request(request)

    items = facet_group.queryset().order_by('name')

    # paginate items, etc.

    context = RequestContext(request)
    context['facets'] = facet_group.facet_list
    context['items'] = items

    return render_to_response('facettools/faceted_list.html', context)
"""