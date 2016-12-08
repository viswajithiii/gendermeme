from django.shortcuts import render
import sys
sys.path.append('../../')
from analysis.analysis import get_article_info


def index(request):
    if request.method == 'POST':
        print request.POST
        article_text = request.POST['articletext']
        article_info = get_article_info(article_text)
        mentions = article_info[0]
        num_quotes = {k: len(v) for k, v in article_info[1].iteritems()}
    return render(request, 'article_cruncher/index.html', locals())
