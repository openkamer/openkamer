
import urllib.request
import lxml.html

LOCAL_TEST = False


def main():
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

        vote_urls = get_vote_url(elements)

        for url in vote_urls:
            votes = parse_voting(url)
            for vote in votes:
                print(vote)


class Vote():
    def __init__(self):
        self.party = ''
        self.seats = 0
        self.decision = ''
        self.details = ''

    def from_html_row(self, row):
        ncol = 0
        for column in row.iter():
            if column.tag == 'td':
                ncol += 1

            if ncol == 1 and column.tag == 'a':
                self.party = column.text
            elif ncol == 2:
                self.seats = int(column.text)
            elif ncol == 3 and column.tag == 'img':
                self.decision = 'VOOR'
            elif ncol == 4 and column.tag == 'img':
                self.decision = 'TEGEN'
            elif ncol == 5 and column.tag == 'h4':
                self.details = column.text
        return self

    def __str__(self):
        summary = self.party + ' (' + str(self.seats) + ')' + ': ' + self.decision
        if self.details:
            summary += ' (' + self.details + ')'
        return summary


def parse_voting(url):
    if LOCAL_TEST:
        test_document_url = '2015D04817.html'
        with open(test_document_url, 'r') as filein:
            html_file = filein.read()
            tree = lxml.html.fromstring(html_file)
    else:
        response = urllib.request.urlopen('http://www.tweedekamer.nl' + url)
        tree = lxml.html.fromstring(str(response.read()))

    table = tree.xpath('//div[@class="vote-result"]/table/tbody/tr')
    votes = []
    for vote_html in table:
        vote = Vote()
        votes.append(vote.from_html_row(vote_html))
    return votes


def get_vote_url(elements):
    vote_urls = []
    for element in elements:
        for child in element.iter():
            if 'href' in child.attrib:
                print(child.attrib['href'])
                vote_urls.append(child.attrib['href'])
    return vote_urls


if __name__ == '__main__':
    main()