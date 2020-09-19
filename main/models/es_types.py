# -*- coding: utf-8 -*-
__author__ = 'bobby'

from datetime import datetime
from elasticsearch_dsl import DocType, Date, Nested, Boolean, \
    analyzer, InnerObjectWrapper, Completion, Keyword, Text, Integer

from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

from elasticsearch_dsl.connections import connections

connections.create_connection(hosts=["localhost"])


class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}


ik_analyzer = CustomAnalyzer("ik_max_word", filter=["lowercase"])


class ArticleQuestionType(DocType):
    suggest = Completion(analyzer=ik_analyzer)
    question_id = Keyword()
    title = Text(analyzer="ik_max_word")
    content = Keyword()
    answer_num = Integer()
    source = Keyword()
    url = Keyword()

    class Meta:
        index = "article"
        doc_type = "question"


if __name__ == "__main__":
    ArticleQuestionType.init()
