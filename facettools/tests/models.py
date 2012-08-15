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
    is_archived = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s ($%s)" % (self.name, self.dollars)

    class Meta:
        app_label="facettools"

    def get_price_facet(self):
        if self.dollars is None:
            return None
        result = []
        if self.dollars == 0:
            result.append('free')
        if self.dollars <=50:
            result.append('$0-$50')
        if self.dollars >=50 and self.dollars <=100:
            result.append('$50-$100')
        if self.dollars >=100:
            result.append('$100 or more')

        return result

class ShopItemFacetGroup(ModelFacetGroup):
    app_label = "facettools"

    def unfiltered_collection(self):
        return ShopItem.objects.all()

    def declare_facets(self):
        def _sort_price(a, b):
            d = {
                'free': 0,
                '$0-$50': 1,
                '$50-$100': 2,
                '$100 or more': 3
            }
            return cmp(d[a.name], d[b.name])

        self.facets['price'] = Facet(
            group=self,
            name="price",
            verbose_name="the price",
            all_label="any price",
            cmp_func=_sort_price
        )
        self.facets['colours'] = Facet(
            group=self,
            name="colours",
            verbose_name="the colours",
            select_multiple=True,
        )
        #selecting multiple colours  has an OR effect.
        self.facets['tags'] = Facet(
            group=self,
            name="tags",
            verbose_name="the tags",
            select_multiple=True,
            intersect_if_multiple=True,
            cmp_func=sort_by_count
        ) #selecting multiple tags has an AND effect

        # Four similar facets that test the hide_all and default options
        self.facets['archived1'] = Facet(
            group=self,
            name="archived1",
            hide_all=False,
            default_selected_labels="no",
        )
        self.facets['archived2'] = Facet(
            group=self,
            name="archived2",
            hide_all=False,
            default_selected_labels=None,
        )
        self.facets['archived3'] = Facet(
            group=self,
            name="archived3",
            hide_all=True,
            default_selected_labels=["no"], # can also pass a list to select many (when applicable)
        )
        self.facets['archived4'] = Facet(
            group=self,
            name="archived4",
            hide_all=True,
            default_selected_labels=None,
        )


    def get_colours_facet(self, obj):
        return [x.name for x in obj.colours.all()]

    def get_tags_facet(self, obj):
         result = self.get_colours_facet(obj)
         if len(result) > 1:
             result.append("multicoloured")
         if obj.dollars == 0:
             result.append("free")
         if "shirt" in obj.name:
             result.append("shirt")
         return result

    def get_archived4_facet(self, obj):
        return "yes" if obj.is_archived else "no"

    get_archived1_facet = get_archived2_facet = get_archived3_facet = get_archived4_facet