# StringMatch
Package requirement: pyjarowinkler (pip install pyjarowinkler)

# StringMatch.py
StringMatch.py is the match program.

```python
query_tagging(args.query_path, args.log_path, args.tagged_query_path, args.algorithm, args.threshold)
```
+ args.query_path: the path of the query file the format of which is txt.
+ args.log_path: the path of the click log the format of which is json.
+ args.tagged_query_path: the path of the outputed tagged queires. The format of the file is txt.
+ args.algorithm: select "jaro-winkler" or "trigram". The default value is "jaro-winkler. 
+ args.threshold: if similarity score calculated by the "jaro-winkler" or "trigram" algorithm equals or bigger than the threshold, the two words are considered same. Threshold is a float value between 0 and 1.

# StringMatchClick.py
In StringMatchClick.py, if the similarity score of two words is bigger than the threshold, we will label the word with the corresponding label and the weighted similarity score which is defined by similarity score * click time. Finally, we will output the labels with the corresponding weighted similarity scores.

The queries and click logs are in one file the format of which is like this:
```
{
  "query1": {
               "attribute1": [{"value1": click times}, {"value2": click times}, ...],
               "attribute2": [{"value1": click times}, {"value2": click times}, ...],
               ...
            },
  "query2": {
               "attribute1": [{"value1": click times}, {"value2": click times}, ...],
               "attribute2": [{"value1": click times}, {"value2": click times}, ...],
               ...
            },
   ...
}
```
# bestbuy_click_log.json
This is the bestbuy click log. The attributes are collected from the [Best Buy E-commerce NER dataset](https://dataturks.com/projects/Mohan/Best%20Buy%20E-commerce%20NER%20dataset). The corresponding queries are in the bestbuy_query.txt.

# bestbuy_query.txt
This is the bestbuy query which is collected from the [Best Buy E-commerce NER dataset](https://dataturks.com/projects/Mohan/Best%20Buy%20E-commerce%20NER%20dataset).
