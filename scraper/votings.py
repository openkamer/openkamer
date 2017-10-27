import logging
import requests
import re

import lxml.html
import dateparser

logger = logging.getLogger(__name__)

TWEEDEKAMER_URL = 'https://www.tweedekamer.nl'
SEARCH_URL = 'https://www.tweedekamer.nl/zoeken'


class Vote(object):
    AGAINST = 'AGAINST'
    FOR = 'FOR'
    NOVOTE = 'NOVOTE'

    def __init__(self, vote_table_row):
        self.vote_table_row = vote_table_row
        self.details = ''
        self.decision = ''
        self.number_of_seats = 0
        self.is_mistake = False
        self.create()

    def create(self):
        raise NotImplementedError


class VoteParty(Vote):
    def __init__(self, vote_table_row):
        self.party_name = ''
        super().__init__(vote_table_row)

    def create(self):
        ncol = 0
        for column in self.vote_table_row.iter():
            if column.tag == 'td':
                ncol += 1
            if ncol == 1:
                self.party_name = column.text
            elif ncol == 2:
                self.number_of_seats = int(column.text)
            elif ncol == 3 and column.tag == 'img':
                self.decision = Vote.FOR
            elif ncol == 4 and column.tag == 'img':
                self.decision = Vote.AGAINST
            elif ncol == 5 and column.tag == 'h4':
                self.details = column.text
                if 'niet deelgenomen' in self.details.lower():
                    self.decision = Vote.NOVOTE

    def __str__(self):
        return 'Vote: ' + self.party_name + ' (' + str(self.number_of_seats) + '): ' + self.decision


class VoteIndividual(Vote):
    MISTAKE = 'MISTAKE'

    def __init__(self, vote_table_row):
        self.parliament_member = ''
        super().__init__(vote_table_row)
        self.number_of_seats = 1

    def create(self):
        ncol = 0
        col_type = {3: Vote.FOR, 4: Vote.AGAINST, 5: Vote.NOVOTE, 6: VoteIndividual.MISTAKE}
        for column in self.vote_table_row.iter():
            if column.tag == 'td':
                ncol += 1
            if ncol == 2:
                self.parliament_member = column.text
            if 'class' in column.attrib and column.attrib['class'] == 'sel':
                if col_type[ncol] == VoteIndividual.MISTAKE:
                    self.is_mistake = True
                else:
                    self.decision = col_type[ncol]

    def __str__(self):
        return 'Vote: ' + self.parliament_member + ' : ' + self.decision


class VotingResult(object):
    def __init__(self, result_tree, date, url):
        self.result_tree = result_tree
        self.date = date
        self.votes = self.create_votes_from_table()
        self.url = url

    def get_property_elements(self):
        return self.result_tree.xpath('div[@class="search-result-properties"]/p')

    def get_table_rows_party(self):
        votes_table = self.get_votes_table()
        if votes_table is not None:
            return votes_table.xpath('tbody/tr')
        else:
            return []

    def get_table_rows_individual(self):
        votes_table = self.get_votes_table()
        if votes_table is not None:
            return votes_table.xpath('tbody/tr[@class="individual-vote" or @class="individual-vote last"]')
        else:
            return []

    def create_votes_from_table(self):
        votes = []
        if self.is_individual():
            table_rows = self.get_table_rows_individual()
            for row in table_rows:
                vote = VoteIndividual(row)
                votes.append(vote)
        else:
            table_rows = self.get_table_rows_party()
            for row in table_rows:
                vote = VoteParty(row)
                votes.append(vote)
        logger.info(str(len(votes)) + ' votes created!')
        return votes

    def get_votes_table(self):
        votes_tables = self.result_tree.xpath('div[@class="vote-result"]/table')
        if len(votes_tables):
            return self.result_tree.xpath('div[@class="vote-result"]/table')[0]
        else:
            logger.warning('no votes table found')
            return None

    def get_document_id(self):
        return self.get_property_elements()[0].text

    def get_dossier_id(self):
        document_id = self.get_document_id()
        if document_id is None:
            return None
        return document_id.split('-')[0]

    def get_document_id_without_rijkswet(self):
        document_id = self.get_document_id()
        if not document_id:
            return ''
        return re.sub("-\(R\d+\)", '', document_id)   # A 'Rijkswet' has the format '34158-(R2048)', removing the last part because there is no use for it (yet)

    def is_dossier_voting(self):
        """
        :returns whether the voting is for the whole dossier
        This is the case if the result has a document id and this document id is the dossier id, without sub-id.
        """
        return self.get_document_id() is not None and len(self.get_document_id_without_rijkswet().split('-')) == 1

    def is_individual(self):
        result_content_elements = self.result_tree.xpath('div[@class="search-result-content"]/p[@class="result"]/span')
        if result_content_elements and 'hoofdelijk' in result_content_elements[0].text.lower():
            return True
        result_content_elements = self.result_tree.xpath('div[@class="vote-result"]/p[@class="vote-type"]/span')
        if result_content_elements and 'hoofdelijk' in result_content_elements[0].text.lower():
            return True
        return False

    def get_result(self):
        result_content_elements = self.result_tree.xpath('div[@class="search-result-content"]/p[@class="result"]/span')
        if not result_content_elements:
            return ''
        return result_content_elements[0].text.replace('.', '')

    def __str__(self):
        return 'Voting for doc ' + self.get_document_id() + ', result: ' + self.get_result() + ', date: ' + str(self.date)

    def print_votes(self):
        for vote in self.votes:
            print(vote)


def get_votings_for_dossier(dossier_id):
    """ get votings for a given dossier """
    urls = get_voting_pages_for_dossier(dossier_id)
    results = []
    for url in urls:
        results += get_votings_for_page(url)
    return results


def get_voting_pages_for_dossier(dossier_id):
    """ searches for votings within a dossier, returns a list of urls to pages with votings """
    params = {
        'qry': dossier_id,
        'fld_prl_kamerstuk': 'Stemmingsuitslagen',
        'Type': 'Kamerstukken',
        'clusterName': 'Stemmingsuitslagen',
    }
    page = requests.get(SEARCH_URL, params, timeout=60)
    tree = lxml.html.fromstring(page.content)
    elements = tree.xpath('//div[@class="search-result-content"]/h3/a')
    voting_urls = []
    for element in elements:
        voting_urls.append(TWEEDEKAMER_URL + element.get('href'))
    return voting_urls


def get_votings_for_page(votings_page_url):
    """
    get votings from a given votings page
    :param votings_page_url: the url of the votings page, example: https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2016P10154
    :return: a list of VotingResult
    """
    page = requests.get(votings_page_url, timeout=60)
    tree = lxml.html.fromstring(page.content)

    content_reader = tree.xpath('//div[@id="content-reader"]/p')
    if len(content_reader) > 0 and content_reader[0].text is not None and 'tijdelijk niet beschikbaar' in content_reader[0].text:
        logger.warning('Votings page temporarily not available: ' + votings_page_url)
        return []

    date = tree.xpath('//p[@class="vote-info"]/span[@class="date"]')[0].text
    date = dateparser.parse(date).date()  # dateparser needed because of Dutch month names
    search_results = tree.xpath('//ul[@class="search-result-list reset"]/li')

    votings = []
    for search_result in search_results:
        result = VotingResult(search_result, date, votings_page_url)
        votings.append(result)
    return votings
