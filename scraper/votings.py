import logging
import requests

import lxml.html

logger = logging.getLogger(__name__)

TWEEDEKAMER_URL = 'https://www.tweedekamer.nl'
SEARCH_URL = 'https://www.tweedekamer.nl/zoeken'


class Vote(object):
    def __init__(self, vote_table_row):
        self.vote_table_row = vote_table_row
        self.details = ''
        self.decision = ''
        self.number_of_seats = 0
        self.party_name = ''
        self.create()

    def create(self):
        ncol = 0

        for column in self.vote_table_row.iter():
            if column.tag == 'td':
                ncol += 1
            if ncol == 1 and column.tag == 'a':
                self.party_name = column.text
            elif ncol == 2:
                self.number_of_seats = int(column.text)
            elif ncol == 3 and column.tag == 'img':
                self.decision = 'FOR'
            elif ncol == 4 and column.tag == 'img':
                self.decision = 'AGAINST'
            elif ncol == 5 and column.tag == 'h4':
                self.details = column.text

    def __str__(self):
        return 'Vote: ' + self.party_name + ' (' + str(self.number_of_seats) + '): ' + self.decision


class VotingResults(object):
    def __init__(self, result_tree):
        print('create VotingResults')
        self.result_tree = result_tree
        self.votes = self.create_votes_from_table()

    def __str__(self):
        return 'Voting for doc ' + self.get_document_id() + ', result: ' + self.get_result()

    def print_votes(self):
        for vote in self.votes:
            print(vote)

    def get_property_elements(self):
        return self.result_tree.xpath('div[@class="search-result-properties"]/p')

    def get_table_rows(self):
        votes_table = self.get_votes_table()
        if votes_table is not None:
            return votes_table.xpath('tbody/tr')
        else:
            return []

    def create_votes_from_table(self):
        table_rows = self.get_table_rows()
        print('table rows: ' + str(len(table_rows)))
        votes = []
        for row in table_rows:
            vote = Vote(row)
            votes.append(vote)
        return votes

    def get_votes_table(self):
        votes_tables = self.result_tree.xpath('div[@class="vote-result"]/table')
        if len(votes_tables):
            return self.result_tree.xpath('div[@class="vote-result"]/table')[0]
        else:
            print('WARNING: no votes table found')
            return None

    def get_document_id(self):
        return self.get_property_elements()[0].text

    def get_date(self):
        return self.get_property_elements()[1].text

    def get_result(self):
        result_content_elements = self.result_tree.xpath('div[@class="search-result-content"]/p[@class="result"]/span')
        return result_content_elements[0].text.replace('.', '')


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
    search_results = tree.xpath('//ul[@class="search-result-list reset"]/li')

    votings = []
    for search_result in search_results:
        result = VotingResults(search_result)
        votings.append(result)
    return votings
