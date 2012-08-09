from django.db.models.signals import pre_save, post_save, pre_delete
try:
    from django.db.models.signals import m2m_changed
except ImportError:
    m2m_changed = None
from facettools.base import FacetGroup

class ModelFacetGroup(FacetGroup):
    """
    A Facetgroup that knows about model CRUD operations
    """

    def watch_model(self, model):
        pre_save.connect(self.pre_save, sender=model)
        post_save.connect(self.post_save, sender=model)
        pre_delete.connect(self.pre_delete, sender=model)
        if m2m_changed is not None:
            m2m_changed.connect(self.m2m_changed, sender=model)

    def unwatch_model(self, model):
        pre_save.disconnect(self.pre_save, sender=model)
        post_save.disconnect(self.post_save, sender=model)
        pre_delete.disconnect(self.pre_delete, sender=model)
        if m2m_changed is not None:
            m2m_changed.disconnect(self.m2m_changed, sender=model)

    def pre_save(self, sender, **kwargs):
        instance = kwargs.pop('instance')
        if instance.pk:
            self.unindex_item(instance)

    def post_save(self, sender, **kwargs):
        instance = kwargs.pop('instance')
        if instance in self.unfiltered_collection():
            self.index_item(instance)

    def pre_delete(self, sender, **kwargs):
        instance = kwargs.pop('instance')
        #remove current facets
        self.unindex_item(instance)

    def m2m_changed(self, sender, **kwargs):
        instance = kwargs.pop('instance')
        if instance in self.unfiltered_collection():
            self.unindex_item(instance)
            self.index_item(instance)

