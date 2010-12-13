from django.template import Template, Context
from django.template.loader import render_to_string


class FacetItem(object):
    def __init__(self, factory, value, label, count=None, selected=False, request=None, all=False):
        self.factory = factory
        self.value = value
        self.label = label
        self.count = count
        self.selected = selected
        self.request = request
        self.all = all
                
    def __unicode__(self):
        if self.selected:
            s = "*"
        else:
            s = ""
        return "%s%s (%s)" % (self.label, s, self.count)
        
    def __repr__(self):
        return unicode(self)
        
    def __cmp__(self, other):
        if self.all:
            return 1 #always comes first
        return cmp(self.label, other.label)
        
    def __eq__(self, other):
        return self.label == other.label and self.count == other.count and self.factory == other.factory and self.all == other.all and self.value == other.value
    
    def get_string(self):
        if not self.request:
            return "%s=%s" % (self.factory.GET_key, self.value)
        else:
            q = self.request.GET.copy()
            if self.value == "":
                if q.has_key(self.factory.GET_key):
                    del q[self.factory.GET_key]
            else:
                q[self.factory.GET_key] = self.value
            return q.urlencode()
                
    def render(self, template=None, template_file="facettools/facet.html", template_string="", extra_context={}):
        c_dict = {'facet': self}
        c_dict.update(extra_context)
        
        if template is not None:
            t = template
            return t.render(Context(c_dict))
        
        if template_string:
            return Template(template_string).render(Context(c_dict))
        
        return render_to_string(template_file, c_dict)


