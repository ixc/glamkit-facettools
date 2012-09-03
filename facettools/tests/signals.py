from django.test import TestCase

from .models import ShopItem, Colour, ShopItemFacetGroup
from .utils import check_counts


class TestModelSignals(TestCase):
    def setUp(self):
        self.f = ShopItemFacetGroup()
        self.f.watch_model(ShopItem)
        self.red = Colour.objects.create(name="red")
        self.orange = Colour.objects.create(name="orange")
        self.yellow = Colour.objects.create(name="yellow")
        self.green = Colour.objects.create(name="green")
        self.blue = Colour.objects.create(name="blue")
        self.indigo = Colour.objects.create(name="indigo")
        self.violet = Colour.objects.create(name="violet")
        ShopItem.objects.all().delete()
        self.f.rebuild_index()

    def tearDown(self):
        self.f.unwatch_model(ShopItem)
        Colour.objects.all().delete()

    def test_empty(self):

        check_counts(self, self.f.price, (
            ('any price', 0, True),
        ))

        check_counts(self, self.f.colours, (
            ('all', 0, True),
        ))

        check_counts(self, self.f.tags, (
            ('all', 0, True),
        ))


    def test_create(self):
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

        # (Sigh) django doesn't send signals if m2m relations are updated
        # and m2m_changed signal isn`t part of Django 1.0
        self.free_violet_shirt.save()
        self.red_shirt.save()
        self.green_shirt.save()
        self.blue_shirt.save()

        # How are we doing so far
        self.f.update()

        check_counts(self, self.f.price, (
            ('any price', 5, True),
            ('free', 1, False),
            ('$0-$50', 4, False),
            ('$50-$100', 3, False)
        ))

        check_counts(self, self.f.colours, (
            ('all', 5, True),
            ('blue', 1, False),
            ('green', 1, False),
            ('red', 1, False),
            ('violet', 1, False),
        ))

        check_counts(self, self.f.tags, (
            ('all', 5, True),
            ('shirt', 4, False),
            ('blue', 1, False),
            ('free', 1, False),
            ('green', 1, False),
            ('red', 1, False),
            ('violet', 1, False),
        ))

        self.red_and_yellow_shirt = ShopItem.objects.create(
            name="red and yellow shirt", dollars=100
        )
        self.red_and_yellow_shirt.colours.add(self.red, self.yellow)

        # (Sigh)
        self.red_and_yellow_shirt.save()

        self.f.update()

        check_counts(self, self.f.price, (
            ('any price', 6, True),
            ('free', 1, False),
            ('$0-$50', 4, False),
            ('$50-$100', 4, False),
            ('$100 or more', 1, False),
        ))

        check_counts(self, self.f.colours, (
            ('all', 6, True),
            ('blue', 1, False),
            ('green', 1, False),
            ('red', 2, False),
            ('violet', 1, False),
            ('yellow', 1, False),
        ))

        check_counts(self, self.f.tags, (
            ('all', 6, True),
            ('shirt', 5, False),
            ('red', 2, False),
            ('blue', 1, False),
            ('free', 1, False),
            ('green', 1, False),
            ('multicoloured', 1, False),
            ('violet', 1, False),
            ('yellow', 1, False),
        ))

    def test_update(self):
        self.red_shirt = ShopItem.objects.create(name="red shirt",
                                                 dollars=50)
        self.red_shirt.colours.add(self.red)

        self.green_shirt = ShopItem.objects.create(name="green shirt",
                                                         dollars=50)
        self.green_shirt.colours.add(self.green)

        self.blue_shirt = ShopItem.objects.create(name="blue shirt",
                                                         dollars=50)
        self.blue_shirt.colours.add(self.blue)

        # (Sigh) django doesn't send signals if m2m relations are updated
        # and m2m_changed signal isn`t part of Django 1.0
        self.red_shirt.save()
        self.green_shirt.save()
        self.blue_shirt.save()

        # How are we doing so far
        self.f.update()

        check_counts(self, self.f.price, (
            ('any price', 3, True),
            ('$0-$50', 3, False),
            ('$50-$100', 3, False)
        ))

        # OH WOW THERE IS A SALE ON RED SHIRTS
        self.red_shirt.dollars = 49
        self.red_shirt.save()

        self.f.update()

        check_counts(self, self.f.price, (
            ('any price', 3, True),
            ('$0-$50', 3, False),
            ('$50-$100', 2, False)
        ))

    def test_delete(self):
        self.red_shirt = ShopItem.objects.create(name="red shirt",
                                                 dollars=50)
        self.red_shirt.colours.add(self.red)

        self.green_shirt = ShopItem.objects.create(name="green shirt",
                                                         dollars=50)
        self.green_shirt.colours.add(self.green)

        self.blue_shirt = ShopItem.objects.create(name="blue shirt",
                                                         dollars=50)
        self.blue_shirt.colours.add(self.blue)

        # (Sigh) django doesn't send signals if m2m relations are updated
        # and m2m_changed signal isn`t part of Django 1.0
        self.red_shirt.save()
        self.green_shirt.save()
        self.blue_shirt.save()

        # How are we doing so far
        self.f.update()

        check_counts(self, self.f.colours, (
            ('all', 3, True),
            ('blue', 1, False),
            ('green', 1, False),
            ('red', 1, False),
        ))

        # OH WOW WE HAVE RUN OUT OF BLUE SHIRTS
        self.blue_shirt.delete()
        self.f.update()

        check_counts(self, self.f.colours, (
            ('all', 2, True),
            ('green', 1, False),
            ('red', 1, False),
        ))
