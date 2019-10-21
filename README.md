# StringMatch
Package requirement: pyjarowinkler (pip install pyjarowinkler)

# StringMatch.py
StringMatch.py is the match program

The are three test instances in this program. The first one is：

```python
query_tagging(args.query_path, args.log_path, args.tagged_query_path, args.algorithm, args.threshold)
```
The **query_tagging** funcation takes a list of queries, the path of the click log, and the path of the outputed tagged queires as input. "jaro-winkler" is the algorithm to calculate the similarity and 0.9 is the threshold. If the similarity score of the two words is equal or bigger than 0.9, then the two words are considered same.

# click_log_1.json
This is the first test click log. The corresponding query is:
```python
query_1 = ["tesla red model x",
           "camry hybrid 2020 white",
           "fullsize ford blue electronic",
           "Honda civic sports black",
           "compact economy blue car ford",
           "e Class model X G63 null null Model y model 3",
           "e clbss mddel x b63 null null mmdel y moael 3"]
```
# special_case.json
This is the second test click log. It is to test the special case: different attributes have the same attribute values. The corresponding query is:
```python
query_2 = ["blue desk bird and red lobster"]
```
# bestbuy_click_log.json
This is the third test click log. The attributes are collected from the [Best Buy E-commerce NER dataset](https://dataturks.com/projects/Mohan/Best%20Buy%20E-commerce%20NER%20dataset). The corresponding queries are also from this dataset.
