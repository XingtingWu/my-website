"""Check local links, publication completeness, image metadata and public scope."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
import json, struct

ROOT=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
    def __init__(self,path):
        super().__init__(); self.ids=[]; self.urls=[]; self.h1=0; self.image_alts=[]; self.articles=0
        self.feed(path.read_text())
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if tag=='h1': self.h1+=1
        if tag=='article' and 'publication' in a.get('class','').split(): self.articles+=1
        if tag=='img' and a.get('src'): self.image_alts.append(a.get('alt'))
        for key in ['src','href']:
            if a.get(key): self.urls.append(a[key])

pages={p.name:Page(p) for p in ROOT.glob('*.html')}
errors=[]; checked=0
for filename,page in pages.items():
    if page.h1!=1: errors.append(f'{filename}: expected one h1, found {page.h1}')
    if len(set(page.ids))!=len(page.ids): errors.append(f'{filename}: duplicate IDs')
    if any(not alt for alt in page.image_alts): errors.append(f'{filename}: missing image description')
    for url in page.urls:
        parsed=urlparse(url)
        if parsed.scheme in ['http','https','mailto','tel']: continue
        if parsed.scheme or url.startswith('//'): errors.append(f'{filename}: unexpected URL {url}'); continue
        path=unquote(parsed.path)
        if path.startswith('/') or '..' in Path(path).parts: errors.append(f'{filename}: nonportable path {path}')
        target=ROOT/(path or filename)
        if not target.is_file(): errors.append(f'{filename}: missing {path}')
        if parsed.fragment and target.suffix=='.html':
            dest=pages.get(target.name)
            if not dest or parsed.fragment not in dest.ids: errors.append(f'{filename}: missing fragment {url}')
        checked+=1
source=json.loads((ROOT/'data/publications.json').read_text())['publications']
if len(source)!=18 or pages['publications.html'].articles!=len(source): errors.append('Publication count mismatch')
for paper in source:
    if 'pub-'+paper['id'] not in pages['publications.html'].ids: errors.append('Missing publication '+paper['id'])
assets=list((ROOT/'assets/images').glob('*.webp'))
for file in assets:
    data=file.read_bytes(); offset=12; chunks=[]
    while offset+8<=len(data):
        tag=data[offset:offset+4]; size=struct.unpack('<I',data[offset+4:offset+8])[0]
        chunks.append(tag); offset+=8+size+(size%2)
    if b'EXIF' in chunks or b'XMP ' in chunks: errors.append(f'{file.name}: private metadata chunk found')
for file in ROOT.rglob('*'):
    if not file.is_file() or '.git' in file.parts or file.name=='.DS_Store': continue
    if file.suffix.lower() in ['.pdf','.docx','.heic','.tropy','.m4a','.mp3']:
        errors.append(f'Unexpected source document in public tree: {file.relative_to(ROOT)}')
    if file.suffix in ['.html','.json','.css','.js']:
        text=file.read_text()
        if '/Users/' in text or 'PhD Xingting Shared Folder' in text: errors.append(f'Local source path in {file.name}')
if errors: raise SystemExit('\n'.join(errors))
print(f'PASS: {len(pages)} pages; {checked} local references; {len(source)} publications; {len(assets)} metadata-free WebP assets; no research source documents in the public tree.')
