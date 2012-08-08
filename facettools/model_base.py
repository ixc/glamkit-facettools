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

    @classmethod
    def watch_model(cls, model):
        pre_save.connect(cls.pre_save, sender=model)
        post_save.connect(cls.post_save, sender=model)
        pre_delete.connect(cls.pre_delete, sender=model)
        if m2m_changed is not None:
            m2m_changed.connect(cls.m2m_changed, sender=model)

    @classmethod
    def unwatch_model(cls, model):
        pre_save.disconnect(cls.pre_save, sender=model)
        post_save.disconnect(cls.post_save, sender=model)
        pre_delete.disconnect(cls.pre_delete, sender=model)
        if m2m_changed is not None:
            m2m_changed.disconnect(cls.m2m_changed, sender=model)

    @classmethod
    def pre_save(cls, sender, **kwargs):
        instance = kwargs.pop('instance')
        if instance.pk:
            cls.unindex_item(instance)


    @classmethod
    def post_save(cls, sender, **kwargs):
        instance = kwargs.pop('instance')
        if instance in cls.unfiltered_collection():
            cls.index_item(instance)

    @classmethod
    def pre_delete(cls, sender, **kwargs):
        instance = kwargs.pop('instance')
        #remove current facets
        cls.unindex_item(instance)

    @classmethod
    def m2m_changed(cls, sender, **kwargs):
        instance = kwargs.pop('instance')
        if instance in cls.unfiltered_collection():
            cls.unindex_item(instance)
            cls.index_item(instance)

