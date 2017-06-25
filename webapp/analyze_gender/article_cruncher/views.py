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
        adj_info = article_info[4]

        people_mentioned_info = []
        for person, mention_info in mentions.iteritems():
            count, (gender, method) = mention_info
            if gender is None:
                gender = "Couldn't guess"
            elif type(gender) is tuple:
                gender = 'Unsure; most likely {}'.format(gender[0].lower())
            else:
                gender = gender.title()

            if method is None:
                method = "N/A"
            else:
                if method == "NAME_ONLY":
                    method = "From first name"
                elif method == "COREF":
                    method = "Using coreference with gendered pronoun"
                elif method == "HONORIFIC":
                    method = "Using Mr./Ms."
            people_mentioned_info.append((person, count, gender, method,
                                          ', '.join(a[0] for a in
                                                    adj_info[person])))

        people_mentioned_info.sort(key=lambda x: x[1], reverse=True)

        num_quotes = {k: len(v) for k, v in article_info[1].iteritems()}
        associated_verbs = article_info[2]

        sources = article_info[3]
        sources_info = []
        for person, reasons in sources.iteritems():
            if len(reasons) == 0:
                continue
            sources_info.append((person, '. '.join(reasons) + '.'))

        sources_info.sort(key=lambda x: mentions[x[0]][0], reverse=True)

    return render(request, 'article_cruncher/index.html', locals())
