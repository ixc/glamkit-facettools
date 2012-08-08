from django.db import models
from facettools.fields import PickledObjectField
from facettools.base import FacetValue

"""
A set of database-stored indexes, which allow database-level indexing and
retrieval of textual facets. There are no links to external models (and in
fact, we needn't only facet `models.Model`s).
"""

class FacetValueStore(models.Model):
    # the key of the FacetValue: app_label__facet_group_name__facet_name
    # e.g. "shop__shop_item_facet_group__colour__red"
    facet_key = models.CharField(max_length=1024, db_index=True)
    #value e.g. 'red'
    name = models.CharField(max_length=255)
    # denormalised size of _pickled_items
    _pickled_items = PickledObjectField() # access with `items`. Currently
    # limited to integer pks on a single model.
    # TODO: allow multiple models to share facets.

    class Meta:
        unique_together = ("facet_key", "name")

    def get_items(self):
        """
        A set of ids for the faceted objects, used for union/intersection.
        """
        return self._pickled_items

    def set_items(self, val):
        self._pickled_items = val

    items = property(get_items, set_items)


