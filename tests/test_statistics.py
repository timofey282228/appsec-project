from appsec_project.statutils import significant


def test_significant():
    assert [1,1,1,1] == significant([1, 2, 1, 1, 1])
