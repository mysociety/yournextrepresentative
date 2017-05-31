from __future__ import unicode_literals

MAPIT_BASE_URL = 'http://mapit.democracyclub.org.uk/'

SITE_OWNER = 'Democracy Club'
COPYRIGHT_HOLDER = 'Democracy Club Limited'


INSTALLED_APPS = [
    'bulk_adding',
    'uk_results',
]

TEMPLATE_CONTEXT_PROCESSORS = (
    "uk_results.context_processors.show_results_feature",
)

PEOPLE_LIABLE_TO_VANDALISM = {
    2811, # Theresa May
    1120, # Jeremy Corbyn
    4546, # Boris Johnson
    6035, # Paul Nuttall
    8372, # Nicola Sturgeon
    737, # Ruth Davidson

    34605, # Matt Furey-King (due to a vandalism incident)

    1528, # Janus Polenceus
    25402, # Giles Game

    # Below we include the person ID of anyone who is currently a minister.
    # This list was generated from:
    #
    #   https://github.com/mysociety/parlparse/blob/master/members/ministers-2010.json
    #
    # ... with this snippet of Python:
    #
    # import datetime, json
    # with open(ministers-2010.json') as f:
    #     ministers = json.load(f)
    # for m in ministers['memberships']:
    #     if not re.search(r'^(Minister|The Secretary of State|Deputy Prime Minister|The Prime Minister)', m.get('role', '')):
    #         continue
    #     today = str(date.today())
    #     if not (today >= m['start_date'] and today <= m.get('end_date', '9999-12-31')):
    #         continue
    #     i = Identifier.objects.filter(identifier=m['person_id']).first()
    #     if i is None:
    #         continue
    #     person = i.content_object
    #     print '    {0}, # {1} ({2})'.format(person.id, person.name, m['role'])

    2885, # David Davis (The Secretary of State for Exiting the European Union)
    212, # Alan Duncan (Minister of State)
    2832, # Michael Fallon (The Secretary of State for Defence)
    451, # Liam Fox (The Secretary of State for International Trade and President of the Board of Trade)
    918, # Nick Gibb (Minister of State (Department for Education))
    3486, # Damian Green (The Secretary of State for Work and Pensions)
    3445, # John Hayes (Minister of State (Department for Transport))
    2811, # Theresa May (The Prime Minister)
    3284, # Chris Grayling (The Secretary of State for Transport)
    3151, # David Jones (Minister of State (Department for Exiting the European Union))
    2534, # James Brokenshire (The Secretary of State for Northern Ireland)
    3238, # Ben Wallace (Minister of State (Home Office) (Security))
    4021, # Justine Greening (Minister for Women and Equalities)
    4021, # Justine Greening (The Secretary of State for Education)
    3155, # Jeremy Hunt (The Secretary of State for Health)
    1918, # Greg Clark (The Secretary of State for Business, Energy and Industrial Strategy )
    1592, # David Mundell (The Secretary of State for Scotland)
    1104, # Edward Timpson (Minister of State (Department for Education))
    1303, # Karen Bradley (The Secretary of State for Culture, Media and Sport)
    1923, # Alun Cairns (The Secretary of State for Wales)
    3737, # Matthew Hancock (Minister of State (Department for Culture, Media and Sport) (Digital Policy))
    1326, # Priti Patel (The Secretary of State for International Development)
    3741, # Robert Halfon (Minister of State (Department of Education) (Apprenticeships and Skills))
    519, # Amber Rudd (The Secretary of State for the Home Department)
    2875, # Andrea Leadsom (The Secretary of State for Environment, Food and Rural Affairs)
    349, # Sajid Javid (The Secretary of State for Communities and Local Government)
    4881, # Gavin Barwell (Minister of State (Department for Communities and Local Government) (Housing, Planning and London))
    3533, # Brandon Lewis (Minister of State (Home Office) (Policing and the Fire Service))
    2204, # Jo Johnson (Minister of State (Department for Education) (Universities and Science) (Joint with the Department for Business, Energy and Industrial Strategy))
    2204, # Jo Johnson (Minister of State (Department for Business, Energy and Industrial Strategy) (Universities and Science) (Joint with the Department for Education))
}
