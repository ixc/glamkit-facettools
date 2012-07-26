

class InvalidObject(ValueError):
    pass


class IncorrectUsage(ValueError):
    pass


class FacetValue(object):

    def __init__(self, id, items=None, name=None, facet=None):
        self.is_selected = False
        self.items = set()
        self._facet = None

        self.id = id
        if isinstance(items, set):
            self.items = items
        elif items:
            self.items = set(items)
        if name is None:
            name = id
        if facet:
            self.set_facet(facet)
        self.name = name

    def set_facet(self, facet, _from_facet=False):
        self._facet = facet
        # Avoid infinite regress when parent facet is adding this object
        if not _from_facet:
            facet.add_value(self)

    @property
    def my_facet(self):
        return self._facet

    @property
    def my_group(self):
        if self.my_facet:
            return self.my_facet.my_group
        return None

    def add_items(self, items):
        if isinstance(items, (set, list, tuple)):
            self.items.update(items)
        else:
            # Assume we have a single item
            self.items.add(items)

    @property
    def matching_items(self):
        if not self.my_facet:
            raise InvalidObject(
                "Cannot generate matching items from %s that is not "
                "associated with a %s" % (self, Facet))
        if not self.my_group:
            return self.items
        else:
            if self.my_group.is_union_over_facets:
                return self.items & self.my_facet.matching_items  # intersection
            else:
                return self.items & self.my_group.matching_items  # intersection

    @property
    def available_items(self):
        if self.is_selected:
            return self.matching_items
        else:
            if self.my_facet.is_union_within_facet:
                if self.my_group.is_union_over_facets:
                    return self.items
                else:
                    # Intersection of my items with matching items in
                    # other facets I don't belong to.
                    availables = set(self.items)  # Defensive copy
                    for facet in self.my_group.facets:
                        if facet != self.my_facet:
                            availables &= facet.matching_items
                    return availables
            else:
                if self.my_group.is_union_over_facets:
                    return self.items & self.my_facet.matching_items
                else:
                    return self.items & self.my_group.matching_items

    def __eq__(self, other):
        if not isinstance(other, FacetValue):
            return False
        return (self.id == other.id
            and self.my_facet == other.my_facet)

    def __unicode__(self):
        return u"%s %s - %s: %s (%s/%s)" % (
            self.__class__.__name__, repr(self.id), self.name, self.items,
            len(self.count_matching_items), len(self.items))


class Facet(object):

    def __init__(self, id, name=None, values=None,
            is_multi_select=False, is_union_within_facet=False):
        # Init internal variables
        self._group = None
        self._values = {}
        self._value_ids_ordered = []
        self._selected_items = set()
        # Init from provided params
        self.id = id
        if name is None:
            name = id
        self.name = name
        self.is_multi_select = is_multi_select
        self.is_union_within_facet = is_union_within_facet
        if values:
            for facet_value in values:
                self.add_value(facet_value)

    def set_group(self, group, _from_group=False):
        self._group = group
        # Avoid infinite regress when parent group is adding this object
        if not _from_group:
            group.add_facet(self)

    @property
    def my_group(self):
        return self._group

    @property
    def values(self):
        return [self._values[value_id] for value_id in self._value_ids_ordered]

    def value_by_id(self, value_id):
        if not value_id in self._values:
            raise IncorrectUsage("No facet value with ID %s in values %s"
                % (repr(value_id), self._values.keys()))
        return self._values[value_id]

    def add_value(self, facet_value):
        # TODO Check for duplicate value
        self._values[facet_value.id] = facet_value
        self._value_ids_ordered.append(facet_value.id)
        facet_value.set_facet(self, _from_facet=True)  # Reverse-relate

    @property
    def is_all_selected(self):
        for facet_value in self.values:
            if facet_value.is_selected:
                return False
        return True

    def select_values(self, value_id_list):
        if not isinstance(value_id_list, list):
            value_id_list = [value_id_list]
        for value_id in value_id_list:
            if not value_id in self._values:
                raise IncorrectUsage(
                    "FacetValue with ID {0} is not defined".format(
                    repr(value_id)))
            if self._selected_items:
                # Selecting more than one value
                if not self.is_multi_select:
                    raise IncorrectUsage(
                        "Cannot select multiple facet values for %s" % self)
            facet_value = self._values[value_id]
            facet_value.is_selected = True
            self._selected_items.add(value_id)

    def clear_selection(self):
        for facet_value in self.values:
            facet_value.is_selected = False
        self._selected_items.clear()

    select_all = clear_selection  # Alias

    @property
    def selected_items(self):
        selected_items = []
        for facet_value in self.values:
            if facet_value.is_selected:
                selected_items.append((self.id, facet_value.id))
        return selected_items

    @property
    def items(self):
        items = set()
        for facet_value in self.values:
            items.update(facet_value.items)
        return items

    @property
    def available_items(self):
        availables = set()
        for facet_value in self.values:
            availables |= facet_value.available_items
        return availables

    # TODO Pre-calculate
    @property
    def matching_items(self):
        if self.is_all_selected:
            return self.items
        matching_in_facet = None
        for facet_value in self.values:
            if facet_value.is_selected:
                if matching_in_facet is None:
                    matching_in_facet = set(facet_value.items)  # Defensive copy
                else:
                    # Handle multiple selected values in facet
                    if self.is_union_within_facet:
                        matching_in_facet |= facet_value.items  # union
                    else:
                        matching_in_facet &= facet_value.items  # intersection
        if matching_in_facet is None:
            return set()
        else:
            return matching_in_facet

    def __eq__(self, other):
        if not isinstance(other, Facet):
            return False
        return self.id == other.id

    def __unicode__(self):
        return u"%s %s - %s (%s/%s)" % (
            self.__class__.__name__, repr(self.id), self.name,
            len(self.matching_items), len(self.items))


class FacetGroup(object):
    DEFAULT_GROUP_ID = 'DEFAULT'

    def __init__(self, facet_list=None, is_union_over_facets=True):
        """
        :param:facet_list:
            List of dictionaries containing at least the named values:
              id - unique facet identifier
            Optional named values are:
              items - set of unique items that belong to the facet
              group_id - identify the facet grouping the facet belongs to
              name -
        """
        self._facets = {}
        self._facet_ids_ordered = []
        if facet_list:
            for facet in facet_list:
                self.add_facet(facet)
        self.is_union_over_facets = is_union_over_facets

    def add_facet(self, facet):
        self._facets[facet.id] = facet
        self._facet_ids_ordered.append(facet.id)
        facet.set_group(self, _from_group=True)

    @property
    def facets(self):
        return [self._facets[facet_id] for facet_id in self._facet_ids_ordered]

    def facet_by_id(self, facet_id):
        if not facet_id in self._facets:
            raise IncorrectUsage("No facet with ID %s in facets %s"
                % (repr(facet_id), self._facets.keys()))
        return self._facets[facet_id]

    def facet_value_by_id(self, facet_id, value_id):
        return self.facet_by_id(facet_id).value_by_id(value_id)

    def select_values(self, facet_and_value_ids_list):
        for facet_id, value_id in facet_and_value_ids_list:
            self.select_value(facet_id, value_id)

    def select_value(self, facet_id, value_ids):
        facet = self.facet_by_id(facet_id)
        facet.select_values(value_ids)

    def clear_selection(self):
        for facet in self.facets:
            facet.clear_selection()

    select_all = clear_selection  # Alias

    @property
    def selected_items(self):
        selected_items = []
        for facet in self.facets:
            for selected_item in facet.selected_items:
                selected_items.append(selected_item)
        return selected_items

    @property
    def items(self):
        items = set()
        for facet in self.facets:
            items.update(facet.items)
        return items

    # TODO Generate and cache data on change, not on call
    @property
    def matching_items(self):
        matching_in_group = None
        for facet in self.facets:
            items_in_group = facet.matching_items
            if items_in_group:
                if matching_in_group is None:
                    matching_in_group = set(items_in_group)  # Defensive copy
                else:
                    # Handle selected facets over multiple groups
                    if self.is_union_over_facets:
                        matching_in_group |= items_in_group  # union
                    else:
                        matching_in_group &= items_in_group  # intersection
        if matching_in_group is None:
            return set()
        else:
            return matching_in_group

    @property
    def available_items(self):
        availables = set()
        for facet in self.facets:
            availables |= facet.available_items
        return availables
