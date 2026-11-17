"""Build a portable, dependency-free academic website from shared components.

Run: python3 scripts/build.py
All pages are complete HTML; JavaScript only enhances navigation and filtering.
"""
from pathlib import Path
from html import escape
import json, re, hashlib
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT/'data/publications.json').read_text())
PAPERS = DATA['publications']
UPDATED = date.fromisoformat(DATA['updated']).strftime('%-d %B %Y')
SCHOLAR = DATA['profile_url']
IMAGES = json.loads((ROOT/'data/images.json').read_text())
SERVICE = json.loads((ROOT/'data/academic-service.json').read_text())
PROFILE = json.loads((ROOT/'data/profile.json').read_text())
AUTHORSHIP = json.loads((ROOT/'data/authorship.json').read_text())['publications']
JOURNAL_METRICS = json.loads((ROOT/'data/journal-metrics.json').read_text())
VISITORS = json.loads((ROOT/'data/visitors.json').read_text())
COUNTRY_POSITIONS = json.loads((ROOT/'data/country-positions.json').read_text())
PUBLISHED = [p for p in PAPERS if p['type'] != 'preprint']
OUTDOOR_STORYBOOK = 'https://heyzine.com/flip-book/990e984dee.html'
ARROW = '<span class="arrow" aria-hidden="true">↗</span>'
pages = []

def asset_url(path):
    version = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()[:12]
    return f'{path}?v={version}'

def img(name, alt, cls='', eager=False, sizes=None):
    size=IMAGES[name+'.webp']
    loading='loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    responsive=''
    if name+'-small.webp' in IMAGES:
        variants=[f'assets/images/{name}-{suffix}.webp {IMAGES[name+"-"+suffix+".webp"][0]}w' for suffix in ['small','medium'] if name+'-'+suffix+'.webp' in IMAGES]
        variants.append(f'assets/images/{name}.webp {size[0]}w')
        sizes=sizes or '(max-width: 760px) calc(100vw - 40px), (max-width: 1050px) 65vw, 850px'
        responsive=f' srcset="{", ".join(variants)}" sizes="{sizes}"'
    return f'<img src="assets/images/{name}.webp"{responsive} alt="{escape(alt)}" width="{size[0]}" height="{size[1]}" class="{cls}" {loading} decoding="async">'

def figure(name, alt, caption, cls='', eager=False, sizes=None):
    sizes=sizes or ('(max-width: 760px) calc(100vw - 40px), (max-width: 1184px) calc(100vw - 64px), 1120px' if 'project-cover' in cls else None)
    plain_caption=re.sub(r'<[^>]+>','',caption)
    return f'<figure class="{cls}"><a class="zoom-link" href="assets/images/{name}.webp" data-image data-caption="{escape(plain_caption)}" aria-label="Enlarge image: {escape(alt)}">{img(name,alt,eager=eager,sizes=sizes)}</a><figcaption class="caption">{caption}</figcaption></figure>'

def photo_sequence(photos, layout='pair'):
    """A small, captioned sequence; every photograph also opens at full size."""
    return '<div class="photo-sequence '+layout+'">'+''.join(figure(*photo) for photo in photos)+'</div>'

def link(url, label, cls='text-link'):
    return f'<a class="{cls}" href="{escape(url)}">{label}</a>'

def eyebrow(text): return f'<span class="eyebrow">{text}</span>'

def academic_service():
    journals=[]
    for journal in SERVICE['journals']:
        m=journal['indicators']
        labels=[link(m.get('index_sources',{}).get(index,m.get('index_source',m['source'])),escape(index),'indicator-link') for index in m['indices']]
        if m.get('quartile'):
            label='JCR '+m['quartile']+(' (best)' if m.get('quartile_scope')=='best' else '')
            labels.append(link(m.get('quartile_source',m['source']),label,'indicator-link'))
        if m.get('jif'):
            labels.append(link(m['source'],f'IF {m["jif"]}','indicator-link'))
        journals.append(f'<li><span class="service-journal-name">{escape(journal["title"])}</span> <span class="service-journal-indicators">({" · ".join(labels)})</span></li>')
    return f'''<div class="service-journal-section" id="reviewer-journals" aria-labelledby="service-heading"><div class="service-journal-heading"><h3 id="service-heading">Journals I review for</h3><p>Journal indicators · 2025 data</p></div><ul class="service-journals">{''.join(journals)}</ul><p class="service-source">IF = Journal Impact Factor (2025, released in 2026). Best JCR quartiles are marked. Indicators link to their sources; indexing checked 17 November 2026.</p></div>'''

def conference_service():
    committees=[]
    reviewers=[]
    for conference in SERVICE['conferences']:
        venue=link(conference['url'],escape(conference['name']),'service-conference-link')
        roles=' &amp; '.join(escape(role) for role in conference['roles'])
        item=f'<li>{venue}<span class="service-conference-role">{roles}</span></li>'
        (committees if 'Program committee member' in conference['roles'] else reviewers).append(item)
    return f'''<div class="service-conference-section" id="conference-service" aria-labelledby="conference-service-heading"><h3 id="conference-service-heading">Conference service</h3><div class="service-conference-grid"><ul class="service-committee">{''.join(committees)}</ul><ul class="service-conference-reviewers">{''.join(reviewers)}</ul></div></div>'''

def home_service():
    checked=date.fromisoformat(SERVICE['updated']).strftime('%-d %B %Y')
    return f'''<section class="home-service" id="academic-service" aria-labelledby="home-service-heading"><div class="wrap"><div class="home-service-grid"><div class="home-service-intro"><h2 id="home-service-heading">Academic service</h2><p>Conference and journal service across HCI, education, ageing and related fields.</p>{link(SERVICE['orcid'],'View my ORCID record')}</div><a class="service-metric" href="#reviewer-journals"><span class="service-value">{SERVICE['record_count']}</span><span class="service-label">ORCID review records</span></a><a class="service-metric" href="#reviewer-journals"><span class="service-value">{len(SERVICE['journals'])}</span><span class="service-label">Journals reviewed for</span></a></div><p class="home-service-source">Based on public ORCID records · Updated {checked}</p>{conference_service()}{academic_service()}</div></section>'''

def writing_stats():
    first=sum(AUTHORSHIP[p['id']]['first_author'] for p in PUBLISHED)
    corresponding=sum(AUTHORSHIP[p['id']]['corresponding_author'] is True for p in PUBLISHED)
    incomplete=any(AUTHORSHIP[p['id']]['corresponding_author'] is None for p in PUBLISHED)
    journals=sum(p['type']=='journal' for p in PUBLISHED)
    conferences=sum(p['type']=='conference' for p in PUBLISHED)
    values=[(str(len(PUBLISHED)),'Published papers',f'{journals} journal articles · {conferences} conference contributions'),
            (str(first),'First-author papers','Within the published papers'),
            (str(corresponding)+('+' if incomplete else ''),'Corresponding-author papers','Confirmed in publisher records')]
    return '<div class="writing-stats" aria-label="Publication statistics">'+''.join(f'<a class="writing-metric" href="publications.html"><span class="writing-value">{value}</span><span class="writing-label">{label}</span><span class="writing-detail">{detail}</span></a>' for value,label,detail in values)+'</div><p class="writing-count-note">Updated 17 November 2026.</p>'

def paper_details(p, linked=True):
    parts=[]
    metrics=next((m for m in JOURNAL_METRICS['journals'].values() if p['id'] in m['match']),None)
    if metrics:
        labels=[(index,metrics.get('index_sources',{}).get(index,metrics['source'])) for index in metrics['indices']]
        if metrics.get('quartile'):
            labels.append(('JCR '+metrics['quartile']+(' (best quartile)' if metrics.get('quartile_scope')=='best' else ''),metrics.get('quartile_source',metrics['source'])))
        labels.append((f'JIF {metrics["jif"]} ({metrics["year"]})',metrics.get('jif_source',metrics['source'])))
        label=' · '.join(link(source,escape(text),'indicator-link') if linked else escape(text) for text,source in labels)
        parts.append(f'<span class="journal-metrics">{label}</span>')
    roles=AUTHORSHIP[p['id']]
    labels=[]
    if roles['first_author']: labels.append('First author')
    if roles['corresponding_author'] is True: labels.append('Corresponding author')
    if labels: parts.append('<span class="author-role">'+ ' &amp; '.join(labels)+'</span>')
    return '<div class="paper-details">'+''.join(parts)+'</div>' if parts else ''

def background():
    def rows(items):
        return ''.join(f'<li class="career-row"><span class="career-date">{escape(item["dates"])}</span><div><h4>{escape(item["title"])}</h4><p class="career-place">{escape(item["institution"])}</p><p class="career-detail">{escape(item["details"])}</p></div></li>' for item in items)
    volunteers=''.join(f'<article class="volunteer-entry"><span class="career-date">{escape(v["dates"])}</span><h4>{escape(v["title"])}</h4><p class="volunteer-organisation">{link(v["url"],escape(v["institution"]),"organisation-link")}</p><p class="volunteer-location">{escape(v["location"])}</p><p>{escape(v["details"])}</p></article>' for v in PROFILE['volunteering'])
    return f'''<section class="home-background home-section" id="background"><div class="wrap"><div class="home-section-head"><h2>Education &amp; experience</h2><p>From interaction design in industry to participatory research with older adults.</p></div><div class="background-grid"><div><h3>Education</h3><ol class="career-list">{rows(PROFILE['education'])}</ol></div><div><h3>Work experience</h3><ol class="career-list">{rows(PROFILE['experience'])}</ol></div></div><div class="volunteering" id="volunteering"><h3>Community &amp; volunteering</h3><div class="volunteer-grid">{volunteers}</div></div><section class="content-creation" id="content-creation" aria-labelledby="creation-heading"><div class="creation-heading"><h3 id="creation-heading">Content creation</h3><p>I share what I read, learn, and draw on Xiaohongshu.</p></div><div class="creation-grid"><article><h4>Research notes</h4><p class="creation-account"><span lang="zh">蜻蜓隊長的学习池</span> · Academy_Design</p><p>Reading notes and practical explanations of qualitative research, from coding and thematic analysis to focus groups and research questions. I also share reflections on academic writing and publishing.</p>{link('https://xhslink.com/m/1MBa8EERfhz','Read my research notes')}</article><article><h4>Art &amp; illustration</h4><p class="creation-account"><span lang="zh">蜻蜓隊長的作画池</span> · wuxingting</p><p>Digital illustrations, landscape sketches, and scenes from everyday life, alongside my Procreate practice and drawing lessons.</p>{link('https://xhslink.com/m/4sUuQcr9thK','Explore my artwork')}</article></div></section></div></section>'''

def research_interests():
    interests=['Design','Human–Computer Interaction','Older adults','AI and Education','Technology Adoption']
    return '<ul class="research-interests" aria-label="Research interests on Google Scholar">'+''.join('<li>'+escape(item)+'</li>' for item in interests)+'</ul>'

def research_landscape():
    """An accessible map of interests, with publication-backed method examples."""
    # The reusable SVG lives in assets; inline links resolve from the page root.
    diagram=(ROOT/'assets/research-landscape.svg').read_text().replace('href="../', 'href="')
    papers_by_id={p['id']:p for p in PAPERS}
    def paper_example(id, label):
        return link(papers_by_id[id]['paper_url'], label)
    methods=[
        ('ethnography','Ethnography','Learning through everyday participation.',
         'My doctoral research involves spending time with older adults and care staff in residential aged care. Through observation, conversations, field notes, and participation in shared activities, I explore how people, places, materials, and routines shape outdoor engagement.',
         link('gardening.html','Gardening in everyday life')+link('outdoor-stories.html#map-and-play','Walking with residents and staff')),
        ('participatory-design','Co-design & participatory design','Making and learning with people.',
         'I explore how residents and care staff can shape activities and materials through making, trying, and adapting them together. Research through Design connects this work with iterative prototyping and reflection: what we make, how it is used, and what this helps us understand.',
         link('crafting.html#iteration','Adapting materials through making')+link('outdoor-stories.html#design-materials','Design materials for a shared walk')),
        ('q-methodology','Q methodology','Making room for different viewpoints.',
         'I am interested in how people understand the same technology differently. My collaborative work uses Q methodology to explore art students’ perspectives on generative AI and creative identity, bringing patterns of viewpoints into focus.',
         paper_example('roLk4NBRz8UC','Art students, GenAI & creative identity')),
        ('mixed-methods','Qualitative & quantitative methods','Connecting experiences with patterns.',
         'I explore interviews and narrative inquiry alongside experiments and mixed-methods designs. My collaborative work also uses structural equation modelling (SEM), including PLS-SEM, and approaches such as fsQCA to examine relationships and patterns in learning, behaviour, and technology experiences.',
         paper_example('W7OEmFMy1HYC','AI teaching assistants: a mixed-methods study')+paper_example('qjMakFHDy7sC','Human–machine collaboration & driving')),
        ('reviews','Reviews','Bringing research into conversation.',
         'I am interested in scoping reviews, systematic literature reviews, and qualitative evidence synthesis, including meta-ethnography. Alongside these approaches, my published work uses bibliometric reviews to explore research trends, connections, and gaps in fields such as game design for older adults and generative AI in design.',
         paper_example('Tyk-4Ss8FVUC','Game design for older adults')+paper_example('3fE2CSJIrl8C','Generative AI in clothes design')),
    ]
    controls=''.join(f'<button type="button" id="method-tab-{id}" data-method="{id}">{name}</button>' for id,name,*_ in methods)
    panels=''.join(f'<section class="method-exploration" id="method-panel-{id}"><div><span class="eyebrow">{name}</span><h4>{title}</h4></div><div><p>{body}</p><div class="method-examples">{examples}</div></div></section>' for id,name,title,body,examples in methods)
    return f'''<section class="research-landscape section" id="research-interests" aria-labelledby="landscape-heading"><div class="wrap">
<div class="landscape-heading home-section-head"><h2 id="landscape-heading">Research interests &amp; methods</h2><p>I explore how design and technology can support participation, creativity, and learning, through my doctoral research and wider collaborations.</p></div>
<div class="landscape-overview"><div class="interest-list">
<article data-interest-copy="care"><div><h3><a data-interest="care" href="research.html">Ageing &amp; older adults</a></h3><p>My doctoral research explores shared making, gardening, and outdoor discovery with older adults and care staff.</p></div></article>
<article data-interest-copy="ai"><div><h3><a data-interest="ai" href="publications.html#pub-roLk4NBRz8UC">Human–AI interaction</a></h3><p>Exploring co-creation, social robots, and technology adoption: how people make sense of AI and find a place for it in their lives.</p></div></article>
<article data-interest-copy="learning"><div><h3><a data-interest="learning" href="publications.html#pub-W7OEmFMy1HYC">AI in education &amp; creativity</a></h3><p>Investigating AI-supported design education, creative identity, and learning across generations.</p></div></article>
</div><figure class="interest-diagram">{diagram}</figure></div>
<div class="methods-explorer" id="methods" data-methods-explorer><div class="methods-heading"><h3>Methods I explore</h3></div><div class="method-tabs" hidden>{controls}</div><div class="method-panels">{panels}</div></div>
</div></section>'''

def plant_journey():
    return '''<ol class="plant-journey" aria-label="From the garden to a shared story">
<li><span class="journey-number">01</span><div><h3>Choose a place.</h3><p>A familiar path, a flower bed, or somewhere to pause.</p></div></li>
<li><span class="journey-number">02</span><div><h3>Follow a plant.</h3><p>Look for a colour, notice a detail, or share what you recognise.</p></div></li>
<li><span class="journey-number">03</span><div><h3>Bring back a story.</h3><p>A photograph, a plant, or a few words become part of the shared display.</p></div></li>
</ol>'''

def head(kicker,title,lead='',actions=''):
    return f'<div class="page-head">{eyebrow(kicker)}<h1>{title}</h1>{f"<p class=lead>{lead}</p>" if lead else ""}{actions}</div>'

def visitor_locations():
    countries=VISITORS['countries']
    active=countries[0]
    pins=[]
    for c in countries:
        if c['code'] not in COUNTRY_POSITIONS: continue
        x,y=COUNTRY_POSITIONS[c['code']]
        label=escape(f'{c["name"]}: {c["visits"]:,} recorded visits')
        selected=c['code']==active['code']
        pins.append(f'<g class="visitor-pin{" is-active" if selected else ""}" transform="translate({x} {y})" data-country-code="{escape(c["code"])}" role="button" tabindex="0" aria-label="{label}" aria-pressed="{str(selected).lower()}"><circle class="pin-target" r="30"/><circle class="pin-halo" r="14"/><circle class="pin-dot" r="5"/><text x="15" y="5">{escape(c["name"])}</text></g>')
    options=''.join(f'<option value="{escape(c["code"])}">{escape(c["name"])}</option>' for c in countries)
    return f'''<section class="wrap visitors visitor-atlas" id="visitors" aria-labelledby="visitors-title" data-visitor-locations><div class="visitor-intro"><span class="eyebrow">Website visitors</span><h2 id="visitors-title">Visitors,<br>near and far.</h2><p>Thank you for stopping by and taking an interest in me and my research.</p>{link(VISITORS['source'],'View visit statistics')}</div><div class="visitor-atlas-panel"><div class="visitor-atlas-heading"><span>Where visitors are browsing from</span><span class="visitor-period">{VISITORS['period_start'][:4]}</span></div><svg class="visitor-world" viewBox="0 0 900 450" role="group" aria-labelledby="visitor-world-title visitor-world-desc"><title id="visitor-world-title">Visitor countries on a world map</title><desc id="visitor-world-desc">Select a country to see its recorded visits. Markers represent countries, not exact visitor locations.</desc><image href="assets/visitor-world.svg" width="900" height="450"/><g class="visitor-pins">{''.join(pins)}</g></svg><div class="visitor-map-readout"><div><label for="visitor-country-choice">Explore a country</label><select id="visitor-country-choice">{options}</select></div><p class="visitor-selection" aria-live="polite"><strong>{active['visits']:,}</strong><span>recorded visits</span></p></div><p class="visitor-updated" role="status">Updated <time datetime="{VISITORS['updated_at']}">{VISITORS['updated_at'][:10]}</time></p><p class="visitor-fineprint">Country-level overview · <a href="privacy.html#visitor-map">About visitor data</a> · Map: <a href="https://www.naturalearthdata.com/">Natural Earth</a></p><script type="application/json" id="visitor-country-positions">{json.dumps(COUNTRY_POSITIONS,separators=(',',':'))}</script><script type="application/json" id="visitor-initial-data">{json.dumps(VISITORS).replace('<',chr(92)+'u003c')}</script></div></section>'''

def write_page(file,title,description,body,active='home'):
    if file != 'index.html':
        body = body.replace('<div class="wrap">', '<div class="page-shell">', 1)
    page_class = 'page-' + file.removesuffix('.html')
    nav=''
    for key,label,url in [('home','Home','index.html'),('research','Research','research.html'),('publications','Publications','publications.html'),('practice','Practice','practice.html')]:
        nav+=f'<a href="{url}"'+(' aria-current="page"' if active==key else '')+f'>{label}</a>'
    nav+='<a class="contact-link" href="contact.html"'+(' aria-current="page"' if active=='contact' else '')+'>Get in touch</a>'
    canonical='https://www.xingtingwu.com/'+('' if file=='index.html' else file)
    social_image='portrait' if file == 'index.html' else 'garden-map'
    html=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Xingting Wu</title><meta name="description" content="{escape(description)}">
<meta name="theme-color" content="#ffffff"><link rel="canonical" href="{canonical}">
<meta property="og:type" content="website"><meta property="og:title" content="{escape(title)} · Xingting Wu"><meta property="og:description" content="{escape(description)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="https://www.xingtingwu.com/assets/images/{social_image}.webp">
<link rel="icon" href="favicon.ico" sizes="16x16 32x32 48x48 64x64 128x128"><link rel="icon" href="favicon.png" type="image/png" sizes="128x128"><link rel="stylesheet" href="assets/site.css"><link rel="stylesheet" href="{asset_url('assets/minimal.css')}"><script defer src="{asset_url('assets/site.js')}"></script><script defer src="assets/motion.js"></script>
<noscript><style>@media(max-width:760px){{.site-header{{position:static}}.header-inner{{height:auto;display:block;padding-block:20px}}.nav{{display:flex;position:static;padding:15px 0 0;flex-direction:row;flex-wrap:wrap;border:0;gap:15px}}.nav .contact-link{{margin:0}}}}</style></noscript>
</head><body class="{page_class}"><a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap header-inner"><a class="brand" href="index.html" aria-label="Xingting Wu, home"><span>Xingting Wu <span class="chinese" lang="zh">武星廷</span></span></a>
<button class="menu-toggle" aria-expanded="false" aria-controls="main-nav" hidden>Menu <span aria-hidden="true">☰</span></button><nav class="nav" id="main-nav" aria-label="Main navigation">{nav}</nav></div></header>
<main id="main">{body}</main>
<footer class="site-footer"><div class="wrap"><div class="footer-main"><div>{eyebrow('A conversation starts somewhere')}<h2>Let’s make connections.</h2><p>Research, design, and everyday life. Based in Melbourne.</p></div><div class="footer-links"><a href="mailto:xingtingwu@swin.edu.au">Email</a><a href="{SCHOLAR}">Google Scholar</a><a href="https://xhslink.com/m/4sUuQcr9thK">Artwork</a></div></div><div class="footer-bottom"><span>© 2026 Xingting Wu · <span lang="zh">武星廷</span></span><a href="privacy.html">Photography &amp; privacy</a></div></div></footer>
<dialog class="lightbox" id="image-dialog" aria-label="Enlarged project photograph"><button type="button" aria-label="Close image">✕</button><img alt=""><p></p></dialog>
</body></html>'''
    (ROOT/file).write_text(html,encoding='utf-8')
    if file!='404.html': pages.append(canonical)

PROJECTS=[
 dict(id='crafting',title='Making together',year='2024',stage='Crafting',image='nativity-finished',alt='Completed Nativity display with hand-decorated figures in a raised garden bed',desc='Shared crafting, brought together in an outdoor Nativity display.'),
 dict(id='gardening',title='Our Garden',year='2025',stage='Gardening',image='garden-together',alt='People holding and planting a flowering plant together at a raised garden bed',desc='Exploring plants, care, and the rhythms of everyday participation.'),
 dict(id='outdoor-discovery',title='Following curiosity',year='2025',stage='Outdoor discovery',image='garden-map',alt='A hand-drawn garden map with photographs of places in the garden',desc='Maps, nature cards, and birdsong as invitations to notice and share.',material=True)
]

HOME_PROJECTS=[
 dict(PROJECTS[0],title='Outdoor Nativity Scene',image='selected-nativity-graded',alt='Xingting Wu, residents and a care staff member sharing wooden sheep during a Nativity crafting session',photo_class='selected-cover selected-nativity'),
 dict(PROJECTS[1],title='Our Gardening Club',image='selected-gardening-graded',alt='Xingting Wu, residents and a care staff member gathered around a table in the garden',photo_class='selected-cover selected-gardening'),
 dict(id='outdoor-stories',title='Our Outdoor Stories',year='2026–ongoing',stage='Plants & stories',image='selected-stories-graded',alt='Xingting Wu with residents and care staff sharing flowers and plant cards around indoor tables',desc='Shared walks, plants, and memories, brought together in the latest Our Outdoor Stories book.',photo_class='selected-cover selected-stories',href=OUTDOOR_STORYBOOK,cta='Read the storybook')
]

def project_grid(projects=PROJECTS):
    cards=''
    for p in projects:
        photo_class=p.get('photo_class') or ('specimen' if p.get('specimen') else 'contain' if p.get('material') else '')
        href=p.get('href',p['id']+'.html')
        cta=f'<span class="project-cta">{escape(p["cta"])}</span>' if p.get('cta') else ''
        cards+=f'''<a class="project-link" href="{escape(href)}"><div class="image-wrap">{img(p['image'],p['alt'],photo_class)}</div><div class="project-number"><span>{p['stage']}</span><span>{p['year']}</span></div><h3>{p['title']}</h3><p>{p['desc']}</p>{cta}</a>'''
    return '<div class="project-grid">'+cards+'</div>'

def selected():
    rows=''
    for id in ['KlAtU1dfN6UC','care-robots-filial-responsibility','0EnyYjriUFMC','roLk4NBRz8UC','Tyk-4Ss8FVUC']:
        p=next(x for x in PAPERS if x['id']==id)
        rows+=f'<a class="selected-paper" href="{escape(p["paper_url"])}"><span class="year">{p["year"]}</span><div><h3>{escape(p["title"])}</h3><p>{escape(p["venue"])}</p>{paper_details(p,linked=False)}</div></a>'
    return '<div class="selected-list">'+rows+'</div>'

def news_updates():
    # The book date marks sharing it here; fieldwork dates follow the documented activities.
    return f'''<section class="home-news home-section" id="news-updates" aria-labelledby="news-heading"><div class="wrap">
<div class="home-section-head"><h2 id="news-heading">News &amp; updates</h2><p>Notes from fieldwork, making, and research life.</p></div>
<div class="news-list">
<article class="news-item"><time datetime="2026-11">Nov 2026</time><p>{link(OUTDOOR_STORYBOOK,'Sharing the Our Outdoor Stories book.','news-title')} Shared walks, plants, photographs, and memories, collected in the latest project book.</p></article>
<article class="news-item"><time datetime="2026-09">Sep 2026</time><p>{link('outdoor-stories.html#many-ways','Plants, prompts, and conversation.','news-title')} Sharing flowers and plant cards around the table with residents and care staff.</p></article>
<article class="news-item"><time datetime="2024">2024</time><p>{link('crafting.html#preparation','Before the making table.','news-title')} Preparing laser-cut pieces at ProtoLAB for residents to assemble, decorate, and make their own.</p></article>
</div></div></section>'''

home=f'''<div class="profile-band"><div class="wrap"><section class="profile-hero" aria-labelledby="profile-title">
<figure class="profile-photo">{img('portrait','Xingting Wu making a colourful artwork',eager=True)}<figcaption>Making an artwork, 2023.</figcaption></figure>
<div class="profile-intro"><h1 id="profile-title">Xingting Wu<span class="profile-name-zh" lang="zh">武星廷</span></h1><p class="profile-role">Design researcher &amp; illustrator</p><p class="profile-affiliation">PhD candidate · Swinburne University of Technology · Melbourne</p><div class="profile-bio"><p>My PhD explores how design can support outdoor engagement in residential aged care. I work with older adults and care staff through crafting, gardening, and nature discovery.</p><p class="profile-supervision">My doctoral research is supervised by <a href="https://experts.swinburne.edu.au/1344">Prof. Sonja Pedell</a>, <a href="https://dmunoz.net/">Dr. Diego Muñoz</a>, and <a href="https://www.leonsterling.com/">Prof. Leon Sterling</a>, and supported by a full scholarship funded by the Australian Research Council (ARC).</p><p>My wider research connects human–AI interaction, education, and technology adoption. Through collaborations across design, HCI, and education, I explore creative practice and learning across generations.</p></div><div class="profile-links">{link(SCHOLAR,'Google Scholar','button')}{link('contact.html','Get in touch')}{link('mailto:xingtingwu@swin.edu.au','Email')}</div></div>
</section></div></div>
{research_landscape()}
<section class="home-projects home-section" id="projects"><div class="wrap"><div class="home-section-head"><h2>My PhD Field Work</h2><div><p>My doctoral research follows creative activities, outdoor places, and everyday participation in residential aged care.</p>{link('research.html','Explore the research journey')}</div></div>{project_grid(HOME_PROJECTS)}</div></section>
{background()}
<section class="home-publications home-section" id="recent-writing"><div class="wrap"><div class="home-section-head"><h2>Recent writing</h2><div><p>Publications from my doctoral research and wider collaborations.</p>{link('publications.html','View all publications')}</div></div>{writing_stats()}{selected()}</div></section>
{home_service()}'''
write_page('index.html','Design researcher & illustrator','Meet Xingting Wu, a PhD candidate at Swinburne University of Technology researching participatory design, older adults, outdoor engagement and human–AI interaction.',home)

RESEARCH_STUDIES=[
 dict(HOME_PROJECTS[0],desc='Making and decorating together, connecting residents’ individual contributions with a shared outdoor Nativity scene.'),
 dict(HOME_PROJECTS[1],desc='Choosing, planting and caring for plants together, exploring sensory experiences and connections across indoor and outdoor spaces.'),
 dict(id='outdoor-discovery',title='Outdoor Discovery',image='discovery-map-conversation',alt='Xingting Wu and residents gathered around illustrated garden maps outdoors',desc='Using maps, nature cards and birdsong to invite curiosity, recognition and shared conversations about garden life.'),
 dict(HOME_PROJECTS[2],image='stories-walk-group-cover',alt='Residents and care staff together on an outdoor walk through the gardens',desc='Connecting garden walks with plant choices, personal stories and shared displays that can be revisited indoors.')
]

study_cards=''.join(f'''<a class="study-card" href="{p['id']}.html"><div class="study-image">{img(p['image'],p['alt'],eager=i<2)}</div><span class="study-number">Study {i+1}</span><h2>{p['title']}</h2><p>{p['desc']}</p></a>''' for i,p in enumerate(RESEARCH_STUDIES))
research=f'''<div class="wrap">{head('Research / PhD in Design','Designing meaningful connections<br>with the <em>outdoors.</em>','Four studies exploring how design can support older adults’ outdoor engagement in residential aged care, through making, gardening, discovery and storytelling.')}<section class="study-grid" aria-label="Four PhD studies">{study_cards}</section></div>'''
write_page('research.html','Research','Four PhD studies exploring outdoor engagement with older adults through crafting, gardening, nature discovery and storytelling.',research,'research')

def author_markup(text):
    return re.sub(r'(?<![\w-])(Xingting Wu|X Wu|武星廷)(?![\w-])',r'<strong>\1</strong>',escape(text))

def publication(p):
    actions=link(p['paper_url'],p['paper_label'])
    return f'''<article class="publication" id="pub-{p['id']}" data-year="{p['year']}" data-type="{p['type']}"><div class="pub-type">{escape(p['label'])}</div><h3><a href="{escape(p['paper_url'])}">{escape(p['title'])}</a></h3><p class="pub-authors">{author_markup(p['authors'])}</p><p class="pub-venue">{escape(p['venue'])} · {p['year']}</p>{paper_details(p)}<div class="pub-actions">{actions}</div></article>'''

pubs=f'''<div class="wrap">{head('Writing & scholarship','Publications.','Work on older adults, participatory design, human–AI interaction, and design education.', '<div class="actions">'+link(SCHOLAR,'View on Google Scholar')+'</div>')}<form id="publication-filters" class="filters" hidden role="search" aria-label="Filter publications"><div class="field"><label for="publication-search">Search publications</label><input id="publication-search" name="search" type="search" placeholder="Try older adults, co-creation, or an author…" autocomplete="off"></div><div class="field"><label for="publication-type">Publication type</label><select id="publication-type" name="type"><option value="">All types</option><option value="journal">Journal articles</option><option value="conference">Conference contributions</option><option value="preprint">Preprints</option></select></div><div class="field"><label for="publication-year">Year</label><select id="publication-year" name="year"><option value="">All years</option>{''.join(f'<option>{y}</option>' for y in [2026,2025,2022,2021])}</select></div><button class="reset" type="reset">Clear filters ↺</button></form><p class="result-count" id="publication-count" role="status" aria-live="polite">{len(PAPERS)} publications · Updated {UPDATED}</p><div id="no-publications" class="empty-state" hidden><h2>No matching publications.</h2><p>Try a broader search, another year, or clear the filters.</p></div>'''
for year in [2026,2025,2022,2021]:
    pubs+=f'<section class="pub-year" aria-labelledby="year-{year}"><h2 id="year-{year}">{year}</h2><div>'+''.join(publication(p) for p in PAPERS if p['year']==year)+'</div></section>'
pubs+=f'<p class="note">List based on my Google Scholar profile and publisher records. Updated {UPDATED}. Preprints and conference contributions are labelled separately from journal articles. Journal indicators show the stated JIF year; quartiles are included where verified against publisher information or the JCR release table. Select an indicator to view its source.</p></div>'
write_page('publications.html','Publications','Publications by Xingting Wu: journal articles, conference contributions and preprints, with direct links to publisher pages and clearly labelled preprints.',pubs,'publications')

def project_page(file,title,kicker,lead,year,focus,cover,alt,caption,sections,next_project,material=False,compact_header=False):
    toc='<aside class="toc" aria-label="On this page">'+eyebrow('In this project')+''.join(f'<a href="#{id}">{heading}</a>' for id,heading,content in sections)+'</aside>'
    content=''.join(f'<section id="{id}"><h2>{heading}</h2>{html}</section>' for id,heading,html in sections)
    intro=f'''<div class="page-head"><a class="bread" href="research.html">← All research</a>{eyebrow(kicker)}<h1>{title}</h1><p class="lead">{lead}</p><dl class="project-meta"><div><dt>When</dt><dd>{year}</dd></div><div><dt>Context</dt><dd>Residential aged care</dd></div><div><dt>Focus</dt><dd>{focus}</dd></div></dl></div>'''
    if compact_header:
        photo=figure(cover,alt,caption,'project-intro-photo',True,sizes='(max-width: 760px) calc(100vw - 40px), (max-width: 1232px) 44vw, 495px')
        intro=f'<div class="project-intro-split">{intro}{photo}</div>'
    else:
        intro+=figure(cover,alt,caption,'project-cover'+(' material' if material else ''),True)
    body=f'''<div class="wrap">{intro}<div class="article-layout">{toc}<div class="prose">{content}</div></div><a class="next-project" href="{next_project[0]}"><div>{eyebrow('Continue exploring')}<h2>{next_project[1]}</h2></div>{ARROW}</a></div>'''
    write_page(file,title.replace('<br>',' ').replace('<em>','').replace('</em>',''),lead,body,'research')

def learning(title,text): return f'<div class="learning">{eyebrow(title)}<p>{text}</p></div>'

project_page('outdoor-stories.html','Our Outdoor<br><em>Stories.</em>','PhD research / Study 4 · Ongoing','Connecting outdoor walks with daily life: from design materials and shared walks to recorded stories, postcards, and conversations indoors.','2026 · Ongoing','Walking · Sharing stories · Revisiting experiences','stories-garden-hero','Residents and a care staff member together in the garden, with two residents holding roses','Residents and a care staff member together in the garden, 30 October 2026.',[
('design-materials','1. Design materials.','<span id="starting-point"></span><p>How can design materials support engagement beyond our visits? The materials pair a card to carry on a walk with information placed beside a plant.</p>'+photo_sequence([
('stories-treasure-card','Grevillea treasure hunt card with a plant photograph and prompts to look, try, and think','<strong>Treasure hunt card.</strong> A portable invitation to find a plant, compare its photograph, and notice its details.'),
('stories-plant-info-card','Grevillea plant information card with its name, photograph, and prompts for conversation','<strong>Plant information card.</strong> Placed beside the plant to help confirm its name, explore a detail, and start a conversation.')
],'documentary study-materials')+'<p>Care staff support the activity by helping people use the cards, look at the plants, and talk about what they notice.</p>'),
('map-and-play','2. Walking together.','<p>We began at the café with “Can You Find It?” cards, then took them outside. The photographs follow one walk, from preparing to leave to pausing and looking closely together.</p>'+photo_sequence([
('stories-walk-cards','A resident and companion holding printed plant-finding cards before a walk','<strong>Ready to set off.</strong> Looking at the cards at the café before going outside.'),
('stories-walk-blossom','A resident and care staff member pausing beneath a flowering tree','<strong>Noticing blossom.</strong> Pausing beneath the flowering tree to look together.'),
('stories-walk-looking','Care staff supporting residents to compare a plant photograph with the living plant','<strong>Cards along the way.</strong> Holding the picture beside the plant and comparing what we see.'),
('stories-walk-leaf','A resident holding a leaf with the activity cards nearby','<strong>A leaf in hand.</strong> Taking a closer look, with the activity cards nearby.')
],'documentary')+'<p class="note">Walking activity, 4 September 2026 · Martin Luther Homes.</p>'),
('many-ways','3. Sharing and recording.','<span id="plant-choices"></span><p>Plants collected outdoors became prompts for indoor conversation. Residents shared a chosen plant, a reason for liking it, or a memory. Staff helped record their words on labels and story cards, keeping the contribution with the plant that prompted it.</p>'+photo_sequence([
('stories-sharing-recording','A care staff member writing during a conversation with residents around a table of flowers','<strong>Share a plant, reason, or memory.</strong> Flowers and conversation around the table.'),
('stories-recorded-label','A handwritten plant label recording a resident’s memory of proteas in a family garden','<strong>Record residents’ words.</strong> A plant label keeps a preference or memory close to the flower.')
],'documentary')+figure('stories-written-memory','A completed bay leaf story card recording a memory about a tree on a farm','<strong>Keep the words with the plant.</strong> A story card provides space for a longer contribution.','recorded-story')),
('plant-stories','4. Making stories shareable.','<p>The recorded contributions became objects to keep and share. Handwritten labels accompanied the plants, while personalised postcards brought together a resident’s portrait, chosen plant, and story.</p>'+figure('stories-plant-labels','Three plants with handwritten labels recording residents’ preferences and memories','Plants and handwritten labels keep the contributions together.')+photo_sequence([
('stories-postcard-bay-leaf','A personalised postcard pairing a resident’s portrait with a memory of a bay tree','A portrait, a chosen plant, and a memory of a familiar place.'),
('stories-postcard-euphorbia','A personalised postcard pairing a resident’s portrait with a comment about euphorbia','A postcard preserves a short observation about a plant’s shape and scent.')
],'documentary study-postcards')),
('map-in-use','5. Revisiting the outdoors.','<p>Back indoors, the walking map, garden video, and real plants provided shared reference points. Residents and staff could locate familiar plants on the map, pause the video to look, and continue the conversation together.</p>'+photo_sequence([
('stories-map-conversation','Residents and care staff looking together at a circular walking map beside a screen showing the garden','<strong>Locate and talk.</strong> Finding familiar plants and places on the walking map.'),
('stories-video-conversation','Residents and care staff gathered around the map while a garden video plays on a large screen','<strong>Pause and revisit.</strong> Looking at the garden video and discussing what is on screen.')
],'documentary')+'<p class="note">Indoor session, October 2026. This study is ongoing; longer-term use remains a research question.</p>'),
('storybook','Read Our Outdoor Stories.','<span id="continuity"></span><p>The latest project book brings together shared walks, plants, photographs, and memories. Browse the pages to see the materials, residents’ contributions, and experiences from Our Outdoor Stories.</p><div class="actions">'+link(OUTDOOR_STORYBOOK,'Read the storybook','button')+'</div>')
],('crafting.html','Making together'),compact_header=True)

project_page('crafting.html','Making<br><em>together.</em>','PhD research / Study 1','Exploring how shared crafting can connect indoor activities with outdoor places, and make personal contributions visible.','2024','Participatory making · Material adaptation · Garden displays','nativity-finished','A completed outdoor Nativity display with hand-decorated figures and plants','The completed Nativity display brings the figures made during the workshops into a shared outdoor setting, December 2024.',[
('invitation','An invitation to make.','<p>Crafting offered a way to begin with familiar interests and tangible materials. Residents and staff took part in making nature-inspired decorations and figures, with the possibility of displaying contributions outdoors.</p><p>The research explored how digital fabrication tools, including a Cricut and laser cutting, could help prepare materials for shared making. The design work involved both preparing the activity and adapting it to the people taking part.</p>'+figure('selected-nativity-graded','Xingting Wu with residents and a staff member around a table of wooden sheep','Sharing the wooden sheep around the making table, September 2024.')),
('around-the-table','A place at the making table.','<p>Paper flowers offered an early way to try the prepared shapes together. Residents selected colours, folded and arranged pieces, and combined their flowers in a shared composition.</p>'+figure('craft-workshop-table','A shared Cricut crafting workshop with residents seated around a table of paper materials','Trying out paper shapes together at the Cricut crafting workshop, August 2024.')+photo_sequence([
('craft-cutting-paper','A resident cutting along the drawn outline of a paper flower','Cutting out a flower shape during the paper-crafting workshop, August 2024.'),
('craft-paper-detail','Hands arranging colourful paper flowers on a shared board','Different colours, folds, and arrangements in the paper-flower composition, August 2024.')
],'uneven')+'<p>The photographs follow the work in someone’s hands, from cutting a drawn outline to arranging flowers in a shared composition.</p>'),
('preparation','Before the workshop.','<p>I prepared the making activities by testing paper shapes with the Cricut and developing wooden parts for laser cutting. At the university makerspace, the designs moved from Adobe Illustrator files to physical pieces that could be handled, assembled, and decorated.</p>'+figure('protolab-making','Xingting Wu working at a laser cutter in Swinburne ProtoLAB','Preparing materials at Swinburne ProtoLAB. Still from an original preparation video, 2024.','photo-wide')+'<p>I also recorded the laser-cutting process and shared it during the workshops, so participants could see how the materials were made.</p>'+figure('nativity-cut-layout','Cutting layout showing Nativity figures, animals, slots and bases','A Nativity cutting layout with figure outlines, slots, and separate bases.')+'<div class="actions">'+link('practice.html#making-process','Explore the making process')+'</div>'),
('iteration','Make the material easier to enter.','<p>Early Nativity models involved multiple interlocking pieces. Handling and fitting these parts could make assembly difficult. Staff suggestions and observations during sessions informed a simpler approach.</p>'+figure('craft-materials','Participants assembling wooden sheep models at a table','Early assembly work illustrates the handling demands of a multipart model.')+learning('From observation to a design change','The sheep was simplified to a body shape and two leg pieces. Other figures used an outline and a base. This shifted attention toward decorating and personalising the objects.')+'<p>Reducing assembly demands did not mean deciding the decoration for participants. It created more room for different choices of colour, texture, and character.</p>'),
('drawing','Each figure, a personal touch.','<p>Drawing and colouring happened directly on the wooden forms. Markers, fabric, wool, and feathers offered different ways to add details: a face, a pattern, a coat, or a bright yellow star.</p>'+photo_sequence([
('craft-making-side-by-side','Xingting Wu working beside a resident as she decorates a wooden Nativity figure','Working side by side on a Nativity figure, November 2024.'),
('craft-decorating-figure','A resident adding colour to a wooden Nativity figure at a table of craft materials','Adding colour and details to a Nativity figure, November 2024.')
],'uneven')+photo_sequence([
('craft-drawing-detail','A resident drawing green details on a wooden animal with a marker','Adding hand-drawn details to a wooden animal, October 2024.'),
('craft-colouring','A resident colouring a wooden star yellow with a marker','Colouring a star for the Nativity display, November 2024.')
])+'<p>Even when people began with similar wooden shapes, the decorated figures looked different. These details keep individual contributions visible within the shared display.</p>'+figure('craft-own-design','Two residents seated with their differently decorated wooden animals','Wool, cloth, and drawn details give the wooden animals their own character, October 2024.')),
('planning-the-display','Bringing the pieces together.','<p>The individually decorated figures were brought together as a Nativity scene. Before the outdoor display, residents and staff discussed how the pieces could come together in the garden.</p>'+figure('craft-display-together','A resident standing beside the assembled Nativity scene and hand-decorated wooden figures','Looking at the Nativity scene as the shared display takes shape, December 2024.')),
('outdoors','Let contributions travel outdoors.','<p>Crafted objects became part of garden-bed displays. The outdoor setting offered a place to encounter the results of earlier making and to share them with other people.</p><p>This raised questions about visibility and recognition: where should a contribution be placed, how can someone see it, and what makes a display worth returning to?</p>'+photo_sequence([('craft-garden-placement','A resident leaning over a garden bed to arrange the Nativity setting','Arranging the garden-bed setting, November 2024.'),('craft-garden-encounter','A resident holding a decorated wooden camel outdoors','A decorated figure out in the garden, December 2024.')],'uneven')+learning('Design reflection','The relationship between making an object and later encountering it matters. Materials, placement, and staff collaboration all shape that connection.')),
('next','What this opened up.','<p>The crafting study drew attention to material accessibility, staff collaboration, and the value of keeping contributions visible. The gardening study then explored participation through living plants, care, and change over time.</p><div class="actions">'+link('gardening.html','Continue to Our Garden')+'</div>')
],('gardening.html','Our Garden'))

project_page('gardening.html','Our<br><em>Garden.</em>','PhD research / Study 2','Exploring how plants, shared care, and everyday relationships shape outdoor engagement in residential aged care.','April–October 2025','Gardening · Sensory encounters · Indoor–outdoor connections','garden-together','People working together with soil and plants at a raised garden bed','Planting together at a raised garden bed during the gardening study.',[
('planting','Working with living things.',figure('selected-gardening-graded','Xingting Wu with residents and care staff gathered at an outdoor table','Coming together in the garden at the beginning of the study, April 2025.')+'<p>Gardening brings a different rhythm to participation. Plants grow, change, and need care between organised activities. This study followed gardening activities over time, attending to practical work, sensory encounters, and the relationships formed around plants.</p><p>Shared activities included choosing plants, planting, and discussing what people noticed. Weather, space, and staff availability were part of the conditions that shaped participation.</p>'+photo_sequence([('garden-hands','Two people tending a flowering plant together in a raised garden bed','Tending a flowering plant together.'),('garden-planting-detail','A resident using a hand fork among plants in a raised garden bed','Working the soil and planting at the raised bed, April 2025.')],'documentary')),
('caring-and-returning','A reason to return.','<p>Planting was followed by watering and visits to look at growth. These encounters brought residents and staff back to the same garden beds, where the plants continued to change between organised activities.</p>'+photo_sequence([('garden-watering','A resident watering plants in a raised garden bed with a hose','Watering the garden bed, April 2025.'),('garden-returning','A resident and a staff member looking together at a raised garden bed','Returning to look at the garden together, July 2025.')],'documentary')),
('inside-outside','The garden reaches indoors.','<p>Outdoor engagement did not always mean being physically outside. Photographs and plants could bring the garden into indoor conversations. Plants adopted into personal spaces also became part of the relationship between individual care and a shared garden.</p><p>The study followed the movement of plants between personal spaces and communal areas, and explored how photographs might support remembering and talking about garden activities.</p>'+figure('garden-conversation','Residents and a facilitator around an indoor table with photographs and small trays of materials','Photographs and collected materials around an indoor table, 2025.')+learning('A connection across places','The design question is not simply how to increase time outdoors. It also concerns what can make the garden present, approachable, and meaningful within daily life.')),
('technology','Technology within the activity.','<p>Photographs and a plant-character chatbot were explored as ways to support looking back and conversation. These experiments also exposed limits: responses depended on the situation, the person, and the support available.</p><p>The research treats technology as something to examine within real activities. A device or a conversational response is not, by itself, evidence of meaningful participation.</p>'),
('learning','Care is part of the design.','<p>Participation developed within everyday arrangements: where a plant could be kept, who could help, and how an activity fitted the day. These details were central to understanding what could continue.</p>'+learning('Design reflection','A garden activity includes the work before and after a session. Designing for continuity means attending to ongoing care, staff collaboration, and opportunities to revisit a contribution.')+'<p>The next study explored curiosity about the wider outdoor environment through maps, nature cards, and birdsong.</p>')
],('outdoor-discovery.html','Following curiosity'))

project_page('outdoor-discovery.html','Following<br><em>curiosity.</em>','PhD research / Study 3','Using maps, nature cards, and birdsong to invite noticing, recognition, imagination, and shared conversation.','November–December 2025','Nature discovery · Visual materials · Sound','discovery-map-conversation','Xingting Wu with residents and a facilitator looking at illustrated garden maps around outdoor tables','Looking at the garden maps together, November 2025.',[
('noticing','Start with what catches attention.','<p>A bird call, a familiar plant, or an unexpected detail can open a conversation. This study explored outdoor ecological discovery through materials that residents could look at, listen to, choose, and discuss.</p><p>An activity-preference booklet helped invite choices about what to explore. The materials offered different entry points, rather than expecting everyone to take part in the same way.</p>'+figure('discovery-booklet-in-use','A resident looking through an illustrated activity booklet','Looking through an activity booklet during the discovery study, November 2025.','portrait-figure')),
('mapping-together','A familiar place, seen together.','<p>The illustrated map was used around the garden table, alongside photographs of familiar places. Residents could point, compare and talk about what they recognised. The map became part of a shared conversation about the garden.</p>'+figure('garden-map','An illustrated garden map paired with photographs of familiar locations','The map used in the outdoor conversations. Photographs connect the drawing with recognisable places.')),
('materials','A small collection of invitations.','<p>The toolkit brought together a hand-drawn map, plant and animal cards, clue and fact cards, and birdsong. Photographs supported recognition, while questions and sound invited people to contribute their own knowledge and associations.</p>'+figure('nature-cards','A collection of plant, animal, clue and fact cards','Nature cards use distinct categories for identification, clues, and ecological facts.')+'<p>Maps were useful for some conversations about places, while understanding and locating oneself on a map varied. The design needed to accommodate this difference.</p>'),
('curiosity','Different forms of curiosity.','<p>The analysis considered observational, identificatory, imaginative, and connective forms of curiosity. Some exchanges began with looking closely or naming a bird. Others moved toward possibilities, associations, or a remembered place.</p>'+learning('A material can outlast an activity','Some residents chose to keep bird images. This points to the importance of what a person can take away, retain, or revisit after the group activity finishes.')+photo_sequence([('discovery-cards-in-use','Two residents looking at illustrated nature materials together at a garden table','Looking through the nature materials outdoors, November 2025.'),('discovery-photo-wall','A resident placing a bird photograph on an indoor wall','Giving a bird photograph a place on the wall, November 2025.') ])),
('sharing-birds','Something to show one another.','<p>Bird images also became materials to hold up and share indoors. Looking at the images together made room for recognition and for residents to contribute what they knew.</p>'+figure('discovery-bird-sharing','Residents sitting around tables while one holds up an illustrated bird sheet for the group','Sharing bird images around the table, December 2025.')),
('design','Keep the invitation accessible.','<p>Visibility, pace, and opportunities to respond shaped participation. In group activities, a small card or a quickly spoken clue could be difficult to follow.</p><p>These observations inform the ongoing Our Outdoor Stories exploration, which connects walking, plant choices, and materials that remain visible in a shared space.</p><div class="actions">'+link('outdoor-stories.html','See the ongoing exploration')+'</div>')
],('outdoor-stories.html','Our Outdoor Stories'))

practice=f'''<div class="wrap">{head('Design practice','Design process<br><em>&amp; output.</em>','I combine digital fabrication, illustration, and information design to make materials for shared activities with older adults.','<nav class="practice-index" aria-label="Practice areas">'+link('#making-process','ProtoLAB &amp; fabrication')+link('#materials','Visual &amp; information design')+'</nav>')}
<section class="practice-domain practice-fabrication" id="making-process" aria-labelledby="fabrication-heading">
<header class="practice-domain-head"><div>{eyebrow('Physical making')}<h2 id="fabrication-heading">ProtoLAB &amp;<br> fabrication.</h2></div><div><p>Turning digital drawings into physical pieces that people can assemble, decorate, and make their own.</p><p class="practice-skills"><strong>Skills</strong> Vector drawing · Laser cutting · Material prototyping</p></div></header>
<div class="practice-phase"><div class="practice-phase-copy"><h3>Design process</h3><ul class="practice-points"><li><strong>Draw.</strong> Prepare outlines, slots, and bases in Adobe Illustrator.</li><li><strong>Make.</strong> Laser-cut wooden parts at Swinburne ProtoLAB.</li><li><strong>Refine.</strong> Use workshop observations and staff feedback to simplify assembly.</li></ul>{link('crafting.html#iteration','Follow the design iterations')}</div><div class="practice-evidence practice-pair">
{figure('protolab-making','Xingting Wu preparing wooden components at the laser cutter in Swinburne ProtoLAB','<strong>Making at ProtoLAB.</strong> Turning the digital files into wooden parts. Video still, 2024.','practice-photo',True)}
{figure('nativity-cut-layout','Digital outlines of Nativity figures, slots and bases prepared for laser cutting','<strong>Preparing the cutting files.</strong> Outlines, slots, and separate bases for the Nativity figures.','practice-sheet')}
</div></div>
<div class="practice-phase"><div class="practice-phase-copy"><h3>Output</h3><ul class="practice-points"><li>Wooden figures to assemble and personalise.</li><li>Colour, fabric, and wool chosen by residents.</li><li>A shared Nativity scene in the garden.</li></ul>{link('crafting.html','Explore Outdoor Nativity Scene')}</div><div class="practice-evidence practice-pair">
{figure('craft-decorating-figure','A resident decorating a wooden Nativity figure with craft materials','<strong>Figures to personalise.</strong> Adding colour and detail to the prepared wooden forms, November 2024.','practice-photo')}
{figure('nativity-finished','Completed Nativity scene with residents’ decorated wooden figures in a raised garden bed','<strong>The shared outdoor display.</strong> The decorated figures together in the garden, December 2024.','practice-photo')}
</div></div></section>
<section class="practice-domain practice-visual" id="materials" aria-labelledby="visual-design-heading">
<header class="practice-domain-head"><div>{eyebrow('Visual communication')}<h2 id="visual-design-heading">Visual &amp;<br> information design.</h2></div><div><p>Cards to carry, information beside the plants, and a large map to explore together.</p><p class="practice-skills"><strong>Skills</strong> Information design · Print production · Spatial illustration</p></div></header>
<div class="practice-phase"><div class="practice-phase-copy"><h3>Design process</h3><ul class="practice-points"><li><strong>Recognise.</strong> Use photographs of the plants along the walking route.</li><li><strong>Explore.</strong> Pair images with short prompts to look, try, and talk.</li><li><strong>Make.</strong> Produce cards for carrying and hanging outdoors.</li></ul><h4 class="material-spec-heading">Card specifications</h4><dl class="practice-material-spec"><div><dt>Size</dt><dd>12 × 18 cm</dd></div><div><dt>Material</dt><dd>3 mm acrylic</dd></div><div><dt>Printing</dt><dd>UV printing</dd></div><div><dt>Formats</dt><dd>Hand-held &amp; hanging</dd></div></dl></div><div class="practice-evidence practice-pair practice-card-designs">
{figure('stories-treasure-card','Treasure hunt card with a plant photograph and prompts to look for, try and think about','<strong>Treasure hunt card.</strong> A portable prompt for looking closely.','practice-sheet')}
{figure('stories-plant-info-card','Plant information card with plant name, photograph and prompts for observation and storytelling','<strong>Plant information card.</strong> A shared reference beside the living plant.','practice-sheet')}
</div></div>
<h3 class="practice-output-heading">Output in use</h3>
<article class="practice-phase practice-use" id="treasure-hunt-cards"><div class="practice-phase-copy"><h4>Treasure hunt cards</h4><ul class="practice-points"><li>Hold a card during the walk.</li><li>Match its photograph with the plant.</li><li>Pause to notice a detail or share a thought.</li></ul></div><div class="practice-evidence practice-pair practice-portrait-pair">
{figure('stories-walk-cards','A resident holding treasure hunt cards on her lap before a garden walk','<strong>In residents’ hands.</strong> Choosing and looking at the cards before setting off.','practice-photo')}
{figure('stories-walk-looking','Residents and care staff holding a plant card beside living plants during an outdoor walk','<strong>Along the walking route.</strong> Taking the photograph to the plant.','practice-photo')}
</div></article>
<article class="practice-phase practice-use" id="plant-information-cards"><div class="practice-phase-copy"><h4>Plant information cards</h4><ul class="practice-points"><li>Hang the card beside its plant.</li><li>Keep the name, photograph, and prompts together.</li><li>Make the information visible on later walks.</li></ul></div><div class="practice-evidence practice-pair practice-portrait-pair">
{figure('practice-plant-card-outdoors','UV-printed plant information card hanging below yellow roses outdoors','<strong>Beside the plant.</strong> A yellow rose information card hanging from the rose bush, November 2026.','practice-photo')}
{figure('practice-card-in-garden','Plant information card hanging among red roses beside the garden path','<strong>Part of the garden.</strong> The card stays with the plant along the route, November 2026.','practice-photo')}
</div></article>
<article class="practice-phase practice-use" id="circular-walking-map"><div class="practice-phase-copy"><h4>A shared circular map</h4><ul class="practice-points"><li>Bring the walking route into one large visual.</li><li>Point to familiar plants and places together.</li><li>Revisit outdoor experiences in an indoor conversation.</li></ul>{link('outdoor-stories.html#map-in-use','See the map in the study')}</div><div class="practice-evidence practice-pair practice-map-pair">
{figure('practice-circular-map','Large circular Walking Route Map displayed on the wall with illustrated plants and paths','<strong>The large-format map.</strong> Plants and paths brought together in a circular walking map.','practice-photo')}
{figure('stories-map-conversation','Residents and care staff pointing and looking together at the large circular walking map','<strong>A map to use together.</strong> Locating plants and sharing memories around the table.','practice-photo')}
</div></article>
<div class="practice-artwork" id="illustration"><div><h3>Illustration beyond the fieldwork</h3><p>Digital illustration, landscape sketches, and scenes from everyday life.</p></div>{link('https://xhslink.com/m/4sUuQcr9thK','Explore my artwork')}</div>
</section></div>'''
write_page('practice.html','Design practice','Xingting Wu’s design process and outputs: ProtoLAB fabrication, participatory making, illustration, garden maps, and printed storytelling materials.',practice,'practice')

# About content now lives on Home; remove the retired generated page.
(ROOT/'about.html').unlink(missing_ok=True)

contact=f'''<div class="wrap">{head('Contact','Get in touch.','I am always open to research collaborations. Please feel free to get in touch!')}<section class="contact-details" aria-labelledby="contact-email-heading"><div><h2 id="contact-email-heading">Email</h2><a class="contact-email" href="mailto:xingtingwu@swin.edu.au">xingtingwu@swin.edu.au</a><p>For research collaborations, peer review invitations, illustration, and drawing lessons.</p></div><div class="contact-wechat"><h2>WeChat</h2><div class="wechat-card"><a href="assets/images/wechat-qr.png" data-image data-caption="WeChat: wuxingting2010" aria-label="Enlarge my WeChat QR code"><img class="wechat-qr" src="assets/images/wechat-qr.png" width="730" height="730" alt="WeChat QR code for wuxingting2010" decoding="async"></a><div><p class="wechat-id">wuxingting2010</p><p class="wechat-note">Scan to connect.<br>Tap the code to enlarge.</p></div></div><div class="contact-location"><h2>Based in Melbourne</h2><p>School of Design and Architecture<br>Swinburne University of Technology<br>Melbourne, Australia</p><div class="actions">{link(SCHOLAR,'Google Scholar')}{link('https://xhslink.com/m/4sUuQcr9thK','Artwork')}</div></div></div></section></div><div class="contact-map-band">{visitor_locations()}</div>'''
write_page('contact.html','Get in touch','Contact Xingting Wu for research collaborations, peer review invitations, illustration and drawing lessons.',contact,'contact')

privacy=f'''<div class="wrap">{head('Care in representation','Photography & privacy.')}<div class="privacy-text"><p>The research photographs on this website show materials, activities, and shared settings. Photographs are shown alongside descriptions of the activity or material.</p><h2>Respecting personal contributions</h2><p>Captions focus on activities and design materials. Personal contributions remain part of the context in which they were shared; photographs are not used to infer a person’s abilities or health.</p><h2 id="visitor-map">Visitor statistics</h2><p>The Get in touch page shows country-level visit totals from MapMyVisitors. Opening that page on this website sends a counting request to MapMyVisitors, including your IP address and browser information. The service uses IP-based geolocation; this website does not request GPS access.</p><p>The map shows aggregate recorded visits by country, not people currently online. Its markers represent countries rather than exact visitor positions. They are refreshed periodically from the public statistics page, with an update time shown. Locations are approximate; visits without a country are not included in the country totals. The exported data contains country names and totals, without individual visitor addresses or coordinates.</p><p>MapMyVisitors states that its embedded counter does not set cookies or track visitors across websites. For processing, retention, and your rights, see the <a href="https://mapmyvisitors.com/b/policy">MapMyVisitors privacy policy</a>.</p><h2>Questions about a photograph</h2><p>If you appear in a photograph, or would like to discuss, correct, or remove an image, please contact <a href="mailto:xingtingwu@swin.edu.au">xingtingwu@swin.edu.au</a>.</p></div></div>'''
write_page('privacy.html','Photography & privacy','How research photographs and participant contributions are represented on this website.',privacy,'')
write_page('404.html','Page not found','The requested page could not be found.',f'<div class="wrap">{head("404 / A different path","Let’s find your way back.","This page may have moved. Explore the research or return to the homepage.","<div class=actions>"+link("index.html","Back to home","button")+link("research.html","Explore research")+"</div>")}</div>','')
(ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+u+'</loc></url>' for u in pages)+'</urlset>\n')
(ROOT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: https://www.xingtingwu.com/sitemap.xml\n')
(ROOT/'.nojekyll').touch()
print(f'Built {len(pages)+1} HTML pages and sitemap; {len(PAPERS)} publications.')
