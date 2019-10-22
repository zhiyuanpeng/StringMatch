"""
This program is to label the search query with the corresponding attributes from the click logs
"""

import json
import argparse
from pyjarowinkler import distance  # pip install pyjarowinkler


def trigram(word):
    """
    Args:
        word: the input the word
    Returns:
        trigram_list: a list contains the trigrams of the input string
    """
    trigram_list = []
    if len(word) <= 3:
        trigram_list.append(word)
    else:
        for index in range(len(word)):
            if index <= len(word) - 3:
                trigram_list.append(word[index:index + 3])
    return trigram_list


def similarity(w1, w2, algorithm, threshold):
    """Computes the trigrams similarity of two input words w1 and w2
        Args:
            w1: the first input word
            w2: the second input word
            algorithm: the name of the algorithm to calculate the similarity
            threshold: the threshold to determine whether two word are similar or not
        Returns:
            1: two words are similar
            0: two words are not similar
    """
    if algorithm == "trigram":
        # lower w1 and w2
        w1_trigram = set(trigram(w1.lower()))
        w2_trigram = set(trigram(w2.lower()))
        score = len(w1_trigram.intersection(w2_trigram)) / len(w1_trigram.union(w2_trigram))
    elif algorithm == "jaro-winkler":
        score = distance.get_jaro_distance(w1, w2, winkler=True, scaling=0.1)
    # for test
    # print(score)
    return score >= threshold


def string_match(query, logs, algorithm, threshold):
    """label the input query with the predefined attributes
        Args:
            query: a list of query to be labeled
            logs: a json file path which contains the attributes and the corresponding value
            algorithm: select the algorithm of similarity
            threshold: the threshold of the similarity algorithm
        Returns:
            label_list: a list contains the corresponding labels of each word of the input query
            Each element of label_list is a set
    """
    # convert the string to list
    query_list = query.strip("\n").split(" ")
    # store the labels in label_list
    label_list = [set() for _ in range(len(query_list))]
    # cache the label_list
    label_list_memo = [set() for _ in range(len(query_list))]
    # the final returned label list
    returned_label_list = []
    # visit each attribute in logs
    for key in logs:
        # visit each value of the attribute
        for value in logs[key]:
            # each value of logs[key] may be composed of two or more words, to match the value, use DP
            value_list = value.split(" ")
            # Top down DP
            # allocate memory
            memo = [[0] * (len(value_list) + 1) for _ in range(len(query_list) + 1)]
            # visit each word of the query, from the last one to the first one
            for i in range(0, len(query_list), 1):
                # visit each word of the attributes[key] from the last one to the first one
                for j in range(0, len(value_list), 1):
                    if similarity(query_list[i], value_list[j], algorithm, threshold):
                        memo[i + 1][j + 1] = memo[i][j] + 1
                        if memo[i][j] == 0:
                            # memo[i][j] == 0, so, it is the beginning of the label
                            label_list_memo[i].add("B-" + key)
                        else:
                            # memo[i][j] != 0, so, it is not the beginning of the label
                            label_list_memo[i].add("I-" + key)
            # for each value, if only part of the value is in the query, discard the label
            # only update the label_list when the whole value of attribute matches the query
            # otherwise, do not update the label_list
            if max(max(row) for row in memo) == len(value_list):
                for index in range(len(label_list)):
                    label_list[index] = label_list[index].union(label_list_memo[index])
            # after updating the label_list, clear the label_list_memo
            for memo_index in range(len(label_list_memo)):
                label_list_memo[memo_index].clear()
    # after finding the matches, the unlabeled parts should be labeled with "O"
    for i in range(len(label_list)):
        # store each word and the corresponding labels in the dictionary
        label_dict = {}
        if len(label_list[i]) == 0:
            label_list[i].add("O")
        # store each word and the corresponding labels in the dictionary
        label_dict[query_list[i]] = label_list[i]
        returned_label_list.append(label_dict)

    return returned_label_list


def query_tagging(query_path, log_path, tagged_query_path, algorithm, threshold):
    """this function take the log_path and query_list as inputs and write
    Args:
        query_path: a list of queries
        log_path: click log path
        tagged_query_path: the path of the outputted tagged query
        algorithm: the select algorithm to calculate similarity
        threshold: the threshold
    Returns:
        write the predicted labels in the tagged_query_path
    """
    # test the args
    print("The selected similarity algorithm is: " + algorithm)
    print("The selected threshold is: " + str(threshold))
    # open the log file and load data
    with open(log_path) as logs_json:
        logs = json.load(logs_json)
    with open(query_path) as query_txt:
        lines = query_txt.readlines()
        index = 0
        for query_list in lines:
            # print(string_match(query, logs, algorithm, threshold))
            tagged_query = string_match(query_list, logs, algorithm, threshold)
            # with open(tagged_query_path, "a+") as tagged_query_json:
            #     json.dump(tagged_query, tagged_query_json)
            with open(tagged_query_path, "a+") as tagged_query_txt:
                tagged_query_txt.write("query{}".format(index) + ": " + query_list.strip("\n") + "\n"
                                       + "Tagged Query: " + str(tagged_query)+"\n")
            index = index + 1
    # read the json file


def main():

    # the threshold is float between [0.0, 1]
    def restricted_float(x):
        x = float(x)
        if x < 0.0 or x > 1.0:
            raise argparse.ArgumentTypeError("%r not in range [0.0, 1.0]" % (x,))
        return x

    # command-line parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("query_path", type=str, help="the path of the input query file, " +
                        "the query file is of txt format each line of which is a query")
    parser.add_argument("log_path", type=str, help="the path of click")
    parser.add_argument("tagged_query_path", type=str,
                        help="the path of the outputted tagged query the format of which is txt")
    parser.add_argument("--algorithm", default="jaro-winkler", type=str, choices=["trigram", "jaro-winkler"],
                        help="select the algorithm to calculate similarity: trigram or jaro-winkler")

    parser.add_argument("--threshold", default=0.9, type=restricted_float,
                        help="if the similarity score of two words >= threshold, the two words are considered same")
    args = parser.parse_args()

    query_tagging(args.query_path, args.log_path, args.tagged_query_path, args.algorithm, args.threshold)


if __name__ == "__main__":
    main()
