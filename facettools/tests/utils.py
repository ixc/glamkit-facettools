def check_counts(tc, facet, mapping):
    # check the list is complete
    tc.assertEqual(set([x.name for x in facet.labels]),
                   set([x[0] for x in mapping]))

    i = 0
    for label, count, is_selected in mapping:
        fv = facet.labels[i]
        try:
            tc.assertEqual(fv.name, label)
            tc.assertEqual(fv.count, count)
            tc.assertEqual(fv.is_selected, is_selected)
        except AssertionError, e:
            print "\ntest says ('%s', %s, %s)" % (label, count,
                                                  is_selected)
            print "code says ('%s', %s, %s)" % (fv.name, fv.count,
                                                fv.is_selected)
            raise e
        i += 1
