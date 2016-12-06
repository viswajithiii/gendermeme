from django.shortcuts import render
import sys
sys.path.append('../../')
from analysis.analysis import get_article_info


def index(request):
    if request.method == 'POST':
        print request.POST
        article_info = get_article_info(request.POST['articletext'])
        mentions = article_info[0]
        num_quotes = article_info[1]
    return render(request, 'article_cruncher/index.html', locals())
