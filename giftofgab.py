import requests
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from bs4 import BeautifulSoup
import urllib
import re
import time


class Client(QWebEnginePage):
    def __init__(self, url, parent=None, app=None):
        if app is None:
            self.app = QApplication([])
        else:
            self.app = app
        super(Client, self).__init__(parent)
        self.loadFinished.connect(self.on_page_load)
        self.load(QUrl(url))
        self.page_html = None
        self.src = None
        self.app.exec_()
    def on_page_load(self):
        self.runJavaScript("document.getElementById('accepted-oral-papers')")
        time.sleep(3.5)
        self.toHtml(self.source)
    def source(self, src):
        self.src = src
        self.app.exit()


ICLR_URL = 'https://openreview.net/group?id=ICLR.cc/2019/Conference#%s'
ICLR_PAPER_URL = 'https://openreview.net/forum?id=%s'
ICLR_REV_URL = 'https://openreview.net%s'



def get_source(url, app):
    resp = Client(url, app=app)
    src = resp.src
    return src


def find_submissions(url, app):
    html = get_source(url, app)
    soup = BeautifulSoup(html, 'lxml')
    idlst = soup.findAll('li', {'class':'note'})
    ids = []
    for _id in idlst:
        ids.append(_id['data-id'])  
    return ids


def find_forums(url, app):
    html = get_source(url, app)
    soup = BeautifulSoup(html, 'lxml')
    title = soup.findAll('h2', {'class': 'note_content_title'})
    title = title[0].findNext('a').text
    revisions = soup.findAll('a', {'class': 'note_content_pdf item', 'href':re.compile('/revisions\?id=*')})
    revisionlist = []
    for revision in revisions:
        revisionlist.append(revision['href'])
    return title, revisionlist


def get_revision_ratings(url, app):
    html = get_source(url, app)
    soup = BeautifulSoup(html, 'lxml')
    notefields = soup.findAll('span', {'class': 'note_content_field'}, text=re.compile('Rating:*'))
    ratings = []
    for note in notefields:
        rating = int(note.parent.findNext('span', {'class': 'note_content_value'}).text.split(':')[0])
        ratings.append(rating)
    return ratings




app = QApplication([])
urls = [ICLR_URL % url for url in ['accepted-oral-papers', 'accepted-poster-papers', 'rejected-papers']]
avg_diffs = []
for url in urls:
    #print(url)
    submissions = find_submissions(url, app)
    for submission in submissions:
        title, revs = find_forums(ICLR_PAPER_URL % submission, app)
        rating_diffs = []
        for rev in revs:
            ratings = get_revision_ratings(ICLR_REV_URL % rev, app)
            if len(ratings) > 0:
                rating_diff = ratings[0] - ratings[-1]
                rating_diffs.append(rating_diff)
                #print('%i\t%s\t%s' % (rating_diff, submission, title))
        if len(rating_diffs) > 0:
            avg_diffs.append((title, submission, sum(rating_diffs)/len(rating_diffs)))

#for i in range(10):            
#    print('')
avg_diffs.sort(key=lambda x: x[1])
for title, sub, diff in avg_diffs[::-1]:
    print('%s\t%s\t%s' % (sub, diff, title))
