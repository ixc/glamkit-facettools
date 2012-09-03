from django.test import TestCase
from django.utils.datastructures import SortedDict

from .models import *
from .utils import check_counts


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

        self.old_fashioned_shirt = ShopItem.objects.create(
            name="archived shirt", dollars = 2,
            is_archived=True,
        )
        self.old_fashioned_shirt.colours.add(self.yellow)

        self.f = ShopItemFacetGroup()
        self.f.rebuild_index()

    def tearDown(self):
        ShopItem.objects.all().delete()
        Colour.objects.all().delete()

    def test_facetgroup_init(self):
        self.assertEqual(self.f.app_label, "facettools")
        self.assertIsInstance(self.f.facets, SortedDict)

        # facets can be accessed by name too
        self.assertEqual(self.f.facets['colours'],
                         self.f.colours)

    def test_facet_display(self):
        self.f.clear_selection()
        self.f.update() # default selection

        # basic FacetField attributes are name, verbose name and labels
        self.assertEqual(self.f.price.name, "the price")
        self.assertEqual(self.f.price.slug, "price")
        # basic FacetLabel attributes are name, is_all, selected and count
        self.assertEqual(len(self.f.price.labels), 5) #including 'all'
        self.assertEqual(self.f.price.labels[0].name, 'any price')
        self.assertEqual(self.f.price.labels[0].is_all, True)
        self.assertEqual(self.f.price.labels[0].is_selected, True)
        self.assertEqual(self.f.price.labels[0].count, ShopItem.objects.filter(is_archived=False).count())

        self.assertEqual(self.f.price.labels[1].name, 'free')
        self.assertEqual(self.f.price.labels[1].is_all, False)
        self.assertEqual(self.f.price.labels[1].is_selected, False)
        self.assertEqual(self.f.price.labels[1].count, 1)

        self.assertEqual(self.f.price.labels[2].name, '$0-$50')
        self.assertEqual(self.f.price.labels[2].is_all, False)
        self.assertEqual(self.f.price.labels[2].is_selected, False)
        self.assertEqual(self.f.price.labels[2].count, 4)

        self.assertEqual(self.f.price.labels[3].name, '$50-$100')
        self.assertEqual(self.f.price.labels[3].is_all, False)
        self.assertEqual(self.f.price.labels[3].is_selected, False)
        self.assertEqual(self.f.price.labels[3].count, 4)
        #etc
    def test_hide_all(self):

        self.f.clear_selection()
        self.f.update() # default selection
        self.assertEqual(len(self.f.archived1.labels), 3)
        self.assertEqual(len(self.f.archived2.labels), 3)
        self.assertEqual(len(self.f.archived3.labels), 2)
        self.assertEqual(len(self.f.archived4.labels), 2)

        self.assertEqual(self.f.archived3.labels[0].name, 'no')
        self.assertEqual(self.f.archived3.labels[1].name, 'yes')

        self.assertEqual(self.f.archived4.labels[0].name, 'no')
        self.assertEqual(self.f.archived4.labels[1].name, 'yes')
        #etc.

    def test_default_selection(self):
        self.f.clear_selection()
        self.f.update() # default selection

        #archived1 has default='no'
        self.assertEqual(self.f.archived1[0].name, "all")
        self.assertEqual(self.f.archived1[0].is_all, True)
        self.assertEqual(self.f.archived1[0].is_selected, False)
        self.assertEqual(self.f.archived1[0].is_default, False)
        self.assertEqual(self.f.archived1[1].name, "no")
        self.assertEqual(self.f.archived1[1].is_all, False)
        self.assertEqual(self.f.archived1[1].is_selected, True)
        self.assertEqual(self.f.archived1[1].is_default, True)
        self.assertEqual(self.f.archived1[2].name, "yes")
        self.assertEqual(self.f.archived1[2].is_all, False)
        self.assertEqual(self.f.archived1[2].is_selected, False)
        self.assertEqual(self.f.archived1[2].is_default, False)

        #archived2 has default behaviour
        self.assertEqual(self.f.archived2[0].name, "all")
        self.assertEqual(self.f.archived2[0].is_all, True)
        self.assertEqual(self.f.archived2[0].is_selected, True)
        self.assertEqual(self.f.archived2[0].is_default, True)
        self.assertEqual(self.f.archived2[1].name, "no")
        self.assertEqual(self.f.archived2[1].is_all, False)
        self.assertEqual(self.f.archived2[1].is_selected, False)
        self.assertEqual(self.f.archived2[1].is_default, False)
        self.assertEqual(self.f.archived2[2].name, "yes")
        self.assertEqual(self.f.archived2[2].is_all, False)
        self.assertEqual(self.f.archived2[2].is_selected, False)
        self.assertEqual(self.f.archived2[2].is_default, False)

        #archived3 has default='no', hide_all = True
        self.assertEqual(self.f.archived3[0].name, "no")
        self.assertEqual(self.f.archived3[0].is_all, False)
        self.assertEqual(self.f.archived3[0].is_selected, True)
        self.assertEqual(self.f.archived3[0].is_default, True)
        self.assertEqual(self.f.archived3[1].name, "yes")
        self.assertEqual(self.f.archived3[1].is_all, False)
        self.assertEqual(self.f.archived3[1].is_selected, False)
        self.assertEqual(self.f.archived3[1].is_default, False)

        #archived4 has hide_all = True
        self.assertEqual(self.f.archived4[0].name, "no")
        self.assertEqual(self.f.archived4[0].is_all, False)
        self.assertEqual(self.f.archived4[0].is_selected, False)
        self.assertEqual(self.f.archived4[0].is_default, False)
        self.assertEqual(self.f.archived4[1].name, "yes")
        self.assertEqual(self.f.archived4[1].is_all, False)
        self.assertEqual(self.f.archived4[1].is_selected, False)
        self.assertEqual(self.f.archived4[1].is_default, False)


    def test_facet_selection(self):
        self.f.clear_selection()
        self.f.update()
        self.assertEqual(set(self.f.unfiltered_collection()),
                         set(ShopItem.objects.all()))
        self.assertEqual(set(self.f.matching_items()), set(ShopItem.objects.filter(is_archived=False)))

        check_counts(self, self.f.price, (
            ('any price', 7, True),
            ('free', 1, False),
            ('$0-$50', 4, False),
            ('$50-$100', 4, False),
            ('$100 or more', 2, False),
        ))

        check_counts(self, self.f.colours, (
            ('all', 7, True),
            ('blue', 2, False),
            ('green', 2, False),
            ('indigo', 1, False),
            ('orange', 1, False),
            ('red', 3, False),
            ('violet', 2, False),
            ('yellow', 2, False),
        ))

        check_counts(self, self.f.tags, (
            ('all', 7, True),
            ('shirt', 6, False),
            ('red', 3, False),
            ('blue', 2, False),
            ('green', 2, False),
            ('multicoloured', 2, False),
            ('violet', 2, False),
            ('yellow', 2, False),
            ('free', 1, False),
            ('indigo', 1, False),
            ('orange', 1, False),
        ))


        # select a single facet
        self.f.price.select_slugs('free')
        # need to call "update" to recalculate everything.
        # before:no change
        self.assertEqual(set(self.f.matching_items()), set(ShopItem.objects.filter(is_archived=False)))
        self.f.update()
        # after: change
        self.assertEqual(set(self.f.matching_items()), set(ShopItem.objects.filter
            (dollars=0)))

        check_counts(self, self.f.price, (
            ('any price', 7, False),
            ('free', 1, True),
            ('$0-$50', 4, False),
            ('$50-$100', 4, False),
            ('$100 or more', 2, False),
        ))

        check_counts(self, self.f.colours, (
            ('all', 1, True),
            ('blue', 0, False),
            ('green', 0, False),
            ('indigo', 0, False),
            ('orange', 0, False),
            ('red', 0, False),
            ('violet', 1, False),
            ('yellow', 0, False),
        ))

        check_counts(self, self.f.tags, (
            ('all', 1, True),
            ('free', 1, False),
            ('shirt', 1, False),
            ('violet', 1, False),
            ('blue', 0, False),
            ('green', 0, False),
            ('indigo', 0, False),
            ('multicoloured', 0, False),
            ('orange', 0, False),
            ('red', 0, False),
            ('yellow', 0, False),
        ))

        # change the selected label of a facet (price is single-select)
        self.f.price.select_slugs('0-50')
        self.f.update()
        self.assertEqual(set(self.f.matching_items()), set(ShopItem.objects.filter
            (dollars__lte=50, is_archived=False)))

        check_counts(self, self.f.price, (
            ('any price', 7, False),
            ('free', 1, False),
            ('$0-$50', 4, True),
            ('$50-$100', 4, False),
            ('$100 or more', 2, False),
         ))

        check_counts(self, self.f.colours, (
            ('all', 4, True),
            ('blue', 1, False),
            ('green', 1, False),
            ('indigo', 0, False),
            ('orange', 0, False),
            ('red', 1, False),
            ('violet', 1, False),
            ('yellow', 0, False),
        ))

        check_counts(self, self.f.tags, (
            ('all', 4, True),
            ('shirt', 4, False),
            ('blue', 1, False),
            ('free', 1, False),
            ('green', 1, False),
            ('red', 1, False),
            ('violet', 1, False),
            ('indigo', 0, False),
            ('multicoloured', 0, False),
            ('orange', 0, False),
            ('yellow', 0, False),
        ))


        # add another facet - red-coloured shirts for $0-$50
        self.f.colours.select_slugs('red')
        self.f.update()
        self.assertEqual(set(self.f.matching_items()), set(ShopItem.objects.filter
            (dollars__lte=50, colours=self.red)))

        check_counts(self, self.f.price, (
            ('any price', 3, False),
            ('free', 0, False),
            ('$0-$50', 1, True),
            ('$50-$100', 2, False),
            ('$100 or more', 2, False),
         ))

        # *slightly* unexpected counts here. Since the facet allows the
        # 'union' of tags, the numbers indicate the 'change' of the tags,
        # not the number of results the tags will produce (which would
        # otherwise all be 1 or more).
        check_counts(self, self.f.colours, (
            ('all', 4, False),
            ('blue', 1, False),
            ('green', 1, False),
            ('indigo', 0, False),
            ('orange', 0, False),
            ('red', 1, True),
            ('violet', 1, False),
            ('yellow', 0, False),
        ))

        check_counts(self, self.f.tags, (
            ('all', 1, True),
            ('red', 1, False),
            ('shirt', 1, False),
            ('blue', 0, False),
            ('free', 0, False),
            ('green', 0, False),
            ('indigo', 0, False),
            ('multicoloured', 0, False),
            ('orange', 0, False),
            ('violet', 0, False),
            ('yellow', 0, False),
        ))


        # add several labels to that facet (colour is multi-select,
        # and conjoined with 'OR')
        self.f.colours.select_slugs('blue')
        self.f.update()
        self.assertEqual(set(self.f.matching_items()), set(ShopItem.objects.filter
            (dollars__lte=50, colours__in=[self.red, self.blue])))

        check_counts(self, self.f.price, (
            ('any price', 4, False),
            ('free', 0, False),
            ('$0-$50', 2, True),
            ('$50-$100', 3, False),
            ('$100 or more', 2, False),
         ))

        check_counts(self, self.f.colours, (
            ('all', 4, False),
            ('blue', 1, True),
            ('green', 1, False),
            ('indigo', 0, False),
            ('orange', 0, False),
            ('red', 1, True),
            ('violet', 1, False),
            ('yellow', 0, False),
        ))

        check_counts(self, self.f.tags, (
            ('all', 2, True),
            ('shirt', 2, False),
            ('blue', 1, False),
            ('red', 1, False),
            ('free', 0, False),
            ('green', 0, False),
            ('indigo', 0, False),
            ('multicoloured', 0, False),
            ('orange', 0, False),
            ('violet', 0, False),
            ('yellow', 0, False),
        ))

        # by the way, we can retrieve the facets that are selected
        self.assertEqual(set([x.name for x in self.f.colours.selected()]),
            set(['red', 'blue'])) #TODO: maintain ordering

        #unselect the price facet
        self.f.price.unselect_slugs('0-50')
        self.f.update()
        self.assertEqual(set(self.f.matching_items()), set(ShopItem.objects.filter
            (colours__in=[self.red, self.blue])))

        check_counts(self, self.f.price, (
            ('any price', 4, True),
            ('free', 0, False),
            ('$0-$50', 2, False),
            ('$50-$100', 3, False),
            ('$100 or more', 2, False),
         ))

        check_counts(self, self.f.colours, (
            ('all', 7, False), #clears the other selections
            ('blue', 2, True),
            ('green', 2, False),
            ('indigo', 1, False),
            ('orange', 1, False),
            ('red', 3, True),
            ('violet', 2, False),
            ('yellow', 2, False),
        ))

        check_counts(self, self.f.tags, (
            ('all', 4, True),
            ('shirt', 4, False),
            ('red', 3, False),
            ('blue', 2, False),
            ('multicoloured', 2, False),
            ('yellow', 2, False),
            ('green', 1, False),
            ('indigo', 1, False),
            ('orange', 1, False),
            ('violet', 1, False),
            ('free', 0, False),
        ))

        #unselect all the colour facets
        self.f.colours.clear_selection()
        self.f.update()
        self.assertEqual(set(self.f.matching_items()), set(ShopItem.objects.filter(is_archived=False)))

        # you can pass several labels to a multiselect facet
        self.f.colours.select_slugs('red', 'blue')
        self.f.update()
        self.assertEqual(set(self.f.matching_items()), set(ShopItem.objects.filter
            (colours__in=[self.blue, self.red])))

        # but you cannot pass several labels to a single-select facet
        self.assertRaises(ValueError, self.f.price.select_slugs, 'free', '0-50')

        #select several tag facets
        self.f.tags.select_slugs('blue', 'red')
        # tags are AND-conjoined (ie intersection)
        self.f.update()
        self.assertEqual(set(self.f.matching_items()),
            set(ShopItem.objects.filter(colours=self.blue).filter(colours=self.red))
        )

        # unselect all facets
        self.f.clear_selection()
        self.f.update()
        self.assertEqual(set(self.f.matching_items()), set(ShopItem.objects.filter(is_archived=False)))

        # you selecting a label that doesn't exist has no effect.
        self.f.colours.select_slugs('maroon')
        self.f.update()
        self.assertEqual(set(self.f.matching_items()), set(ShopItem.objects.filter(is_archived=False)))
