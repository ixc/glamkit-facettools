from unittest import TestCase

from facettools.lib import (FacetValue, Facet, FacetGroup,
        InvalidObject, IncorrectUsage)


class LibTests(TestCase):

    def setUp(self):
        disjoint_facet_values = [
            FacetValue('big', ['mountain', 'planet']),
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
            group.select_values('not_a_facet', 'red')
        with self.assertRaises(IncorrectUsage):
            group.select_values('colours', 'not_a_colour')
        # Selecting a facet value ID limits matching items, not overall items
        group.select_values('colours', 'red')
        self.assertEqual([('colours', 'red')], group.selected_items)
        self.assertEqual(
            set(['red pants', 'red and blue shirt', 'rainbow',
                 'mountain', 'planet', 'ant', 'microbe',
                 'person', 'pink elephant']),
            group.matching_items)
        self.assertEqual(19, len(group.items))
        # Cannot select multiple values within a facet by default
        with self.assertRaises(IncorrectUsage):
            group.select_values('colours', 'pink')
        self.colours_facet.is_multi_select = True  # Permit multi-select
        self.colours_facet.select_values('pink')
        # But we can select a value in another facet within the group
        group.select_values('sizes', 'small')
        with self.assertRaises(IncorrectUsage):
            # Again, cannot select multiple values in second facet
            group.select_values('sizes', 'small')
        self.assertEqual(
            [('colours', 'red'), ('colours', 'pink'), ('sizes', 'small')],
            group.selected_items)
        # By default, selection across multiple facets produces a union
        self.assertEqual(
            # rainbow from colours facet (red + pink) + small from sizes facet
            set(['rainbow', 'ant', 'microbe']),
            group.matching_items)
        # Check facet value counts -- selected and filtered facet
        self.assertEqual(1,
            len(group.facet_value_by_id('colours', 'pink').matching_items))
        self.assertEqual(3,
            len(group.facet_value_by_id('colours', 'pink').items))
        # Check facet value counts -- unselected and filtered facet
        self.assertEqual(0,
            len(group.facet_value_by_id('sizes', 'big').matching_items))
        self.assertEqual(2,
            len(group.facet_value_by_id('sizes', 'big').items))
        # Perform intersection instead of default union across facets
        group.is_union_over_facets = False
        self.assertEqual(set(), group.matching_items)
        # Clear selected values
        group.clear_selection()
        self.assertEqual(19, len(group.items))
        # Only one match now, because we're doing an intersection over facets
        self.assertEqual(set(['pink elephant']), group.matching_items)
        # More explicit select_all method is also available
        group.select_all()
        self.assertEqual(19, len(group.items))
        self.assertEqual(set(['pink elephant']), group.matching_items)
