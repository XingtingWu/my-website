"""Guard the country-only export against changes in the upstream HTML."""
import unittest
from refresh_visitors import parse_countries


def fixture(rows):
    return '''<table><tr><td><span class="flag au"></span>
        An individual visit that must not be exported</td><td>1</td></tr></table>
        <table class="audience"><tr><th>Country</th><th>Locations</th>
        <th>Visits</th><th>Uniques</th></tr>''' + rows + '''</table>
        <script>var start = "01/01/2026"; var end = "12/31/2026";</script>'''


AU = '''<tr><td><span class="flag au"></span><span class="vstor">Australia</span></td>
<td></td><td>1,234</td><td>12</td></tr>'''
CA = '''<tr><td><span class="flag ca"></span><span class="vstor">Canada</span></td>
<td>2 Locations</td><td>4</td><td>3</td></tr>'''


class CountryExportTests(unittest.TestCase):
    def test_exports_aggregate_visits_not_unique_people_or_individual_rows(self):
        result = parse_countries(fixture(AU + CA))
        self.assertEqual(result['countries'], [
            {'code': 'AU', 'name': 'Australia', 'visits': 1234},
            {'code': 'CA', 'name': 'Canada', 'visits': 4},
        ])
        self.assertEqual(result['period_start'], '2026-01-01')
        self.assertEqual(result['period_end'], '2026-12-31')

    def test_does_not_export_city_details_or_duplicate_malformed_closing_rows(self):
        city = '<tr><td></td><td>City detail</td><td>2</td><td>1</td></tr></tr>'
        self.assertEqual(len(parse_countries(fixture(AU + city + CA))['countries']), 2)

    def test_rejects_missing_or_invalid_data(self):
        for html in ['<html>Service unavailable</html>', fixture(''), fixture(AU + AU),
                     fixture(AU.replace('1,234', 'Unavailable')),
                     fixture(AU).replace('var start', 'var unexpected')]:
            with self.subTest(html=html), self.assertRaises(ValueError):
                parse_countries(html)


if __name__ == '__main__':
    unittest.main()
