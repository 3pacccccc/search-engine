import json
from datetime import datetime
import redis

from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse
from elasticsearch import Elasticsearch

from search.models import ArticleType


client = Elasticsearch(hosts='127.0.0.1')
redis_cli = redis.StrictRedis()


class IndexView(View):
    def get(self, request):
        topn_search = redis_cli.zrevrangebyscore('search_keywords_set', '+inf', '-inf', start=0, num=5)  # 取出热门前五的搜索
        return render(request, 'index.html', {
            'topn_search': topn_search,
        })


class SearchSuggest(View):
    def get(self, request):
        key_words = request.GET.get('s', '')
        s_type = request.GET.get('s_type', 'article')
        re_datas = []
        if key_words:
            s = ArticleType.search()
            s = s.suggest('my-suggest', key_words, completion={
                "field": "suggest", "fuzzy": {
                    "fuzziness": 2
                },
                "size": 10     # 返回的数据个数
            })
            suggestions = s.execute_suggest()
            for match in getattr(suggestions, 'my-suggest')[0].options:
                source = match._source
                re_datas.append(source['title'])

            return HttpResponse(json.dumps(re_datas), content_type='application/json')


class SearchView(View):
    def get(self, request):
        site = '伯乐在线'
        key_words = request.GET.get('q', '')

        redis_cli.zincrby('search_keywords_set', key_words)   # 关键词次数+1

        topn_search = redis_cli.zrevrangebyscore('search_keywords_set', '+inf', '-inf', start=0, num=5)  # 取出热门前五的搜索

        page = request.GET.get('p', 1)
        try:
            page = int(page)
        except:
            page = 1

        jobbole_count = redis_cli.get('jobbole_count')
        start_time = datetime.now()
        response = client.search(
            index='jobbole',
            body={
                "query": {
                    "multi_match": {
                        "query": key_words,
                        "fields": ['title', 'tags', 'content']
                    }
                },
                "from": (page-1)*10,
                "size": 10,
                "highlight": {
                    "pre_tags": ['<span class="keyWord">'],
                    "post_tags": ['</span>'],
                    "fields": {
                        'title': {},
                        'content': {},
                    }
                }
            }
        )
        end_time = datetime.now()
        last_time = (end_time - start_time).total_seconds()
        time = response['took'] * 0.001

        total_nums = response['hits']['total']
        if (page % 10) > 0:
            page_nums = int(total_nums/10) + 1
        else:
            page_nums = int(total_nums/10)
        hit_list = []
        for hit in response['hits']['hits']:
            hit_dict = {}
            if 'title' in hit['highlight']:
                hit_dict['title'] = ''.join(hit['highlight']['title'])
            else:
                hit_dict['title'] = hit['_source']['title']
            if 'content' in hit['highlight']:
                hit_dict['content'] = ''.join(hit['highlight']['content'])[:500]
            else:
                hit_dict['content'] = hit['_source']['content'][:500]

            hit_dict['create_date'] = hit['_source']['date']
            hit_dict['url'] = hit['_source']['url']
            hit_dict['score'] = hit['_score']

            hit_list.append(hit_dict)

        return render(request, 'result.html', {
            'all_hits': hit_list,
            'key_words': key_words,
            'total_nums': total_nums,
            'page': page,
            'page_nums': page_nums,
            'last_time': last_time,
            'time': time,
            'jobbole_count': jobbole_count,
            'topn_search': topn_search,
            'site': site,
        })