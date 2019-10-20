# StringMatch

# StringMatch.py
StringMatch.py is the match program

```python
"""
    test 1: this test is to test whether the labels and segmentation are right or not
    query_１：a list of queries to be tested
    log_path_1: the path of the click log
    query_with_tag_path_1: the output tagged queries
    """
    query_1 = ["tesla red model x",
               "camry hybrid 2020 white",
               "fullsize ford blue electronic",
               "Honda civic sports black",
               "compact economy blue car ford",
               "e Class model X G63 null null Model y model 3",
               "e clbss mddel x b63 null null mmdel y moael 3"]
    log_path_1 = "click_log_1.json"
    query_with_tag_path_1 = "click_log_1.txt"
    query_tagging(query_1, log_path_1, query_with_tag_path_1, "jaro-winkler", 0.9)
    """
    test 2: this test is to test the multi labels
    query_2：a list of queries to be tested
    log_path_2: the path of the click log
    query_with_tag_path_2: the output tagged queries
    """
    query_2 = ["blue desk bird and red lobster"]
    log_path_2 = "special_case.json"
    query_with_tag_path_2 = "special_case.txt"
    query_tagging(query_2, log_path_2, query_with_tag_path_2, "jaro-winkler", 0.9)
    """
    test 3:
    BestBuy_query：a list of queries from Bestbuy dataset to be tested
    BestBuy_log: the path of the click log
    query_with_tag_path_3: the output tagged queries
    """
    bestbuy_query = ['apple watch', 'ipad', 'apple watch series 3', 'apple watch series 2',...]
    bestbuy_log = "bestbuy_click_log.json"
    query_with_tag_path_3 = "bestbuy_query.txt"
    query_tagging(bestbuy_query, bestbuy_log, query_with_tag_path_3, "jaro-winkler", 0.9)
```
