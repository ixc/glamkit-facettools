import sys

from django.template.defaultfilters import slugify
from django.utils.datastructures import SortedDict

from .utils import get_verbose_name, is_iterable

class FacetLabel(object):
    def __init__(
        self,
        facet,
        name,
        slug=None,
        is_all=False,
        is_selected=False,
        is_default=False
    ):
        # the facet that I am a label of
        self.facet = facet
        # the string that is displayed
        self.name = name
        if slug is None:
            self.slug = slugify(self.name)
        else:
            self.slug = slug
        # the set of matching items (when no other facets are selected)
        # use `get_/set_items` to get and set.
        self._items = self.initialise_items()
        self.is_all = is_all
        self._matching_items = None
        self.is_selected = is_selected
        self.is_default = is_default

    @property
    def items(self):
        return self._items

    def set_items(self, val, inhibit_save=False):
        self._items = val
        if not inhibit_save:
            self.save()

    def add_item(self, item, inhibit_save=False):
        # Assume we have a single item
        self._items.add(item)
        if not inhibit_save:
            self.save()

    def clear_items(self, inhibit_save=False):
        self.set_items(set(), inhibit_save)

    def matching_items(self):
        """
        The heart of the matter:

        Returns the items that are (or would be) matched if the item is
        selected, in combination with any other facet selections.

        This is tricky because if a sibling label is selected and will
        become unselected, or if there is a union relation between siblings,
        we need to take that effect into account.
        """

        if self._matching_items is None:
            if self.is_all:
                # then ignore whatever is selected
                result = self.facet.group.matching_items(ignore=[self.facet])
            elif self.facet.select_multiple and self.facet.intersect_if_multiple:
                # then simulate additional intersection
                result = self.facet.group.matching_items() & self.items
            else:
                # then simulate intersection as though no other labels were
                # selected
                result = self.facet.group.matching_items(ignore=[self.facet]) & \
                       self.items

            self._matching_items = result or []
        return self._matching_items

    def invalidate(self):
        self._matching_items = None

    @property
    def count(self):
        return len(self.matching_items())

    @property
    def key(self):
        return "%s__%s" % (self.facet.key, self.slug)

    def __eq__(self, other):
        if not isinstance(other, FacetLabel):
            return False
        return (self.key == other.key
            and self.facet == other.facet)

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return "<%s: %s (%s)>" % (self.__class__.__name__, self.name,
                                  self.count)

    def initialise_items(self):
        # subclasses may retrieve a stored set for this label
        return set()

    def save(self):
        # a no-op, but used in subclasses that provide storage
        pass

class Facet(object):
    """
    A collection of FacetLabels, that is in turn grouped in a FacetGroup
    """
    _FacetLabelClass = FacetLabel

    def __init__(self,
         name,
         group, #the FacetGroup that contains this facet
         slug=None, #the slug of this facet, e.g. "colour"
         all_label="all",
         all_label_slug=None,
         cmp_func=None,
         select_multiple=False,
         intersect_if_multiple=False,
         default_selected_slugs=None, #a list of labels (strings) to select by default
         #TODO: if default_selected_slugs == True, then all labels are selected by default.
         hide_all=False, #set to true to prevent the "all_label" from being used or shown.
    ):
        self.group = group
        self.name = name
        if slug is None:
            self.slug = slugify(name)
        else:
            self.slug = slug
        self.all_label = all_label
        if all_label_slug is None:
            self.all_label_slug = slugify(all_label)
        else:
            self.all_label_slug = all_label_slug
        if cmp_func:
            self.cmp_func = cmp_func
        else:
            self.cmp_func = lambda a, b: cmp(a.slug, b.slug)
        self.select_multiple = select_multiple
        self.intersect_if_multiple = intersect_if_multiple

        if default_selected_slugs is None:
            self.default_selected_slugs = [self.all_label_slug]
        elif is_iterable(default_selected_slugs):
            self.default_selected_slugs = default_selected_slugs
        else:
            self.default_selected_slugs = [default_selected_slugs]

        self.hide_all=hide_all

        self.clear_items()

    @property
    def key(self):
        return "%s__%s" % (self.group.key(), self.slug)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.labels[item]
        else:
            return self._label_dict[item]

    def clear_items(self):
        """
        Clearing items on a facet means resetting labels.
        Subclasses that implement storage may want to purge the cache.
        """
        self._label_dict = {}

        if not self.hide_all:
            self._label_dict[self.all_label_slug] = self._FacetLabelClass(
                facet=self, name=self.all_label, slug=self.all_label_slug,
                is_all=True)
            if self.all_label_slug in self.default_selected_slugs:
                self._label_dict[self.all_label_slug].is_default = True
                self._label_dict[self.all_label_slug].is_selected = True
        # dict of FacetLabel objects, for bookkeeping
        self.labels = None # a sorted list of FacetLabels objects for
        # displaying, generated by calling update()
        self._matching_items = None

    def index_item(self, item, inhibit_save=False):
        # call get_FOO_facet on the item
        attr_name = "get_%s_facet" % self.slug.replace("-", "")
        attr = getattr(self.group, attr_name, None)

        if attr:
            facet_labels = attr(item)
        else:
            attr = getattr(item, attr_name, None)
            if attr:
                facet_labels = attr()
            else:
                facet_labels = None

        if facet_labels is not None:
            if not is_iterable(facet_labels):
                facet_labels = [facet_labels]
            self.index_labels(facet_labels, item, inhibit_save)

        # add every item to the 'all' facet
        if not self.hide_all:
            self._label_dict[self.all_label_slug].add_item(item)

    def unindex_item(self, item, inhibit_save=False):
        labels_to_remove = set()
        for facet_label in self._label_dict.values():
            facet_label.items.discard(item)
            if len(facet_label.items) == 0: #empty label! delete it.
                labels_to_remove.add(facet_label.slug)
            if not inhibit_save:
                facet_label.save()

        for v in labels_to_remove:
            del self._label_dict[v]

    def index_labels(self, facet_labels, item, inhibit_save=False):
        for label in facet_labels:
            # initialise a FacetLabel if we have to
            ltext = unicode(label)
            slug = slugify(ltext)
            if slug not in self._label_dict:
                self._label_dict[slug] = self._FacetLabelClass(facet=self,
                                                name=ltext, slug=slug)
                if ltext in self.default_selected_slugs:
                    self._label_dict[slug].is_default = True
                    self._label_dict[slug].is_selected = True


            self._label_dict[slug].add_item(item)
        if not inhibit_save:
            self.save()

    def save(self):
        # save all my labels (it's a no-op, but subclasses may save to storage)
        for label in self._label_dict.values():
            label.save()

    def matching_items(self):
        if self._matching_items is None:
            for facet_label in self.selected():
                if self._matching_items is None:
                    self._matching_items = facet_label.items.copy()
                else:
                    if self.select_multiple and self.intersect_if_multiple:
                        # take intersection of selected facet_labels
                        self._matching_items &= facet_label.items
                    else:
                        # take union of selected facet_labels
                        self._matching_items |= facet_label.items

        return self._matching_items

    def invalidate(self):
        self._matching_items = None
        for facet_label in self._label_dict.values():
            facet_label.invalidate()

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.name)

    def sort(self, cmp_func=None):
        if cmp_func is None:
            cmp_func = self.cmp_func

        def _sort_func(a, b):
            if a.is_all:
                return -1
            if b.is_all:
                return 1

            return cmp_func(a, b)

        unsorted = self._label_dict.values()
        self.labels = sorted(unsorted, cmp=_sort_func)

    def select_slugs(self, *slugs):
        """
        Mark label(s) of this facet as being selected by passing in a list of slugs.
        """

        # Can't select more than one label, unless select_multiple is true
        if len(slugs) > 1:
            if not self.select_multiple:
                raise ValueError("%s does not allow more than one label to be"
                                 " selected" % self)
            if self.all_label_slug in slugs:
                raise ValueError("You cannot select 'all' at the same time as"
                                 " another facet")


        if not slugs == [self.all_label_slug] and not self.hide_all:
            self._label_dict[self.all_label_slug].is_selected = False

        if not self.select_multiple or slugs == [self.all_label_slug]:
            # clear other selections
            for v in self._label_dict:
                self._label_dict[v].is_selected = False

        # make the selection
        for v in slugs:
            try:
                self._label_dict[v].is_selected = True
            except KeyError:
                pass

    def _select_default(self):
        """
        select the default values (usually all_label - set in init).

        Don't call directly, call via clear_selection.
        """
        for k in self.default_selected_slugs:
            try:
                self._label_dict[k].is_selected = True
            except KeyError:
                pass

    def unselect_slugs(self, *slugs):
        """
        Mark label(s) of this facet as not being selected.
        """

        if slugs == [self.all_label_slug]:
            raise ValueError("You cannot unselect 'all'. Select another facet"
                             " instead.")

         # make the unselection
        for v in slugs:
            self._label_dict[v].is_selected = False

        # if nothing is selected, select default, or 'all'
        if len(self.selected()) == 0:
            self._select_default()

    def clear_selection(self):
        for v in self._label_dict:
            self._label_dict[v].is_selected = False
        self._select_default()

    def selected(self):
        return filter(lambda x: x.is_selected, self._label_dict.values())


class FacetGroup(object):
    """
    A Facetgroup is the whole set of facets on a collection that interact.
    """

    app_label = None

    def __init__(self):
        self._matching_items = None
        self.facets = SortedDict()
        self.declare_facets()
        if self.app_label is None:
            model_module = sys.modules[self.__class__.__module__]
            self.app_label = model_module.__name__.split('.')[-2]

    def declare_facets(self):
        raise NotImplemented("FacetGroup subclasses should implement "
                             "declare_facets")

    @property
    def facet_list(self):
        return self.facets.values()

    @property #shame it can't be a property
    def key(self):
        return "%s__%s" % (self.app_label, get_verbose_name(self.__class__.__name__))

    def __getattr__(self, item):
        try:
            return self.facets[item]
        except KeyError:
            raise AttributeError(
                "%s object has no attribute '%s' - it is not the name of a facet either." \
                    % (self.__class__.__name__, item))

    def rebuild_index(self):
        """
        Bulk update to rebuild index
        1. erase old index
        2. iterate through unfiltered_collection
            add it to 'all' for each defined facet
            call get_FOO_facet for each defined facet
            update facet labels with the result
        3. save facet labels to the index
        4. update facets
        """
        self.clear_items()
        for item in self.unfiltered_collection():
            self.index_item(item, inhibit_save=True)
        for facet in self.facet_list:
            facet.save()
        self.update()

    def clear_items(self):
        """
        Subclasses that implement storage may wish to purge the storage to
        avoid orphans.
        """
        for facet in self.facet_list:
            facet.clear_items()

    def index_item(self, item, inhibit_save=False):
        for facet in self.facet_list:
            facet.index_item(item, inhibit_save)

    def unindex_item(self, item, inhibit_save=False):
        for facet in self.facet_list:
            facet.unindex_item(item, inhibit_save)

    def matching_items(self, ignore=[]):
        """
        Take the intersection of the items that match each facet.
        """
        if ignore == []:
            if self._matching_items is not None:
                return self._matching_items

        mi = None
        for facet in self.facet_list:
            if facet not in ignore:
                fmi = facet.matching_items()
                if fmi:
                    if mi is None:
                        mi = fmi.copy() #don't want to overwrite this when we &= to it.
                    else:
                        mi &= fmi

        if ignore == []:
            self._matching_items = mi

        return mi

    def invalidate(self):
        self._matching_items = None
        for facet in self.facet_list:
            facet.invalidate()

    def update(self):
        """
        Invalidate the _matching_items cache
        Update the sort of facet labels to reflect the current selection.
        """
        self.invalidate()
        for facet in self.facet_list:
            facet.sort()

    def clear_selection(self):
        """
        Unselect all facets
        """
        for facet in self.facet_list:
            facet.clear_selection()

    def apply_request(self, request):
        # Parse a request to select the facets within it.
        self.clear_selection()
        get = request.GET
        for facet in self.facet_list:
            vals = get.getlist(facet.slug)
            if vals:
                facet.select_slugs(*vals)
