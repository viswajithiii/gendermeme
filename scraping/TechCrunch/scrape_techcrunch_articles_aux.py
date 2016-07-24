from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtWebKit import *
from bs4 import BeautifulSoup
import sys

out_f = open('techcrunch_articles_scraped.txt','a')

class Render(QWebPage):
  def __init__(self, url):

    self.app = QApplication(sys.argv)
    QWebPage.__init__(self)
    self.loadFinished.connect(self._loadFinished)
    self.mainFrame().load(QUrl(url))
    self.app.exec_()

  def _loadFinished(self, result):
    self.frame = self.mainFrame()
    self.app.quit()

def get_article_info(page_url):
    print 'A'
    #result is a QString.
    r = Render(page_url)
    print 'B'
    result = r.frame.toHtml()
    #print str(result.toAscii())
    print 'C'
    result_str = str(result.toAscii())
    print result_str
    sp_result = result_str.splitlines()
    for line in sp_result:
        if line.startswith('var sranalytics'):
            article_info = eval(line[18:-1])
    soup = BeautifulSoup(result_str, "lxml")
    shares = soup.find("h5", "total-shares-count")
    shares = int(shares.get_text().replace(',','').replace('k','000').replace('.',''))

    # Assuming no techcrunch articles have more than 100k shares.
    if shares > 100000 and shares % 100 == 0:
        shares /= 10
    #html = lxml_html.fromstring(str(result.toAscil`i()))
    #print html
    article_info["shares"] = shares
    return article_info

a_info = get_article_info(sys.argv[1])
if a_info["shares"] == 0:
    out_f.write(sys.argv[1] + '\n')
else:
    out_f.write(repr(a_info) + '\n')
print a_info
