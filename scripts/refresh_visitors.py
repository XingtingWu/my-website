"""Export country-level visit totals from the site's public MapMyVisitors table.

Only aggregate country names and counts are retained. Raw visits, addresses,
coordinates and device details never enter the published JSON.
"""
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
import argparse
import json
import re

SOURCE = 'https://mapmyvisitors.com/web/1c8cg'


class Countries(HTMLParser):
    def __init__(self):
        super().__init__()
        self.countries = []
        self.cells = []
        self.cell = None
        self.code = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr':
            self.cells, self.cell, self.code = [], None, None
        elif tag == 'td':
            self.cell = []
        elif tag == 'span' and self.cell is not None:
            match = re.fullmatch(r'flag ([a-z]{2})', attrs.get('class', ''))
            if match:
                self.code = match[1].upper()

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == 'td' and self.cell is not None:
            self.cells.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        elif tag == 'tr' and self.code and len(self.cells) >= 4:
            name, visits = self.cells[0], self.cells[2].replace(',', '')
            if not name or len(name) > 80 or not visits.isdigit():
                raise ValueError('Unexpected country row; preserving the previous data.')
            self.countries.append({'code': self.code, 'name': name, 'visits': int(visits)})
            self.cells, self.code = [], None


def parse_countries(html):
    parser = Countries()
    table = next((body for body in re.findall(r'<table\b[^>]*>(.*?)</table>', html, re.S)
                  if re.search(r'<th\b[^>]*>\s*Country\s*</th>', body)), None)
    if not table:
        raise ValueError('Missing country table; preserving the previous data.')
    parser.feed(table)
    rows = parser.countries
    if not rows or len({r['code'] for r in rows}) != len(rows):
        raise ValueError('Missing or duplicate countries; preserving the previous data.')
    start = re.search(r'var start = "(\d{2}/\d{2}/\d{4})"', html)
    end = re.search(r'var end = "(\d{2}/\d{2}/\d{4})"', html)
    if not start or not end:
        raise ValueError('Missing reporting period; preserving the previous data.')
    return {
        'schema_version': 1,
        'source': SOURCE,
        'updated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'period_start': datetime.strptime(start[1], '%m/%d/%Y').date().isoformat(),
        'period_end': datetime.strptime(end[1], '%m/%d/%Y').date().isoformat(),
        'countries': sorted(rows, key=lambda r: (-r['visits'], r['name'])),
    }


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'data/visitors.json')
    options = args.parse_args()
    request = Request(SOURCE, headers={'User-Agent': 'Mozilla/5.0 (compatible; XingtingWebsite/1.0)'})
    with urlopen(request, timeout=30) as response:
        data = parse_countries(response.read().decode('utf-8'))
    options.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = options.output.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(options.output)
    print(f'Updated {len(data["countries"])} country-level totals; no individual visitor records exported.')


if __name__ == '__main__':
    main()
