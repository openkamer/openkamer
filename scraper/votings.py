
import urllib.request
import lxml.html

from datetime import datetime


def main():
    bills = []
    for i in range(0, 200):
        url = 'http://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2015P' + "%05d" % (2266+i)
        print('request url: ' + url)
        response = urllib.request.urlopen(url)
        tree = lxml.html.fromstring( str(response.read()) )

        elements = tree.xpath('//div[@class="search-result-content"]/h3')

        bills_urls = get_bill_urls(elements)

        for url in bills_urls:
            bill = Bill()
            bill.from_url(url)
            bills.append(bill)
            print(bill)

    for bill in bills:
        print(bill)


class Member():
    def __init__(self):
        self.name = 'undefined'
        self.party = Party()


class Bill():
    def __init__(self):
        self.title = 'undefined'
        self.original_title = 'undefined'
        self.type = 'undefined'  # [Amendement, Motie, Wetsvoorstel]
        self.date = datetime.now()
        self.votes = []
        self.url = ''
        self.author = Member()
        self.document_url = 'undefined'

    def get_vote_results(self):
        options = dict()
        for vote in self.votes:
            if vote.decision in options:
                options[vote.decision] += vote.party.seats
            else:
                options[vote.decision] = vote.party.seats
        for option in options:
            print(option + ' ' + str(options[option]))

    def from_url(self, url):
        self.url = url
        response = urllib.request.urlopen('http://www.tweedekamer.nl' + url)
        tree = lxml.html.fromstring(str(response.read()))

        # get bill title
        original_title = tree.xpath('//div[@class="paper-description"]/span')
        if original_title:
            self.original_title = original_title[0].text
        title = tree.xpath('//div[@class="paper-description"]/p')
        if title:
            self.title = title[0].text

        document_url = tree.xpath('//div[@class="paper-description"]/a')
        if document_url:
            self.document_url = document_url[0].attrib['href']
            print(self.document_url)

        # get the bill type
        types = tree.xpath('//div[@class="paper-header"]/h1')
        if types:
            self.type = types[0].text
        elif tree.xpath('//div[@class="bill-info"]/h2'):
            self.type = tree.xpath('//div[@class="bill-info"]/h2')[0].text

        # get the bill author
        authors = tree.xpath('//div[@class="paper-header"]/dl/dd/a')
        for author in authors:
            print(author.text)
            print(author.attrib['href'])
            self.author.name = author.text

        # get the vote results
        vote_results_table = tree.xpath('//div[@class="vote-result"]/table/tbody/tr')
        for vote_html in vote_results_table:
            vote = Vote()
            self.votes.append(vote.from_html_row(vote_html))
        assert len(types) <= 1

    def __str__(self):
        summary = ''
        summary += 'Type: ' + self.type + '\n'
        summary += 'Title: ' + self.title + '\n'
        summary += 'Original title: ' + self.original_title + '\n'
        self.get_vote_results()
        for vote in self.votes:
            summary += str(vote) + '\n'
        return summary


class Party():
    def __init__(self):
        self.name = ''
        self.seats = 0
        self.url = 'undefined'


class Vote():
    def __init__(self):
        self.party = Party()
        self.decision = ''
        self.details = ''

    def from_html_row(self, row):
        ncol = 0
        for column in row.iter():
            if column.tag == 'td':
                ncol += 1

            if ncol == 1 and column.tag == 'a':
                self.party.name = column.text
            elif ncol == 2:
                self.party.seats = int(column.text)
            elif ncol == 3 and column.tag == 'img':
                self.decision = 'VOOR'
            elif ncol == 4 and column.tag == 'img':
                self.decision = 'TEGEN'
            elif ncol == 5 and column.tag == 'h4':
                self.details = column.text
        return self

    def __str__(self):
        summary = self.party.name + ' (' + str(self.party.seats) + ')' + ': ' + self.decision
        if self.details:
            summary += ' (' + self.details + ')'
        return summary


def get_bill_urls(elements):
    vote_urls = []
    for element in elements:
        for child in element.iter():
            if 'href' in child.attrib:
                print(child.attrib['href'])
                vote_urls.append(child.attrib['href'])
    return vote_urls


if __name__ == '__main__':
    main()