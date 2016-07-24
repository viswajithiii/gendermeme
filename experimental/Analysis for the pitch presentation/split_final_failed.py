with open('techcrunch_article_info_failed_poorna.txt', 'r') as in_f:
    with open('techcrunch_articles_final3.txt', 'a') as out_f1:
        with open('techcrunch_articles_failed3.txt', 'a') as out_f2:
            for line in in_f:
                if line[0] == '{':
                    out_f1.write(line)
                else:
                    out_f2.write(line)
