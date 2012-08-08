from django.test import TestCase
from django.db import models
from django.utils.datastructures import SortedDict
from facettools.base import ModelFacetGroup, FacetGroup, Facet

class Colour(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class ShopItem(models.Model):
    name = models.CharField(max_length=255)
    dollars = models.IntegerField(null=True)
    colours = models.ManyToManyField(Colour, null=True)

    def __unicode__(self):
        return "%s ($%s)" % (self.name, self.dollars)


class ShopItemFacetGroup(ModelFacetGroup):
    #TODO: allow facetgroup inheritance

    colours = Facet(verbose_name="the colours", select_multiple=True,
                    order_by=lambda f: f.count) #selecting multiple colours has
                    # an OR effect. Values are sorted by count

    @classmethod
    def get_colours_facet(cls, obj):
        return [x.name for x in obj.colours.all()]


    tags = Facet(verbose_name="the tags", select_multiple=True,
                 intersect_if_multiple=True) #selecting multiple tags has an AND effect

    def _sort_price(f):
        return {
            'free': 0,
            '$0-$50': 1,
            '$50-$100': 2,
            '$100 or more': 3
        }[f.name]

    price = Facet(verbose_name="the price", all_value="any price",
                  order_by=_sort_price)

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


    field_order = ('price', 'tags', 'colours') #specify a field ordering

    @classmethod
    def unfiltered_collection(cls):
        return ShopItem.objects.all()


class TestSimpleFacets(TestCase):

    def setUp(self):
        self.red = Colour.objects.create(name="red")
        self.orange = Colour.objects.create(name="orange")
        self.yellow = Colour.objects.create(name="yellow")
        self.green = Colour.objects.create(name="green")
        self.blue = Colour.objects.create(name="blue")
        self.indigo = Colour.objects.create(name="indigo")
        self.violet = Colour.objects.create(name="violet")

        self.null_item = ShopItem.objects.create(name="vacuum")
        self.free_violet_shirt = ShopItem.objects.create(name="violet shirt",
                                                 dollars=0)
        self.free_violet_shirt.colours.add(self.violet)

        self.red_shirt = ShopItem.objects.create(name="red shirt",
                                                 dollars=50)
        self.red_shirt.colours.add(self.red)

        self.green_shirt = ShopItem.objects.create(name="green shirt",
                                                         dollars=50)
        self.green_shirt.colours.add(self.green)

        self.blue_shirt = ShopItem.objects.create(name="blue shirt",
                                                         dollars=50)
        self.blue_shirt.colours.add(self.blue)

        self.red_and_yellow_shirt = ShopItem.objects.create(
            name="red and yellow shirt", dollars=100
        )
        self.red_and_yellow_shirt.colours.add(self.red, self.yellow)

        self.rainbow_shirt = ShopItem.objects.create(
            name="rainbow shirt", dollars=400
        )
        self.rainbow_shirt.colours.add(*list(Colour.objects.all()))

        ShopItemFacetGroup.rebuild_index()

    def test_facetgroup_metaclass(self):
        self.assertEqual(ShopItemFacetGroup.app_label, "facettools")
        self.assertIsInstance(ShopItemFacetGroup.facets, SortedDict)
        self.assertEqual(tuple(ShopItemFacetGroup.facets.keys()),
                         tuple(ShopItemFacetGroup.field_order))

        # facets can be accessed by name too
        self.assertEqual(ShopItemFacetGroup.facets['colours'], ShopItemFacetGroup.colours)

    def test_facet_display(self):
        f = ShopItemFacetGroup
        f.update() # default selection

        # basic FacetField attributes are name, verbose name and values
        self.assertEqual(f.price.name, "price")
        self.assertEqual(f.price.verbose_name, "the price")
        # basic FacetValue attributes are name, is_all, selected and count
        self.assertEqual(len(f.price.values), 5) #including 'all'
        self.assertEqual(f.price.values[0].name, 'any price')
        self.assertEqual(f.price.values[0].is_all, True)
        self.assertEqual(f.price.values[0].is_selected, True)
        self.assertEqual(f.price.values[0].count, ShopItem.objects.count())

        self.assertEqual(f.price.values[1].name, 'free')
        self.assertEqual(f.price.values[1].is_all, False)
        self.assertEqual(f.price.values[1].is_selected, False)
        self.assertEqual(f.price.values[1].count, 1)

        self.assertEqual(f.price.values[2].name, '$0-$50')
        self.assertEqual(f.price.values[2].is_all, False)
        self.assertEqual(f.price.values[2].is_selected, False)
        self.assertEqual(f.price.values[2].count, 4)
        #etc.

    def test_facet_selection(self):
        f = ShopItemFacetGroup
        self.assertEqual(set(f.unfiltered_collection()),
                         set(ShopItem.objects.all()))
        self.assertEqual(set(f.matching_items()), set(ShopItem.objects.all()))

        #TODO: test counts and selected update properly

        # select a single facet
        f.facets['price'].select('free')
        # need to call "update" to recalculate everything.
        self.assertEqual(set(f.matching_items()), set(ShopItem.objects.all()))
        f.update()
        self.assertEqual(set(f.matching_items()), set(ShopItem.objects.filter
            (dollars=0)))

        # change the value of a facet (price is single-select)
        f.facets['price'].select('$0-$50')
        f.update()
        self.assertEqual(set(f.matching_items()), set(ShopItem.objects.filter
            (dollars__lte=50)))

        # add another facet
        f.facets['colours'].select('red')
        f.update()

        self.assertEqual(set(f.matching_items()), set(ShopItem.objects.filter
            (dollars__lte=50, colours=self.red)))

        # add several values to that facet (colour is multi-select,
        # and conjoined with 'OR')
        f.facets['colours'].select('yellow')
        f.update()
        self.assertEqual(set(f.matching_items()), set(ShopItem.objects.filter
            (dollars__lte=50, colours__in=[self.red, self.yellow])))

        # by the way, we can retrieve the facets that are selected
        self.assertEqual(set([x.name for x in f.facets['colours'].selected()]),
            set(['red', 'yellow'])) #TODO: maintain ordering

        #unselect the price facet
        f.facets['price'].unselect('$0-$50')
        f.update()
        self.assertEqual(set(f.matching_items()), set(ShopItem.objects.filter
            (colours__in=[self.red, self.yellow])))

        #unselect all the colour facets
        f.facets['colours'].clear_selection()
        f.update()
        self.assertEqual(set(f.matching_items()), set(ShopItem.objects.all()))

        # you can pass several values to a multiselect facet
        f.facets['colours'].select('yellow', 'red')
        f.update()
        self.assertEqual(set(f.matching_items()), set(ShopItem.objects.filter
            (colours__in=[self.red, self.yellow])))

        # but you cannot pass several values to a single-select facet
        self.assertRaises(ValueError, f.price.select, 'free', '$0-$50')

        #select several tag facets
        f.facets['tags'].select('yellow', 'red')
        # tags are AND-conjoined (ie intersection)
        f.update()
        self.assertEqual(set(f.matching_items()),
            set(ShopItem.objects.filter(colours=self.red).filter(colours=self.yellow))
        )

        # unselect all facets
        f.clear_all()
        f.update()
        self.assertEqual(set(f.matching_items()), set(ShopItem.objects.all()))

        # you can pass a value that doesn't exist, but it will empty the
        # queryset (no result will show as selected, including 'all').
        self.assertRaises(KeyError, f.colours.select, 'maroon')


    def test_facet_GET_strings(self):
        #TODO: generate GET strings from a request
        pass

    def test_reindex(self):
        """
        Save a new ShopItem
        Update an existing ShopItem
        Delete a ShopItem

        after each, test that the facets are updated
        """
        pass


    def test_facetvaluestore(self):
        #TODO: test api of persistent store
        pass