import logging
import requests

import lxml.html

from person.models import Person
from parliament.models import PartyMember
from parliament.models import PoliticalParty

from voting.models import Bill
from voting.models import Vote

logger = logging.getLogger(__name__)

TWEEDEKAMER_URL = 'https://www.tweedekamer.nl'
SEARCH_URL = 'https://www.tweedekamer.nl/zoeken'


def get_voting_pages_for_dossier(dossier_nr):
    """ searches for votings within a dossier, returns a list of urls to pages with votings """
    params = {
        'qry': dossier_nr,
        'fld_prl_kamerstuk': 'Stemmingsuitslagen',
        'Type': 'Kamerstukken',
        'clusterName': 'Stemmingsuitslagen',
    }
    page = requests.get(SEARCH_URL, params)
    tree = lxml.html.fromstring(page.content)
    elements = tree.xpath('//div[@class="search-result-content"]/h3/a')
    voting_urls = []
    for element in elements:
        voting_url = TWEEDEKAMER_URL + element.get('href')
        voting_urls.append(voting_url)
    return voting_urls


def get_votings_for_page(votings_page_url):
    """ scrapes votings from a votings page (example: https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2016P10154) """
    page = requests.get(votings_page_url)
    tree = lxml.html.fromstring(page.content)
    result_elements = tree.xpath('//div[@class="search-result-content"]/p[@class="result"]/span')
    property_elements = tree.xpath('//div[@class="search-result-properties"]/p')
    document_ids = []
    for i in range(len(property_elements)):
        if i%2 == 0:
            document_ids.append(property_elements[i].text)
    assert len(document_ids) == len(result_elements)

    votings = []
    for i in range(len(result_elements)):
        voting = {
            'result': result_elements[i].text.replace('.', ''),
            'document_id': document_ids[i]
        }
        votings.append(voting)
    return votings


# def get_bills():
#     for i in range(0, 200):
#         url = 'http://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2015P' + "%05d" % (2266+i)
#         print('request url: ' + url)
#         page = requests.get(url)
#         tree = lxml.html.fromstring(page.content)
#
#         elements = tree.xpath('//div[@class="search-result-content"]/h3')
#
#         bills_urls = get_bill_urls(elements)
#
#         for url in bills_urls:
#             create_bill_from_url(url)
#
#
# def person_exists(forename, surname):
#     return Person.objects.filter(forename=forename, surname=surname).exists()
#
#
# def get_vote_results(votes):
#     options = dict()
#     for vote in votes:
#         if vote.decision in options:
#             options[vote.decision] += vote.party.seats
#         else:
#             options[vote.decision] = vote.party.seats
#     for option in options:
#         print(option + ' ' + str(options[option]))
#
#
# def create_bill_from_url(url):
#     url = url
#     page = requests.get('http://www.tweedekamer.nl' + url)
#     tree = lxml.html.fromstring(page.content)
#
#     # get bill title
#     original_title_element = tree.xpath('//div[@class="paper-description"]/span')
#     if original_title_element:
#         original_title = original_title_element[0].text
#     title = tree.xpath('//div[@class="paper-description"]/p')
#     if title:
#         title = title[0].text
#
#     document_url = tree.xpath('//div[@class="paper-description"]/a')
#     if document_url:
#         document_url = document_url[0].attrib['href']
#
#     # get the bill type
#     types = tree.xpath('//div[@class="paper-header"]/h1')
#     assert len(types) <= 1
#     if types:
#         bill_type = types[0].text
#     elif tree.xpath('//div[@class="bill-info"]/h2'):
#         bill_type = tree.xpath('//div[@class="bill-info"]/h2')[0].text
#
#     # get the bill author
#     authors = tree.xpath('//div[@class="paper-header"]/dl/dd/a')
#     if authors:
#         forename = authors[0].text.split()[0]
#         surname = authors[0].text.split()[-1]
#         member = PartyMember.find_member(forename, surname)
#         if not member:
#             logger.warning("Member model could not be found for: " + forename + ' ' + surname)
#             return None
#
#         bill = Bill.objects.create(title=title, original_title=original_title,
#                                    author=member, type=bill_type, document_url=document_url)
#         bill.save()
#     else:
#         logger.warning("No bill author found")
#         return None
#
#     # get the vote results
#     vote_results_table = tree.xpath('//div[@class="vote-result"]/table/tbody/tr')
#     for vote_html in vote_results_table:
#         create_vote_from_html_row(vote_html, bill)
#
#     return bill
#
#
# def create_vote_from_html_row(row, bill):
#     ncol = 0
#     details = ''
#     decision = ''
#
#     for column in row.iter():
#         if column.tag == 'td':
#             ncol += 1
#
#         if ncol == 1 and column.tag == 'a':
#             party_name = column.text
#             print(party_name)
#         elif ncol == 2:
#             number_of_seats = int(column.text)
#             print(number_of_seats)
#         elif ncol == 3 and column.tag == 'img':
#             decision = Vote.FOR
#         elif ncol == 4 and column.tag == 'img':
#             decision = Vote.AGAINST
#         elif ncol == 5 and column.tag == 'h4':
#             details = column.text
#             print(details)
#
#     party = PoliticalParty.get_party(party_name)
#     vote = Vote.objects.create(bill=bill, party=party, number_of_seats=number_of_seats,
#                                decision=decision, details=details)
#     vote.save()
#     return vote
#
#
# def get_bill_urls(elements):
#     vote_urls = []
#     for element in elements:
#         for child in element.iter():
#             if 'href' in child.attrib:
#                 print(child.attrib['href'])
#                 vote_urls.append(child.attrib['href'])
#     return vote_urls