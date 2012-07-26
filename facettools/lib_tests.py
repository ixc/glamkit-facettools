from unittest import TestCase

from facettools.lib import (FacetValue, Facet, FacetGroup,
        InvalidObject, IncorrectUsage)


class LibTests(TestCase):

    def setUp(self):
        disjoint_facet_values = [
            FacetValue('big', ['mountain', 'planet', 'rainbow']),
            FacetValue('small', ['ant', 'microbe']),
            FacetValue('middling', ['person', 'pink elephant']),
            ]
        self.sizes_facet = Facet(
            'sizes', name='different sizes',
            values=disjoint_facet_values)
        overlapping_facet_values = [
            FacetValue('red', ['red pants', 'red and blue shirt', 'rainbow']),
            FacetValue('yellow', ['yellow pants', 'yellow duck', 'rainbow']),
            FacetValue('pink', ['pink pants', 'pink elephant', 'rainbow']),
            FacetValue('blue', ['blue pants', 'red and blue shirt', 'rainbow']),
            FacetValue('purple', ['purple pants', 'purple patch', 'rainbow']),
            FacetValue('orange', ['orange pants', 'rhyming orange', 'rainbow']),
            FacetValue('green', ['green pants', 'green with envy', 'rainbow']),
            ]
        self.colours_facet = Facet(
            'colours', name='overlapping colours',
            values=overlapping_facet_values)

    def test_FacetValue(self):
        self.assertRaises(TypeError, FacetValue)  # id required
        fv = FacetValue('id')  # Single arg is sufficient
        self.assertEqual('id', fv.id)
        self.assertEqual('id', fv.name)  # Name defaults to id
        self.assertEqual(set(), fv.items)  # No items by default
        # Add some items
        fv.add_items(['one', 2, 'Three'])
        fv.add_items('another')  # Individual item
        self.assertEqual(4, len(fv.items))
        # Useful exception if FacetValue isn't hooked up to a Facet
        with self.assertRaises(InvalidObject):
            fv.matching_items
        # Hook up correctly
        facet = Facet('facet_id')
        fv.set_facet(facet)
        # All items match by default (selection always restricts matches)
        self.assertEqual(fv.items, fv.matching_items)
        # Select this facet value
        facet.select_values(fv.id)
        self.assertEqual(fv.items, fv.matching_items)
        # Equality is based on id and parent facet
        self.assertEqual(FacetValue('id1'), FacetValue('id1'))
        self.assertEqual(
            FacetValue('id1', facet=facet),
            FacetValue('id1', facet=facet))
        self.assertNotEqual(
            FacetValue('id1'),  # facet defaults to None
            FacetValue('id1', facet=facet))
        self.assertNotEqual(
            FacetValue('id1', facet=facet),
            FacetValue('id2', facet=facet))

    def test_matching_on_single_facet(self):
        # 21 items provided, but item IDs overlap
        self.assertEqual(14, len(self.colours_facet.items))
        # Selecting a facet value ID limits matching items, not overall items
        self.colours_facet.select_values('red')
        self.assertEqual([('colours', 'red')],
            self.colours_facet.selected_items)
        self.assertEqual(3, len(self.colours_facet.matching_items))
        self.assertEqual(
            set(['red pants', 'red and blue shirt', 'rainbow']),
            self.colours_facet.matching_items)
        self.assertEqual(14, len(self.colours_facet.items))
        # Cannot select multiple facet values by default
        self.assertRaises(Exception, self.colours_facet.select_values, ['pink'])
        self.colours_facet.is_multi_select = True  # Permit next test
        # Facet value ID selection is cumulative; intersection by default
        self.colours_facet.select_values('pink')
        self.assertEqual(
            [('colours', 'red'), ('colours', 'pink')],
            self.colours_facet.selected_items)
        self.assertEqual(set(['rainbow']), self.colours_facet.matching_items)
        # Perform facet union instead of default intersection
        self.colours_facet.is_union_within_facet = True
        self.assertEqual(
            set(['red pants', 'red and blue shirt',
                 'rainbow', 'pink pants', 'pink elephant']),
            self.colours_facet.matching_items)
        # Clear selected values, in effect selects all
        self.colours_facet.clear_selection()
        self.assertEqual(14, len(self.colours_facet.items))
        self.assertEqual(14, len(self.colours_facet.matching_items))
        # More explicit select_all method is also available
        self.colours_facet.select_all()
        self.assertEqual(14, len(self.colours_facet.items))
        self.assertEqual(14, len(self.colours_facet.matching_items))

    def test_matching_on_group_with_multiple_facet(self):
        group = FacetGroup(facet_list=[
            self.colours_facet,
            self.sizes_facet])
        # 14 unique from overlapping, 6 unique from disjoint, less 1 shared
        self.assertEqual(19, len(group.items))
        # Cannot select unknown facet or value IDs
        with self.assertRaises(IncorrectUsage):
            group.select_value('not_a_facet', 'red')
        with self.assertRaises(IncorrectUsage):
            group.select_value('colours', 'not_a_colour')
        # Selecting a facet value ID limits matching items, not overall items
        group.select_value('colours', 'red')
        self.assertEqual([('colours', 'red')], group.selected_items)
        self.assertEqual(
            set(['red pants', 'red and blue shirt', 'rainbow',
                 'mountain', 'planet', 'ant', 'microbe',
                 'person', 'pink elephant']),
            group.matching_items)
        self.assertEqual(19, len(group.items))
        # Cannot select multiple values within a facet by default
        with self.assertRaises(IncorrectUsage):
            group.select_value('colours', 'pink')
        self.colours_facet.is_multi_select = True  # Permit multi-select
        self.colours_facet.select_values('pink')
        # But we can select a value in another facet within the group
        group.select_value('sizes', 'small')
        with self.assertRaises(IncorrectUsage):
            # Again, cannot select multiple values in second facet
            group.select_value('sizes', 'small')
        self.assertEqual(
            [('colours', 'red'), ('colours', 'pink'), ('sizes', 'small')],
            group.selected_items)
        # By default, selection across multiple facets produces a union
        self.assertEqual(
            # rainbow from colours facet (red + pink) + small from sizes facet
            set(['rainbow', 'ant', 'microbe']),
            group.matching_items)
        # Perform intersection instead of default union across facets
        group.is_union_over_facets = False
        self.assertEqual(set(), group.matching_items)
        # Clear selected values
        group.clear_selection()
        self.assertEqual(19, len(group.items))
        # Only two matches now, because we're doing an intersection over facets
        self.assertEqual(
            set(['pink elephant', 'rainbow']),
            group.matching_items)
        # More explicit select_all method is also available
        group.select_all()
        self.assertEqual(19, len(group.items))
        self.assertEqual(
            set(['pink elephant', 'rainbow']),
            group.matching_items)


    def test_facet_value_counts(self):
        group = FacetGroup(facet_list=[
            self.colours_facet,
            self.sizes_facet])
        facetvalue_colours_pink = group.facet_value_by_id('colours', 'pink')
        facetvalue_colours_red = group.facet_value_by_id('colours', 'red')
        facetvalue_colours_blue = group.facet_value_by_id('colours', 'blue')
        facetvalue_colours_orange = group.facet_value_by_id('colours', 'orange')
        facetvalue_sizes_big = group.facet_value_by_id('sizes', 'big')
        facetvalue_sizes_middling = group.facet_value_by_id('sizes', 'middling')
        facetvalue_sizes_small = group.facet_value_by_id('sizes', 'small')
        # Before any selection, all items are both matching and available
        self.assertEqual(19, len(group.items))
        self.assertEqual(19, len(group.matching_items))
        self.assertEqual(
            set(['pink pants', 'pink elephant', 'rainbow']),
            facetvalue_colours_pink.matching_items)
        self.assertEqual(
            set(['red pants', 'red and blue shirt', 'rainbow']),
            facetvalue_colours_red.matching_items)
        self.assertEqual(
            set(['mountain', 'planet', 'rainbow']),
            facetvalue_sizes_big.matching_items)
        self.assertEqual(
            set(['ant', 'microbe']),
            facetvalue_sizes_small.matching_items)

        # Test: Group union + Facets union
        group.select_value('colours', 'red')
        group.select_value('sizes', 'big')
        group.is_union_over_facets = True
        self.colours_facet.is_union_within_facet = True
        self.sizes_facet.is_union_within_facet = True
        self.assertEqual(
            set(['red pants', 'red and blue shirt', 'rainbow',
                 'mountain', 'planet']),
            group.matching_items)
        #       Matching => All items in all selected facet values
        #       available => All items in all facet values
        self.assertEqual(  # 'rainbow' is also in red facet value
            set(['rainbow']),
            facetvalue_colours_pink.matching_items)
        self.assertEqual(  # all items are available
            set(['pink pants', 'pink elephant', 'rainbow']),
            facetvalue_colours_pink.available_items)
        self.assertEqual(  # all red facet value items
            set(['red pants', 'red and blue shirt', 'rainbow']),
            facetvalue_colours_red.matching_items)
        self.assertEqual(  # all items are available
            set(['red pants', 'red and blue shirt', 'rainbow']),
            facetvalue_colours_red.available_items)
        self.assertEqual(  # all big items also match
            set(['mountain', 'planet', 'rainbow']),
            facetvalue_sizes_big.matching_items)
        self.assertEqual(  # all items are available
            set(['mountain', 'planet', 'rainbow']),
            facetvalue_sizes_big.available_items)
        self.assertEqual(  # no small items match, no shared items with big
            set(),
            facetvalue_sizes_small.matching_items)
        self.assertEqual(  # all items are available
            set(['ant', 'microbe']),
            facetvalue_sizes_small.available_items)

        # Test: Group union + Facets intersection
        group.is_union_over_facets = True
        self.colours_facet.is_union_within_facet = False
        self.colours_facet.is_multi_select = True
        self.sizes_facet.is_union_within_facet = False
        group.clear_selection()
        group.select_value('colours', 'red')
        group.select_value('colours', 'blue')
        group.select_value('sizes', 'big')
        self.assertEqual(
            set(['red and blue shirt', 'rainbow',
                 'mountain', 'planet']),
            group.matching_items)
        #       Matching => items in selected intersecting all facet values
        #       available => items in parent facet's matching items
        self.assertEqual(  # 'rainbow' is also in red facet value
            set(['red and blue shirt', 'rainbow']),
            facetvalue_colours_blue.matching_items)
        self.assertEqual(  # candidate items must be in facet's matching items
            set(['rainbow']),
            facetvalue_colours_pink.available_items)
        self.assertEqual(  # all red facet value items
            set(['red and blue shirt', 'rainbow']),
            facetvalue_colours_red.matching_items)
        self.assertEqual(  # candidate items must be in facet's matching items
            set(['red and blue shirt', 'rainbow']),  # even when selected
            facetvalue_colours_red.available_items)
        self.assertEqual(  # all big items also match
            set(['mountain', 'planet', 'rainbow']),
            facetvalue_sizes_big.matching_items)
        self.assertEqual(  # items in sole selected facet value are available
            set(['mountain', 'planet', 'rainbow']),
            facetvalue_sizes_big.available_items)
        self.assertEqual(  # no small items match, no shared items with big
            set(),
            facetvalue_sizes_small.matching_items)
        self.assertEqual(  # no small items are available, no overlap with big
            set(),
            facetvalue_sizes_small.available_items)

        # Test: Group intersection + Facets union
        group.is_union_over_facets = False
        self.colours_facet.is_union_within_facet = True
        self.colours_facet.is_multi_select = True
        self.sizes_facet.is_union_within_facet = True
        group.clear_selection()
        group.select_value('colours', 'orange')
        group.select_value('colours', 'pink')
        group.select_value('sizes', 'middling')
        self.assertEqual(  # only one intersection across facets
            set(['pink elephant']),
            group.matching_items)
        #       Matching => items in selected intersecting all facet values
        #       available => items in parent group's matching items
        self.assertEqual(  # no orange items are also middling
            set(),
            facetvalue_colours_orange.matching_items)
        self.assertEqual(  # available must overlap with matching sizes
            set(),
            facetvalue_colours_red.available_items)
        self.assertEqual(  # only elephant overlaps colours and sizes facets
            set(['pink elephant']),
            facetvalue_colours_pink.matching_items)
        self.assertEqual(  # no additional available even though selected
            set(['pink elephant']),
            facetvalue_colours_pink.available_items)
        self.assertEqual(  # only elephant overlaps colours and sizes facets
            set(['pink elephant']),
            facetvalue_sizes_middling.matching_items)
        self.assertEqual(  # available must overlap with matching colours
            set(['pink elephant']),
            facetvalue_sizes_middling.available_items)
        self.assertEqual(  # no small items match, no overlap with colours
            set(),
            facetvalue_sizes_small.matching_items)
        self.assertEqual(  # no small item available, no overlap with colours
            set(),
            facetvalue_sizes_small.available_items)

        # Test: Group intersection + Facets intersection
        group.is_union_over_facets = False
        self.colours_facet.is_union_within_facet = False
        self.colours_facet.is_multi_select = True
        self.sizes_facet.is_union_within_facet = False
        group.clear_selection()
        # Start with only single selection in each facet
        group.select_value('colours', 'pink')
        group.select_value('sizes', 'middling')
        self.assertEqual(  # only one intersection across facets
            set(['pink elephant']),
            group.matching_items)
        #       Matching => items in selected intersecting all group matching
        #       available => items in parent facet's and group's matching items
        self.assertEqual(  # no orange items are also middling
            set(),
            facetvalue_colours_orange.matching_items)
        self.assertEqual(  # available must overlap with matching sizes
            set(),
            facetvalue_colours_red.available_items)
        self.assertEqual(  # only elephant overlaps colours and sizes facets
            set(['pink elephant']),
            facetvalue_colours_pink.matching_items)
        self.assertEqual(  # no additional available even though selected
            set(['pink elephant']),
            facetvalue_colours_pink.available_items)
        self.assertEqual(  # only elephant overlaps colours and sizes facets
            set(['pink elephant']),
            facetvalue_sizes_middling.matching_items)
        self.assertEqual(  # available must overlap with matching colours
            set(['pink elephant']),
            facetvalue_sizes_middling.available_items)
        self.assertEqual(  # no small items match, no overlap with colours
            set(),
            facetvalue_sizes_small.matching_items)
        self.assertEqual(  # no small item available, no overlap with colours
            set(),
            facetvalue_sizes_small.available_items)
        # Now with multiple in-facet colours selection: pink + red
        group.select_value('colours', 'red')
        self.assertEqual(  # no intersection across facets and groups
            set(),
            group.available_items)
        # Now with multiple in-facet sizes selection:
        group.clear_selection()
        group.select_value('sizes', 'big')
        group.select_values([
            ('colours', 'red'), ('colours', 'blue')])
        self.assertEqual(  # just one intersection across all facets in group
            set(['rainbow']),
            group.available_items)
