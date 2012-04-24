"""
Query JIRA via XMLRPC and produce a pdf of cards.
"""

import xmlrpclib, getpass
from reportlab.lib.units import inch 
from reportlab.pdfgen.canvas import Canvas

# this needs to be refactored!
import cardlayout

from datetime import datetime

host = raw_input('Please specify the JIRA host (SSL is assumed): ')
username = raw_input('Please enter your JIRA username: ')
password = getpass.getpass('Please enter your JIRA password: ')

jira = xmlrpclib.ServerProxy('https://%s:%s@%s/jira/rpc/xmlrpc' % (host, username, password), use_datetime=True)

auth = jira.jira1.login(username, password)

cards = jira.jira1.getIssuesFromFilter(auth, '12328')

output = "card.pdf"
    
# 5 x 3 index card size
page_width = 5*inch
page_height = 3*inch
canvas = Canvas(output, pagesize=(page_width, page_height))

# retrieve user details, but only once    
users = {}

issue_types = jira.jira1.getIssueTypes(auth)
types = {}
for issue_type in issue_types:
    types[issue_type['id']] = issue_type

for card in cards:
    import ipdb; ipdb.set_trace()
    
    reporter = users.get(card['reporter'], None)
    
    if not reporter:
        reporter = jira.jira1.getUser(auth, card['reporter'])
        users[card['reporter']] = reporter
    
    
    # add_card(canvas, story_info, page_width, page_height);
    story_info = {
        'summary': card['summary'],
        'detail': card['description'],
        'id': card['key'],
        'type': types[card['type']]['name'],
        'reporter': reporter['fullname'],
        'date': datetime.strptime(card['created'], "%Y-%m-%d %H:%M:%S.0"),
        'icon': 'agt_utilities.png',
    }
    
    story_info['formatted_date'] = story_info['date'].strftime('%m/%d @ %I:%M %p')
    
    cardlayout.add_card(canvas, story_info, page_width, page_height);
    
canvas.save()
