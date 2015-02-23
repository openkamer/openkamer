
import urllib.request
import lxml.html

from datetime import datetime

LOCAL_TEST = False


def main():

    bills = []
    for i in range(0, 200):
        if LOCAL_TEST:
            with open('2015P02267.html', 'r') as filein:
                html_file = filein.read()
                tree = lxml.html.fromstring( html_file )
        else:
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


class Bill():
    def __init__(self):
        self.type = 'Undefined'  # [Amendement, Motie, Wetsvoorstel]
        self.date = datetime.now()
        self.votes = []
        self.url = ''

    def from_url(self, url):
        self.url = url
        if LOCAL_TEST:
            test_document_url = '2015D04817.html'
            with open(test_document_url, 'r') as filein:
                html_file = filein.read()
                tree = lxml.html.fromstring(html_file)
        else:
            response = urllib.request.urlopen('http://www.tweedekamer.nl' + url)
            tree = lxml.html.fromstring(str(response.read()))

        types = tree.xpath('//div[@class="paper-header"]/h1')

        if types:
            self.type = types[0].text
        else:
            types = tree.xpath('//div[@class="bill-info"]/h2')
            self.type = types[0].text

        vote_results_table = tree.xpath('//div[@class="vote-result"]/table/tbody/tr')
        for vote_html in vote_results_table:
            vote = Vote()
            self.votes.append(vote.from_html_row(vote_html))

        assert len(types) <= 1

    def __str__(self):
        summary = ''
        summary += 'Type: ' + self.type + '\n'
        for vote in self.votes:
            summary += str(vote) + '\n'
        return summary


class Party():
    def __init__(self):
        self.name = ''
        self.seats = 0


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