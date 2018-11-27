from django.db import models
from datetime import datetime
from elasticsearch_dsl import Date, Nested, Boolean, \
    analyzer, Completion, Keyword, Text, DocType, Integer
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer


connections.create_connection(hosts=['localhost'])


class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}


"""
filter=['lowercase']可以将搜索内容大小写进行转换,将ik_analyzer传递到suggest的参数里面，
不然会报错。可以尝试下直接Completion(analyzer='ik_max_word')
"""
ik_analyzer = CustomAnalyzer('ik_max_word', filter=['lowercase'])


class ArticleType(DocType):
    suggest = Completion(analyzer=ik_analyzer)
    title = Text(analyzer='ik_max_word')
    tags = Text(analyzer='ik_max_word')
    praise_nums = Integer()
    date = Date()
    comment_nums = Integer()
    collect_nums = Integer
    url_object_id = Keyword()
    image_urls = Keyword()
    image_paths = Keyword()

    class Meta:
        index = 'jobbole'
        doc_type = 'article'   # ArticleType对应type的名称


if __name__ == '__main__':
    ArticleType.init()

