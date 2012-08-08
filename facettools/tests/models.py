from django.db import models
from facettools.base import Facet
from facettools.model_base import ModelFacetGroup
from facettools.utils import sort_by_count

class Colour(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label="facettools"


class ShopItem(models.Model):
    name = models.CharField(max_length=255)
    dollars = models.IntegerField(null=True)
    colours = models.ManyToManyField(Colour, null=True)

    def __unicode__(self):
        return "%s ($%s)" % (self.name, self.dollars)

    class Meta:
        app_label="facettools"

class ShopItemFacetGroup(ModelFacetGroup):

    def _sort_price(a, b):
        d = {
            'free': 0,
            '$0-$50': 1,
            '$50-$100': 2,
            '$100 or more': 3
        }
        return cmp(d[a.name], d[b.name])

    price = Facet(
        verbose_name="the price",
        all_label="any price",
        cmp_func=_sort_price
    )
    colours = Facet(
        verbose_name="the colours",
        select_multiple=True,
    )
    #selecting multiple colours  has an OR effect.
    tags = Facet(
        verbose_name="the tags",
        select_multiple=True,
        intersect_if_multiple=True,
        cmp_func=sort_by_count
    ) #selecting multiple tags has an AND effect

    class Meta:
        app_label="facettools"
        facets_order = ('price', 'tags', 'colours') #specify a field ordering

    @classmethod
    def get_colours_facet(cls, obj):
        return [x.name for x in obj.colours.all()]

    @classmethod
    def get_price_facet(cls, obj):
        if obj.dollars is None:
            return None
        result = []
        if obj.dollars == 0:
            result.append('free')
        if obj.dollars <=50:
            result.append('$0-$50')
        if obj.dollars >=50 and obj.dollars <=100:
            result.append('$50-$100')
        if obj.dollars >=100:
            result.append('$100 or more')

        return result

    @classmethod
    def get_tags_facet(cls, obj):
         result = cls.get_colours_facet(obj)
         if len(result) > 1:
             result.append("multicoloured")
         if obj.dollars == 0:
             result.append("free")
         if "shirt" in obj.name:
             result.append("shirt")
         return result

    @classmethod
    def unfiltered_collection(cls):
        return ShopItem.objects.all()