from django.test import TestCase
from django.db import models
from django.template import Template

from facetfactories import *

from django.test import Client
from django.core.handlers.wsgi import WSGIRequest

class RequestFactory(Client):
    """
    Class that lets you create mock Request objects for use in testing.
    
    Usage:
    
    rf = RequestFactory()
    get_request = rf.get('/hello/')
    post_request = rf.post('/submit/', {'foo': 'bar'})
    
    This class re-uses the django.test.client.Client interface, docs here:
    http://www.djangoproject.com/documentation/testing/#the-test-client
    
    Once you have a request object you can pass it to any view function, 
    just as if that view had been hooked up using a URLconf.
    
    """
    def request(self, **request):
        """
        Similar to parent class, but returns the request object as soon as it
        has created it.
        """
        environ = {
            'HTTP_COOKIE': self.cookies,
            'PATH_INFO': '/',
            'QUERY_STRING': '',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '',
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': 80,
            'SERVER_PROTOCOL': 'HTTP/1.1',
        }
        environ.update(self.defaults)
        environ.update(request)
        return WSGIRequest(environ)
        
        
#######
class SimpleFacetItem(models.Model):
    name = models.CharField(max_length=2, db_index=True)
    letter = models.SlugField(max_length=1, db_index=True)
    number = models.IntegerField()

    def __unicode__(self):
        return self.name

class NumberFacets(FacetFactory):
    pool = SimpleFacetItem.objects.all()
    GET_key = "no"
    model_field = "number"

class LetterFacets(SlugFacetFactory):
    pool = SimpleFacetItem.objects.all()
    GET_key = "letter"
    model_field = "letter"
    model_field_for_label = "letter"
#########    
    
    
    

class TestSimpleFacets(TestCase):

    def setUp(self):
        for i in range(0,5):
            for a in "ABCDE":
                SimpleFacetItem.objects.create(name="%s%s" % (a, i), letter=a, number=i)
                
    def test_facet_generation(self):
        self.assertEqual(SimpleFacetItem.objects.count(), 25)
        
        letterfacets = list(LetterFacets().get_facets(pool=SimpleFacetItem.objects.all(), ))
        # numberfacets = NumberFacets().get_facets(SimpleFacetItem, {})
        self.assertEqual(letterfacets[0].__unicode__(), "All* (25)")
        self.assertEqual(letterfacets[1].__unicode__(), "A (5)")
        self.assertEqual(letterfacets[2].__unicode__(), "B (5)")
        self.assertEqual(letterfacets[3].__unicode__(), "C (5)")
        self.assertEqual(letterfacets[4].__unicode__(), "D (5)")
        self.assertEqual(letterfacets[5].__unicode__(), "E (5)")
        
        self.assertEqual(letterfacets[0].selected, True)
        self.assertEqual(letterfacets[1].selected, False)
        #etc

        numberfacets = list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), ))
        self.assertEqual(numberfacets[0].__unicode__(), "All* (25)")
        self.assertEqual(numberfacets[1].__unicode__(), "0 (5)")
        self.assertEqual(numberfacets[2].__unicode__(), "1 (5)")
        self.assertEqual(numberfacets[3].__unicode__(), "2 (5)")
        self.assertEqual(numberfacets[4].__unicode__(), "3 (5)")
        self.assertEqual(numberfacets[5].__unicode__(), "4 (5)")


    def test_facet_subselection(self):
        letterfacets = list(LetterFacets().get_facets(pool=SimpleFacetItem.objects.all(), query={'letter__iexact': 'B' }))
        
        self.assertEqual(unicode(letterfacets[0]), "All (25)")
        self.assertEqual(letterfacets[1].__unicode__(), "A (5)")
        self.assertEqual(letterfacets[2].__unicode__(), "B* (5)")
        self.assertEqual(letterfacets[3].__unicode__(), "C (5)")
        self.assertEqual(letterfacets[4].__unicode__(), "D (5)")
        self.assertEqual(letterfacets[5].__unicode__(), "E (5)")
        #etc
        
        numberfacets = list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), query={'letter__iexact': 'B'}))
        self.assertEqual(numberfacets[0].__unicode__(), "All* (5)")
        self.assertEqual(numberfacets[1].__unicode__(), "0 (1)")
        self.assertEqual(numberfacets[2].__unicode__(), "1 (1)")
        self.assertEqual(numberfacets[3].__unicode__(), "2 (1)")
        self.assertEqual(numberfacets[4].__unicode__(), "3 (1)")
        self.assertEqual(numberfacets[5].__unicode__(), "4 (1)")


    def test_facet_subsubselection(self):
        numberfacets = list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), query={'letter__iexact': 'B', 'number': 2}))
        
        self.assertEqual(len(numberfacets), 6)
        self.assertEqual(numberfacets[0].__unicode__(), "All (5)")
        self.assertEqual(numberfacets[1].__unicode__(), "0 (1)")
        self.assertEqual(numberfacets[2].__unicode__(), "1 (1)")
        self.assertEqual(numberfacets[3].__unicode__(), "2* (1)")
        self.assertEqual(numberfacets[4].__unicode__(), "3 (1)")
        self.assertEqual(numberfacets[5].__unicode__(), "4 (1)")

    def test_query_building(self):
        rf = RequestFactory()
        get_request = rf.get('/hello/?apples=cox&letter=b&no=2')
        qs = FacetFactory.apply_filter(pool=SimpleFacetItem.objects.all(), request=get_request)
        self.assertEqual(set(qs), set(SimpleFacetItem.objects.filter(letter='B', number=2)))

        
    def test_facet_options(self):
        numberfacets = list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), query={'letter__iexact': 'W', 'number': 2}, include_empty=True))
        self.assertEqual(len(numberfacets), 6)
        self.assertEqual(numberfacets[0].__unicode__(), "All (0)")
        self.assertEqual(numberfacets[1].__unicode__(), "0 (0)")
        self.assertEqual(numberfacets[2].__unicode__(), "1 (0)")
        self.assertEqual(numberfacets[3].__unicode__(), "2* (0)")
        self.assertEqual(numberfacets[4].__unicode__(), "3 (0)")
        self.assertEqual(numberfacets[5].__unicode__(), "4 (0)")

        numberfacets = list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), query={'letter__iexact': 'B', 'number': 2}, include_all=False))
        self.assertEqual(len(numberfacets), 5)
        self.assertEqual(numberfacets[0].__unicode__(), "0 (1)")
        #etc

    def test_facet_properties(self):
        numberfacets = list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), query={'letter__iexact': 'B', 'number': 2}))
        self.assertEqual(len(numberfacets), 6)
        self.assertEqual(numberfacets[0].label, "All")
        self.assertEqual(numberfacets[1].label, "0")
        self.assertEqual(numberfacets[2].label, "1")
        self.assertEqual(numberfacets[0].count, 5)
        self.assertEqual(numberfacets[1].count, 1)
        self.assertEqual(numberfacets[2].count, 1)
        #etc
        
    def test_facet_sort(self):
        numberfacets = list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), query={'letter__iexact': 'B', 'number': 2}, include_empty=True))
        numberfacets.sort(key=lambda x: x.count)
        self.assertEqual(len(numberfacets), 6)
        self.assertEqual(numberfacets[0].__unicode__(), "0 (1)")
        self.assertEqual(numberfacets[1].__unicode__(), "1 (1)")
        self.assertEqual(numberfacets[2].__unicode__(), "2* (1)")
        self.assertEqual(numberfacets[3].__unicode__(), "3 (1)")
        self.assertEqual(numberfacets[4].__unicode__(), "4 (1)")
        self.assertEqual(numberfacets[5].__unicode__(), "All (5)")

    def test_GET(self):
        numberfacets = list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), query={'letter__iexact': 'B', 'number': 2}, include_empty=True))
        self.assertEqual(len(numberfacets), 6)
        self.assertEqual(numberfacets[0].get_string(), "no=")
        self.assertEqual(numberfacets[1].get_string(), "no=0")
        self.assertEqual(numberfacets[2].get_string(), "no=1")
        self.assertEqual(numberfacets[3].get_string(), "no=2")
        self.assertEqual(numberfacets[4].get_string(), "no=3")
        self.assertEqual(numberfacets[5].get_string(), "no=4")
        
        # trivial request
        rf = RequestFactory()
        get_request = rf.get('/hello/?')

        numberfacets = list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), include_empty=True, request=get_request))
        self.assertEqual(len(numberfacets), 6)
        self.assertEqual(numberfacets[0].get_string(), "")
        self.assertEqual(numberfacets[1].get_string(), "no=0")
        self.assertEqual(numberfacets[2].get_string(), "no=1")
        self.assertEqual(numberfacets[3].get_string(), "no=2")
        self.assertEqual(numberfacets[4].get_string(), "no=3")
        self.assertEqual(numberfacets[5].get_string(), "no=4")
        
        # more advanced request
        rf = RequestFactory()
        get_request = rf.get('/hello/?apples=cox&no=2')

        numberfacets = list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), include_empty=True, request=get_request))
        self.assertEqual(len(numberfacets), 6)
        self.assertEqual(numberfacets[0].get_string(), "apples=cox")
        self.assertEqual(numberfacets[1].get_string(), "apples=cox&no=0")
        self.assertEqual(numberfacets[2].get_string(), "apples=cox&no=1")
        self.assertEqual(numberfacets[3].get_string(), "apples=cox&no=2")
        self.assertEqual(numberfacets[4].get_string(), "apples=cox&no=3")
        self.assertEqual(numberfacets[5].get_string(), "apples=cox&no=4")
        
        letterfacets = list(LetterFacets().get_facets(pool=SimpleFacetItem.objects.all(), include_empty=True, request=get_request))
        self.assertEqual(len(letterfacets), 6)
        self.assertEqual(letterfacets[0].get_string(), "apples=cox&no=2")
        self.assertEqual(letterfacets[1].get_string(), "apples=cox&letter=a&no=2")
        self.assertEqual(letterfacets[2].get_string(), "apples=cox&letter=b&no=2")
        self.assertEqual(letterfacets[3].get_string(), "apples=cox&letter=c&no=2")
        self.assertEqual(letterfacets[4].get_string(), "apples=cox&letter=d&no=2")
        self.assertEqual(letterfacets[5].get_string(), "apples=cox&letter=e&no=2")

    def test_render(self):
        rf = RequestFactory()
        get_request = rf.get('/hello/?apples=cox&no=1')
        numberfacets = list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), include_empty=True, request=get_request))
        self.assertEqual(len(numberfacets), 6)
        self.assertEqual(numberfacets[0].render(), '<a href="?apples=cox">All&nbsp;<span class="count">(25)</span></a>')
        self.assertEqual(numberfacets[1].render(), '<a href="?apples=cox&amp;no=0">0&nbsp;<span class="count">(5)</span></a>')
        self.assertEqual(numberfacets[2].render(), '<a href="?apples=cox&amp;no=1" class="selected">1&nbsp;<span class="count">(5)</span></a>')
        # etc       


    def test_render_options(self):
        rf = RequestFactory()
        get_request = rf.get('/hello/?apples=cox&no=2')
        numberfacets = list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), include_empty=True, request=get_request))
        self.assertEqual(len(numberfacets), 6)
        
        t = Template("{{ facet.count }} item{{ facet.count|pluralize }} have {{ facet.label }} banana{{ facet.label|pluralize }}")
        
        self.assertEqual(numberfacets[2].render(template=t), "5 items have 1 banana")
        self.assertEqual(numberfacets[3].render(template=t), "5 items have 2 bananas")
        self.assertTrue(numberfacets[2].render(template_file="facettools/facet.html"))
        self.assertEqual(numberfacets[2].render(template_string="woo {{ facet.label }} the yay <span>{{ facet.count }}</span>"), "woo 1 the yay <span>5</span>")
        # etc

    def test_edge(self):
        rf = RequestFactory()
        get_request = rf.get('/hello/?letter=w')
        numberfacets = list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), request=get_request))
        self.assertEqual(len(numberfacets), 1)
        self.assertEqual(unicode(numberfacets[0]), "All* (0)")
        letterfacets = list(LetterFacets().get_facets(pool=SimpleFacetItem.objects.all(), request=get_request))
        self.assertEqual(len(letterfacets), 6)
        self.assertEqual(unicode(letterfacets[0]), "All (25)")
        self.assertEqual(letterfacets[1].__unicode__(), "A (5)")
        self.assertEqual(letterfacets[2].__unicode__(), "B (5)")
        self.assertEqual(letterfacets[3].__unicode__(), "C (5)")
        self.assertEqual(letterfacets[4].__unicode__(), "D (5)")
        self.assertEqual(letterfacets[5].__unicode__(), "E (5)")
        
    def test_facet_from_GET(self):
        # more advanced request
        rf = RequestFactory()
        get_request = rf.get('/hello/?apples=cox&no=2')
        l1 = list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), query={'number': '2'}))
        l2 = list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), request=get_request)) 
        self.assertEqual(
            l1,
            l2,
        )
        self.assertEqual(
            list(LetterFacets().get_facets(pool=SimpleFacetItem.objects.all(), query={'number': '2'})),
            list(LetterFacets().get_facets(pool=SimpleFacetItem.objects.all(), request=get_request)),
        )
        
        get_request1 = rf.get('/hello/?letter=A&no=2&citrus=lemon')
        get_request2 = rf.get('/hello/?letter=a&no=2&citrus=lemon') #lowercase
        self.assertEqual(
            list(LetterFacets().get_facets(pool=SimpleFacetItem.objects.all(), request=get_request1)),
            list(LetterFacets().get_facets(pool=SimpleFacetItem.objects.all(), request=get_request2))
        )

        get_request = rf.get('/hello/?letter=A&no=2&citrus=lemon')
                
        self.assertEqual(
            list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), query={'letter__iexact': 'A', 'number': 2})),
            list(NumberFacets().get_facets(pool=SimpleFacetItem.objects.all(), request=get_request)),
        )
        self.assertEqual(
            list(LetterFacets().get_facets(pool=SimpleFacetItem.objects.all(), query={'letter__iexact': 'A', 'number': 2})), # do we care about the discrepancy?
            list(LetterFacets().get_facets(pool=SimpleFacetItem.objects.all(), request=get_request)),
        )
    

class AgeRange(models.Model):
    title = models.CharField(max_length=10)
    slug = models.SlugField(max_length=10)
    rank = models.IntegerField()
    
    class Meta:
        ordering = ('rank',)
    
    def __unicode__(self):
        return self.title
    
class Tag(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

    def __unicode__(self):
        return self.title
        
class Facility(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

class Venue(models.Model):
    name = models.CharField(max_length=100)
    facilities = models.ManyToManyField(Facility, null=True)
    
    
class Event(models.Model):
    title = models.CharField(max_length=100)
    is_free = models.BooleanField()
    age = models.ForeignKey(AgeRange, null=True)
    tags = models.ManyToManyField(Tag)
    venue = models.ForeignKey(Venue, null=True)

    def __unicode__(self):
        return self.title

class FreeFacets(BooleanFacetFactory):
    pool = Event.objects.all()
    GET_key = "free"
    model_field = "is_free"
    
    @classmethod
    def facet_label_from_db_value(cls, value):
        if value:
            return "Free"
        else:
            return "Not free"
            
class AgeFacets(FacetFactory):
    pool = Event.objects.all()
    GET_key = 'age'
    model_field = 'age__slug'
    model_field_for_label = 'age__title'
    model_field_for_ordering = 'age__rank'

class TagFacets(M2MFacetFactory):
    pool = Event.objects.all()
    GET_key = 'tag'
    m2m_field = 'tags'
    model_field = 'slug'
    model_field_for_label = 'title'
    model_field_for_ordering = 'title'

    
        
class TestComplexFacets(TestCase):

    def setUp(self):
        self.ar = []
        for i in range(0,5):
            ages = (i*3, (i+1)*3)
            self.ar.append(AgeRange.objects.create(title="%s to %s" % ages, slug="%s-%s" % ages, rank=i))
        
        t1 = Tag.objects.create(title="Daddy", slug="daddy")
        t2 = Tag.objects.create(title="Chips", slug="chips")
            
        self.events = []
        for r in self.ar:
            self.events.append(Event.objects.create(title="Free event for %s" % r, is_free=True, age=r))
            self.events.append(Event.objects.create(title="Costly event for %s" % r, is_free=False, age=r))

        for i, event in enumerate(self.events):
            if i % 2 == 0:
                event.tags.add(t1)
            if i % 3 == 0:
                event.tags.add(t2)
        
    
    def test_simple_facet(self):
        self.assertEqual(Event.objects.count(), 10)
        
        pricefacets = list(FreeFacets().get_facets(pool=Event.objects.all()))        
        self.assertEqual(pricefacets[0].get_string(), "free=")
        self.assertEqual(pricefacets[1].get_string(), "free=n")
        self.assertEqual(pricefacets[2].get_string(), "free=y")

        self.assertEqual(pricefacets[0].__unicode__(), "All* (10)")
        self.assertEqual(pricefacets[1].__unicode__(), "Not free (5)")
        self.assertEqual(pricefacets[2].__unicode__(), "Free (5)")
        
        
    def test_query_building(self):
        rf = RequestFactory()
        get_request = rf.get('/hello/?apples=cox&free=y')
        qs = FacetFactory.apply_filter(pool=Event.objects.all(), request=get_request)
        self.assertEqual(set(qs), set(Event.objects.filter(is_free=True)))

    def test_fk_facet(self):
        agefacets = list(AgeFacets().get_facets(pool=Event.objects.all()))
        
        self.assertEqual(agefacets[0].__unicode__(), "All* (10)")
        self.assertEqual(agefacets[1].__unicode__(), "0 to 3 (2)")
        self.assertEqual(agefacets[2].__unicode__(), "3 to 6 (2)")

        self.assertEqual(agefacets[0].get_string(), "age=")
        self.assertEqual(agefacets[1].get_string(), "age=0-3")
        self.assertEqual(agefacets[2].get_string(), "age=3-6")

        # etc.
        
    def test_fk_facet_query(self):
        rf = RequestFactory()
        get_request = rf.get('/hello/?apples=cox&free=n&age=3-6')
        qs = FacetFactory.apply_filter(pool=Event.objects.all(), request=get_request)
        self.assertEqual(set(qs), set(Event.objects.filter(is_free=False, age__slug="3-6")))

    def test_m2m_facet(self):
        tagfacets = list(TagFacets().get_facets(pool=Event.objects.all()))
        
        self.assertEqual(tagfacets[0].__unicode__(), "All* (10)")
        self.assertEqual(tagfacets[1].__unicode__(), "Chips (4)")
        self.assertEqual(tagfacets[2].__unicode__(), "Daddy (5)")

        self.assertEqual(tagfacets[0].get_string(), "tag=")
        self.assertEqual(tagfacets[1].get_string(), "tag=chips")
        self.assertEqual(tagfacets[2].get_string(), "tag=daddy")


    def test_m2m_facet_query(self):
        rf = RequestFactory()
        get_request = rf.get('/hello/?apples=cox&age=3-6')        
        tagfacets = list(TagFacets().get_facets(pool=Event.objects.all(), request=get_request))
        self.assertEqual(tagfacets[0].__unicode__(), "All* (2)")
        self.assertEqual(tagfacets[1].__unicode__(), "Chips (1)")
        self.assertEqual(tagfacets[2].__unicode__(), "Daddy (1)")

        get_request = rf.get('/hello/?apples=cox&age=3-6&tag=daddy')        
        tagfacets = list(TagFacets().get_facets(pool=Event.objects.all(), request=get_request))
        self.assertEqual(tagfacets[0].__unicode__(), "All (2)")
        self.assertEqual(tagfacets[1].__unicode__(), "Chips (1)")
        self.assertEqual(tagfacets[2].__unicode__(), "Daddy* (1)")

        qs = FacetFactory.apply_filter(pool=Event.objects.all(), request=get_request)
        self.assertEqual(set(qs), set(Event.objects.filter(age__slug="3-6", tags__slug="daddy")))                

class FacilityFacets(IndirectFacetFactory):
    facet_pool = Facility.objects.all()
    model_field = 'slug'
    indirect_model_field = 'venue__facilities__slug'
    model_field_for_ordering = 'slug'
    model_field_for_label = 'name'
    GET_key = "facility"
    
class TestIndirectFacet(TestCase):
    def setUp(self):
        f1 = Facility.objects.create(name="cafe",slug="cafe")
        f2 = Facility.objects.create(name="wheelchair access",slug="wheelchair-access")
        v1 = Venue.objects.create(name="observatory")
        v1.facilities.add(f1)
        v2 = Venue.objects.create(name="city hall")
        v2.facilities.add(f1)
        v2.facilities.add(f2)
        e1 = Event.objects.create(title="festi",venue=v1)
        e2 = Event.objects.create(title="firework",venue=v2)
    
    def test_creation(self):
        facilityfacets = list(FacilityFacets().get_facets(pool=Event.objects.all()))
        
        self.assertEqual(facilityfacets[0].__unicode__(), "All* (2)")
        self.assertEqual(facilityfacets[1].__unicode__(), "cafe (2)")
        self.assertEqual(facilityfacets[2].__unicode__(), "wheelchair access (1)")

    def test_indirect_facet_query(self):
        rf = RequestFactory()
        get_request = rf.get('/hello/?apples=cox&facility=cafe')
        qs = FacetFactory.apply_filter(pool=Event.objects.all(), request=get_request)
        self.assertEqual(set(qs), set(Event.objects.filter(venue__facilities__slug="cafe")))

"""
test
Also need to incorporate and test search_url
Also, later, need to make facets into registries (with pool defined there)
"""
    
