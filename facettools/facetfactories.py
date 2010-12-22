from django.db.models import Count
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext, ugettext_lazy as _
from facetitem import FacetItem

class FacetFactoryBase(type):
    def __init__(cls, name, bases, attrs):
        
        if name == 'FacetFactory':
            cls.GET_KEY_MAPPING = {}

        gk =  getattr(cls, 'GET_key', None)   
        if gk is not None:
            cls.GET_KEY_MAPPING[gk] = cls

class FacetFactory(object):
    """
    A simple facet factory, that generates values based on fields in a model.
    
    Subclass with the fields GET_key and model_field, and optionally model_field_label.
    """
    __metaclass__ = FacetFactoryBase
    
    FacetItemModel = FacetItem
    all_label = unicode(_("All"))

    @classmethod
    def is_selected(cls, query_value, selected_value):
        return query_value == selected_value  

    @classmethod
    def GET_value_from_db_value(cls, value):
        """Converts the value stored in the field for this model to the value to use in the GET string"""
        return unicode(value)     

    @classmethod
    def facet_label_from_db_value(cls, value):        
        """Converts the value stored in the field for this model to the value to use in the facet label"""
        return unicode(value)     

    @classmethod
    def filter_param(cls):
        """Returns the relevant filter parameter name"""
        return cls.model_field

    @classmethod
    def filter_param_from_db_value(cls, value):
        """Converts the value stored in the field for this model to **kwargs for a filter. This is to run a test query and count the results."""
        return {cls.filter_param(): value}

    @classmethod
    def filter_param_from_GET_value(cls, value):
        """Converts the value received in in the relevant GET parameter for this model to **kwargs for a filter. This is to apply the given query."""
        return {cls.filter_param(): value}

    @classmethod
    def _facet_label_from_db_value(cls, value):
        if value is None:
            return cls.all_label
        else:
            return cls.facet_label_from_db_value(value)
    
    @classmethod
    def _GET_value_from_db_value(cls, value):
        if value is None:
            return ""
        return cls.GET_value_from_db_value(value)

    @classmethod
    def generate_entire_facet_list(cls, pool): #TODO: cache this
        """
        Ignore annotate's count() - it only works with the entire queryset
        """
        mffl = getattr(cls, 'model_field_for_label', None)
        if not mffl:
            mffl = cls.model_field

        mffo = getattr(cls, 'model_field_for_ordering', None)
        if not mffo:
            mffo = mffl

        fl = pool.values(cls.model_field, mffl).order_by(mffo).distinct() #ignore count.
        for f in fl:
            yield {'value': f[cls.model_field], 'label': f[mffl]}
    
    @classmethod
    def query_from_request(cls, request):
        if request:
            GET_dict = dict(request.GET)
        
            query = {}
            for key, value in GET_dict.iteritems():
                facetfactory = FacetFactory.GET_KEY_MAPPING.get(key, None)            
                if facetfactory is not None:
                    u = facetfactory.filter_param_from_GET_value(value[0])
                    query.update(u) #GET values are normally lists
            return query
        return {}

    @classmethod
    def apply_filter(cls, pool, request):
        q = cls.query_from_request(request)
        
        # remove any trailing slashes
        for query in q:
            if q[query][-1:] == "/":
                q[query] = q[query][0:-1]
                
        return pool.filter(**q)

    @classmethod
    def get_all_facets(cls, *args, **kwargs):
        """
        call FacetFactory.get_all_facets(pool, request, ...) to run all of the defined facets.
        The result is a dictionary of each factory's facet generator.
        """
        results = {}
        for name, factory in FacetFactory.GET_KEY_MAPPING.iteritems():
            results[name] = factory.get_facets(*args, **kwargs)
            
        return results

    @classmethod
    def get_facets(cls, pool, request=None, query={}, include_empty = False, include_all=True):
        """
        Call this on implementing subclasses to 
        """
        if request is not None:
            q = cls.query_from_request(request)
            q.update(query)
        else:
            q = query 
        
        # remove any trailing slashes
        for query in q:
            if q[query][-1:] == "/":
                q[query] = q[query][0:-1]
                
        fp = cls.filter_param()
        selected_value = cls._GET_value_from_db_value(q.get(fp, None))

        if q.has_key(fp):
            del q[fp]
                
        if include_all:
            yield cls.FacetItemModel(
                factory = cls,
                label = cls._facet_label_from_db_value(None),
                value = cls._GET_value_from_db_value(None),
                count = pool.filter(**q).count(),
                selected = cls.is_selected("", selected_value),
                request = request,
                all=True,
            )
        
        #should return a list of all the facets
        facet_query = cls.generate_entire_facet_list(pool)
                
        for f in facet_query:
            if f['value'] is not None: #done that
                r = q.copy()
                r.update(cls.filter_param_from_db_value(f['value']))
                count = pool.filter(**r).count()
                value = cls._GET_value_from_db_value(f['value'])
                label = cls._facet_label_from_db_value(f['label'])
                if count or include_empty:
                    yield cls.FacetItemModel(
                        factory = cls,
                        label = label,
                        value = value,
                        count = count,
                        selected = cls.is_selected(value, selected_value),
                        request = request,
                    )

class SlugFacetFactory(FacetFactory):
    @classmethod
    def is_selected(cls, query_value, selected_value):
        return query_value.lower() == selected_value.lower()

    @classmethod
    def GET_value_from_db_value(cls, value):
        """Converts the value stored in the field for this model to the value to use in the GET string"""
        return slugify(value)

    @classmethod
    def filter_param(cls):
        """Converts the value stored in the field for this model to **kwargs for a filter. This is to run a test query and count the results."""
        return cls.model_field+"__iexact"

class BooleanFacetFactory(FacetFactory):
    @classmethod
    def GET_value_from_db_value(cls, value):
        """Converts the value stored in the field for this model to the value to use in the GET string"""
        if value:
            return "y"
        return "n"

    @classmethod
    def facet_label_from_db_value(cls, value):        
        """Converts the value stored in the field for this model to the value to use in the facet label"""
        if value:
            return "Yes"
        return "No"

    @classmethod
    def filter_param_from_db_value(cls, value):
        """Converts the value stored in the field for this model to **kwargs for a filter. This is to run a test query and count the results."""
        return {cls.model_field: value}

    @classmethod
    def filter_param_from_GET_value(cls, value):
        """Converts the value received in in the relevant GET parameter for this model to **kwargs for a filter. This is to apply the given query."""
        if value.lower() == "y":
            return {cls.model_field: True}
        elif value.lower() == "n":
            return {cls.model_field: False}
            
            
class M2MFacetFactory(FacetFactory):

    @classmethod
    def filter_param(cls):
        """Returns the relevant filter parameter name"""
        return cls.m2m_field+"__"+cls.model_field
    
    @classmethod
    def generate_entire_facet_list(cls, pool): #TODO: cache this
        """
        Ignore annotate's count() - it only works with the entire queryset
        """
        if len(pool) > 0:
            related_model = getattr(type(pool[0]), cls.m2m_field).field.related.parent_model
                
        mffl = getattr(cls, 'model_field_for_label', None)
        if not mffl:
            mffl = cls.model_field
    
        mffo = getattr(cls, 'model_field_for_ordering', None)
        if not mffo:
            mffo = mffl
    
        fl = related_model.objects.values(cls.model_field, mffl).order_by(mffo).distinct() #ignore count.

        for f in fl:
            yield {'value': f[cls.model_field], 'label': f[mffl]}

class IndirectFacetFactory(FacetFactory):
    """ Use IndirectFacetFactory when it's cheaper to supply the facet_pool directly rather than derive from the items to be faceted.
    For example, when Venues have Facilities and Events have Venues use this to facet Events by Facilities.
    Specify facet_pool e.g. Facility.objects.all() and indirect_model_field e.g. 'venue__facilities__slug'.
    """
    @classmethod
    def filter_param(cls):
        """Returns the relevant filter parameter name"""
        return cls.indirect_model_field

    @classmethod
    def generate_entire_facet_list(cls, pool): #TODO: cache this    
        mffl = getattr(cls, 'model_field_for_label', None)
        if not mffl:
            mffl = cls.model_field

        mffo = getattr(cls, 'model_field_for_ordering', None)
        if not mffo:
            mffo = mffl

        fl = cls.facet_pool.values(cls.model_field, mffl).order_by('slug').distinct()
        for f in fl:
            yield {'value': f[cls.model_field], 'label': f[mffl]}