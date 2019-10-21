# StringMatch
Package requirement: pyjarowinkler (pip install pyjarowinkler)

# StringMatch.py
StringMatch.py is the match program

The are three test instances in this program. The first one is：

```python
query_tagging(args.query_path, args.log_path, args.tagged_query_path, args.algorithm, args.threshold)
```
The **query_tagging** funcation takes a list of queries, the path of the click log, and the path of the outputed tagged queires as input. "jaro-winkler" is the algorithm to calculate the similarity and 0.9 is the threshold. If the similarity score of the two words is equal or bigger than 0.9, then the two words are considered same.

# bestbuy_click_log.json
This is the bestbuy click log. The attributes are collected from the [Best Buy E-commerce NER dataset](https://dataturks.com/projects/Mohan/Best%20Buy%20E-commerce%20NER%20dataset). The corresponding queries are in the bestbuy_query.txt.

# bestbuy_query.txt
This is the bestbuy query which is collected from the [Best Buy E-commerce NER dataset](https://dataturks.com/projects/Mohan/Best%20Buy%20E-commerce%20NER%20dataset).
