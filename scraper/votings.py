import logging
logger = logging.getLogger(__name__)

from datetime import datetime
import requests

import lxml.html

from voting.models import Bill
from voting.models import Member
from voting.models import Party
from voting.models import Vote


def get_bills():
    for i in range(0, 200):
        url = 'http://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2015P' + "%05d" % (2266+i)
        print('request url: ' + url)
        page = requests.get(url)
        tree = lxml.html.fromstring(page.content)

        elements = tree.xpath('//div[@class="search-result-content"]/h3')

        bills_urls = get_bill_urls(elements)

        for url in bills_urls:
            create_bill_from_url(url)


def create_members():
    members = []
    url = 'http://www.tweedekamer.nl/kamerleden/alle_kamerleden'
    page = requests.get(url)
    tree = lxml.html.fromstring(page.content)

    rows = tree.xpath("//tbody/tr")

    for row in rows:
        columns = row.xpath("td")
        if len(columns) == 8:
            surname = columns[0][0].text.split(',')[0]
            print(surname)
            prefix = columns[0][0].text.split('.')[-1].strip()
            forename = columns[1][0].text

            if member_exists(forename, surname):
                continue

            party_name = columns[2][0].text
            party = get_or_create_party(party_name)
            residence = columns[3][0].text
            # if not residence:
            #     residence = ''
            age = columns[4][0][0].text
            sex = columns[5][0].text
            assert age is not None
            if sex == 'Man':
                sex = Member.MALE
            elif sex == 'Vrouw':
                sex = Member.FEMALE
            print(age)
            member = Member.objects.create(forename=forename,
                                           surname=surname,
                                           surname_prefix=prefix,
                                           sex=sex,
                                           residence=residence,
                                           party=party)
            members.append(member)
            print("new member: " + str(member))


def member_exists(forename, surname):
    return Member.objects.filter(forename=forename, surname=surname).exists()


def get_or_create_party(party_name):
    party = Party.objects.filter(name=party_name)
    if party.exists():
        return party[0]

    party = Party.objects.create(name=party_name, seats=0)
    party.save()
    return party


def get_vote_results(votes):
    options = dict()
    for vote in votes:
        if vote.decision in options:
            options[vote.decision] += vote.party.seats
        else:
            options[vote.decision] = vote.party.seats
    for option in options:
        print(option + ' ' + str(options[option]))


def create_bill_from_url(url):
    url = url
    page = requests.get('http://www.tweedekamer.nl' + url)
    tree = lxml.html.fromstring(page.content)

    # get bill title
    original_title_element = tree.xpath('//div[@class="paper-description"]/span')
    if original_title_element:
        original_title = original_title_element[0].text
    title = tree.xpath('//div[@class="paper-description"]/p')
    if title:
        title = title[0].text

    document_url = tree.xpath('//div[@class="paper-description"]/a')
    if document_url:
        document_url = document_url[0].attrib['href']

    # get the bill type
    types = tree.xpath('//div[@class="paper-header"]/h1')
    assert len(types) <= 1
    if types:
        bill_type = types[0].text
    elif tree.xpath('//div[@class="bill-info"]/h2'):
        bill_type = tree.xpath('//div[@class="bill-info"]/h2')[0].text

    # get the bill author
    authors = tree.xpath('//div[@class="paper-header"]/dl/dd/a')
    if authors:
        forename = authors[0].text.split()[0]
        surname = authors[0].text.split()[-1]
        member = Member.find_member(forename, surname)
        if not member:
            logger.warning("Member model could not be found for: " + forename + ' ' + surname)
            return None

        bill = Bill.objects.create(title=title, original_title=original_title,
                                   author=member, type=bill_type, document_url=document_url)
        bill.save()
    else:
        logger.warning("No bill author found")
        return None

    # get the vote results
    vote_results_table = tree.xpath('//div[@class="vote-result"]/table/tbody/tr')
    for vote_html in vote_results_table:
        create_vote_from_html_row(vote_html, bill)

    return bill


def create_vote_from_html_row(row, bill):
    ncol = 0
    details = ''
    decision = ''

    for column in row.iter():
        if column.tag == 'td':
            ncol += 1

        if ncol == 1 and column.tag == 'a':
            party_name = column.text
            print(party_name)
        elif ncol == 2:
            number_of_seats = int(column.text)
            print(number_of_seats)
        elif ncol == 3 and column.tag == 'img':
            decision = Vote.FOR
        elif ncol == 4 and column.tag == 'img':
            decision = Vote.AGAINST
        elif ncol == 5 and column.tag == 'h4':
            details = column.text
            print(details)

    party = get_or_create_party(party_name)
    vote = Vote.objects.create(bill=bill, party=party, number_of_seats=number_of_seats,
                               decision=decision, details=details)
    vote.save()
    return vote


def get_bill_urls(elements):
    vote_urls = []
    for element in elements:
        for child in element.iter():
            if 'href' in child.attrib:
                print(child.attrib['href'])
                vote_urls.append(child.attrib['href'])
    return vote_urls