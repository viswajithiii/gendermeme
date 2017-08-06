from django.shortcuts import render
import sys
sys.path.append('../../')
from analysis.analysis import get_article_info


def index(request):

    return render(request, 'article_cruncher/home.html', locals())


def demo(request):

    if request.method == 'GET':
        article_text = 'Ann Smith and her husband Jim went to the movies. "It was okay," he said.'

    if request.method == 'POST':
        print request.POST
        article_text = request.POST['articletext']
        article_info = get_article_info(article_text, make_json=False)
        from pprint import pprint
        pprint(article_info)

        people_mentioned_info = []
        sources_info = []

        for _id, info_dict in article_info.iteritems():
            gender = info_dict['gender']
            if gender is None:
                gender = "Couldn't guess"
            elif type(gender) is tuple:
                gender = 'Unsure; most likely {}'.format(gender[0].lower())
            else:
                gender = gender.title()

            method = info_dict['gender_method']
            if method is None:
                method = "N/A"
            else:
                if method == "NAME_ONLY":
                    method = "From first name"
                elif method == "COREF":
                    method = "Using coreference with gendered pronoun"
                elif method == "HONORIFIC":
                    method = "Using Mr./Ms."

            name = info_dict['name']
            count = info_dict['num_times_mentioned']
            adjectives = ', '.join(info_dict['associated_adjs'])
            people_mentioned_info.append(
                (_id, name, count, gender, method, adjectives))

            is_speaker, reasons = info_dict['is_speaker']
            if is_speaker:
                sources_info.append(
                    (_id, name, '; '.join(reasons['Reasons']) + '.'))

        people_mentioned_info.sort(key=lambda x: x[0])
        sources_info.sort(key=lambda x: x[0])

    return render(request, 'article_cruncher/demo.html', locals())
