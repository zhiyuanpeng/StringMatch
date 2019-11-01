"""
tag each query using the corresponding click log
"""

import json
import numpy as np
import argparse
from pyjarowinkler import distance  # pip install pyjarowinkler


def trigram(word):
    """
    trigram the word
    :param word: the input the word
    :return: trigram_list: a list contains the trigrams of the input string
    """
    trigram_list = []
    if len(word) <= 3:
        trigram_list.append(word)
    else:
        for index in range(len(word)):
            if index <= len(word) - 3:
                trigram_list.append(word[index:index + 3])
    return trigram_list


def similarity(w1, w2, algorithm):
    """
    Computes the trigrams similarity of two input words w1 and w2
    :param w1: the first input word
    :param w2: the second input word
    :param algorithm: the name of the algorithm to calculate the similarity
    :return:
        score: the similarity score
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
    return score


def string_match(query, logs, algorithm, threshold):
    """
    label the input query with the predefined attributes
    :param query: a list of query to be labeled
    :param logs: a json file path which contains the attributes and the corresponding value
    :param algorithm: select the algorithm of similarity
    :param threshold: the threshold of the similarity algorithm
    :return:
        label_list: a list contains the corresponding labels of each word of the input query
        Each element of label_list is a set
    """
    # convert the string to list
    query_list = query.strip("\n").split(" ")
    # store the labels in label_list
    label_list = [[] for _ in range(len(query_list))]
    # cache the label_list
    label_list_memo = [dict() for _ in range(len(query_list))]
    # the final returned label list
    returned_label_list = []
    # visit each attribute in logs
    for key in logs:
        # visit each value of the attribute
        for value in logs[key]:
            # each value is a dict in which there is only a pair of key and value we use the key_name to calculate the
            # similarity score, and the value (click_time) to weight the score
            key_name = list(value.keys())[0]
            click_time = value[key_name]
            # each value of logs[key] may be composed of two or more words, to match the value, use DP
            value_list = key_name.split(" ")
            # Top down DP
            # allocate memory
            # memo = [[0] * (len(value_list) + 1) for _ in range(len(query_list) + 1)]
            memo = np.zeros((len(value_list) + 1, len(query_list) + 1))
            # weighted similarity score memo
            # visit each word of the query, from the last one to the first one
            for i in range(0, len(query_list), 1):
                # visit each word of the attributes[key] from the last one to the first one
                for j in range(0, len(value_list), 1):
                    similarity_score = similarity(query_list[i], value_list[j], algorithm)
                    if similarity_score >= threshold:
                        weighted_similarity_score = similarity_score*click_time
                        memo[j + 1][i + 1] = memo[j][i] + 1
                        if memo[j][i] == 0:
                            # memo[j][i] == 0, so, it is the beginning of the label
                            label_list_memo[i]["B-" + key] = weighted_similarity_score
                        else:
                            # memo[j][i] != 0, so, it is not the beginning of the label
                            label_list_memo[i]["I-" + key] = weighted_similarity_score
            # for each value, if only part of the value is in the query, discard the label
            # only update the label_list when the whole value of attribute matches the query
            # otherwise, do not update the label_list.
            # we first find the location of the max value and then row_index -1, column_index -1, until we find 0
            max_value = max(max(row) for row in memo)
            # in case there are two or more same length matching
            while max(max(row) for row in memo) == len(value_list):
                row_index = 0
                for row in memo:
                    column_index = 0
                    for column in row:
                        # we find the first max_value, assume we have more than one max_value
                        if column == max_value:
                            row_index_cache = row_index
                            column_index_cache = column_index
                            while True:
                                # column_index and row_index are at least 1
                                label_list[column_index_cache - 1].append(label_list_memo[column_index_cache - 1].copy())
                                # clear the added value
                                memo[row_index_cache][column_index_cache] = 0
                                # move to the left up data
                                row_index_cache = row_index_cache - 1
                                column_index_cache = column_index_cache - 1
                                # if the left up data is zero, we don't need to add the label
                                if memo[row_index_cache][column_index_cache] == 0:
                                    break
                        # check next column
                        column_index = column_index + 1
                    # check next row
                    row_index = row_index + 1
            # after updating the label_list, clear the label_list_memo
            for memo_index in range(len(label_list_memo)):
                label_list_memo[memo_index].clear()
    # after finding the matches, the unlabeled parts should be labeled with "O"
    for i in range(len(label_list)):
        # store each word and the corresponding labels in the dictionary
        label_dict = {}
        if len(label_list[i]) == 0:
            label_list[i].append("O")
        # store each word and the corresponding labels in the dictionary
        label_dict[query_list[i]] = label_list[i]
        returned_label_list.append(label_dict)
    return returned_label_list


def query_tagging(query_log_path, tagged_query_path, algorithm, threshold):
    """
    this function take the log_path and query_list as inputs and write
    :param query_log_path: json file contains queries the corresponding click logs
    :param tagged_query_path: the path of the outputted tagged query
    :param algorithm: the select algorithm to calculate similarity
    :param threshold: the threshold
    :return: write the predicted labels in the tagged_query_path
    """
    # test the args
    print("The selected similarity algorithm is: " + algorithm)
    print("The selected threshold is: " + str(threshold))
    # open the log file and load data
    with open(query_log_path) as query_log_json:
        query_log = json.load(query_log_json)
    index = 0
    for query in query_log:
        # print(string_match(query, logs, algorithm, threshold))
        tagged_query = string_match(query, query_log[query], algorithm, threshold)
        with open(tagged_query_path, "a+") as tagged_query_txt:
            tagged_query_txt.write("query{}".format(index) + ": " + query.strip("\n") + "\n"
                                   + "Tagged Query: " + str(tagged_query) + "\n" + "\n")
        index = index + 1


def main():

    # the threshold is float between [0.0, 1]
    def restricted_float(x):
        x = float(x)
        if x < 0.0 or x > 1.0:
            raise argparse.ArgumentTypeError("%r not in range [0.0, 1.0]" % (x,))
        return x

    # command-line parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("query_log_path", type=str, help="the path of the input query and click log file")
    parser.add_argument("tagged_query_path", type=str,
                        help="the path of the outputted tagged query the format of which is txt")
    parser.add_argument("--algorithm", default="jaro-winkler", type=str, choices=["trigram", "jaro-winkler"],
                        help="select the algorithm to calculate similarity: trigram or jaro-winkler")

    parser.add_argument("--threshold", default=0.95, type=restricted_float,
                        help="if the similarity score of two words >= threshold, the two words are considered same")
    args = parser.parse_args()

    query_tagging(args.query_log_path, args.tagged_query_path, args.algorithm, args.threshold)


if __name__ == "__main__":
    main()
