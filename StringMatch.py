"""
This program is to label the search query with the corresponding attributes from the click logs
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


def similarity(w1, w2, algorithm, threshold):
    """
    Computes the trigrams similarity of two input words w1 and w2
    :param w1: the first input word
    :param w2: the second input word
    :param algorithm: the name of the algorithm to calculate the similarity
    :param threshold: the threshold to determine whether two word are similar or not
    :return:
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


def get_memo_matrix(query, attribute_set):
    """
    generate a memo matrix according to the input attribute set
    :param query: the input query
    :param attribute_set: a set of the attribute value
    :return: a matrix
    """
    attribute_list = list(attribute_set)
    # store the sorted attribute value
    order_no_repeat = []
    for i in range(len(attribute_list) - 1):
        for j in range(i + 1, len(attribute_list)):
            if attribute_list[i][2:] == attribute_list[j][2:]:
                # find B-xx and I-xx
                # we put the B-xx in front of I-xx by default
                if attribute_list[i][0] == "B":
                    order_no_repeat.append(attribute_list[i])
                    order_no_repeat.append(attribute_list[j])
                else:
                    order_no_repeat.append(attribute_list[j])
                    order_no_repeat.append(attribute_list[i])
                # once find one, break
                break
    if len(order_no_repeat) == 0:
        longest_match_flag = 0
    else:
        longest_match_flag = 1
    return longest_match_flag, np.zeros((len(order_no_repeat) + 1, len(query) + 1)), order_no_repeat


def find_longest_value(query, attribute_set):
    """
    find the longest attribute value, here we only use memo to store the attribute value which length is bigger than 2
    for O or only one value attribute label, we don't store them
    :param query: a labeled query with the format: [{'tesla': {'B-BR'}}, {'red': {'B-CO'}},
    {'model': {'B-PD'}}, {'x': {'I-PD'}}]
    :param attribute_set: the attribute value: BR, CO, PD, ...
    :return:
        memo: use numbers to indicate the location of each element of the longest attribute value
        look_up_chain: this is for backward look up
    """
    # Top down DP
    # allocate memory and get the attributes in the matrix
    trash, memo, attribute_list = get_memo_matrix(query, attribute_set)
    lookup_chain = np.zeros_like(memo)
    # visit each word of the query, from the last one to the first one
    for i in range(0, len(query), 1):
        # visit each element of the attribute_list:B I B I ...
        for j in range(0, len(attribute_list), 1):
            key_list = list(query[i].keys())
            key = key_list[0]
            if attribute_list[j] in query[i][key]:
                # For B, we only assign 1.
                if attribute_list[j][0] == "B":
                    memo[j + 1][i + 1] = 1
                # the attribute_list only have B- and I- values
                # for I, we need to check the left up corner and left
                else:
                    # we first check the left begins with I or not, if the left is I,
                    if memo[j + 1][i] > 1:
                        memo[j + 1][i + 1] = memo[j + 1][i] + 1
                        # 1 means left is I
                        lookup_chain[j + 1][i + 1] = 1
                    # if the left is 0, this I is the second word of the attribute value
                    else:
                        memo[j + 1][i + 1] = 2
                        # 2 means left up is B
                        lookup_chain[j + 1][i + 1] = 2
            # if query[i].values doesn't contain the attribute_list[j], we don't change the memo value
    return memo, lookup_chain, attribute_list


def longest_value_match(query, attribute_set):
    """
    for multi labels, use this function to only match the longest attribute value. If the query only have one label for
    each token, we don't need to use this function to deal with the query.
    :param query: a query some elements of which have more than one labels
    :param attribute_set: the attribute the length of the value of which is more than 2
    :return: the query each token of which only has one label
    """
    memo, lookup_chain, attribute_list = find_longest_value(query, attribute_set)
    # the memo and lookup_chain have one more row and column, delete them before iterate the matrix
    memo = np.delete(memo, 0, axis=0)
    memo = np.delete(memo, 0, axis=1)
    lookup_chain = np.delete(lookup_chain, 0, axis=0)
    lookup_chain = np.delete(lookup_chain, 0, axis=1)
    while True:
        max_value = max(max(row) for row in memo)
        row_index = 0
        for row in memo:
            column_index = 0
            for column in row:
                # column is the one contains the last element of the longest attribute value, we use the lookup_chain
                # to update query, if the column contains more than one max value, we deal with the first one
                if column == max_value:
                    # we find the longest value backward
                    while True:
                        # we need to clear the memo corresponding to the longest value
                        memo[row_index, column_index] = 0
                        # we need to delete all other attributes, and only keep the name of this row, which is kept
                        # in the attribute_list
                        # first we need to get the key, each element of the query only has one key, so we use [0]
                        key_list = list(query[column_index].keys())
                        key = key_list[0]
                        # if the token have more than one attribute values, we need to delete and keep
                        if len(query[column_index][key]) > 1:
                            query[column_index][key].clear()
                            # print(row_index, column_index)
                            # after we delete the attribute value, we need to add the name of this row
                            query[column_index][key].add(attribute_list[row_index])
                        if lookup_chain[row_index, column_index] == 2:
                            # we need to update the next location according to the flag
                            row_index = row_index - 1
                            column_index = column_index - 1
                        elif lookup_chain[row_index, column_index] == 1:
                            # we need to update the next location according to the flag
                            column_index = column_index - 1
                        # the last element of the attribute value
                        else:
                            break
                column_index = column_index + 1
            row_index = row_index + 1
        # if each value of the memo is less than 2, we don't need to mach the longest value
        if max(max(row) for row in memo) < 2:
            break
    return query


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
    label_list = [set() for _ in range(len(query_list))]
    # cache the label_list
    label_list_memo = [set() for _ in range(len(query_list))]
    # the final returned label list
    returned_label_list = []
    # get the different attribute value of the query
    attribute_set = set()
    # math the longest value flag
    multi_label_flag = 0
    # visit each attribute in logs
    for key in logs:
        # visit each value of the attribute
        for value in logs[key]:
            # each value of logs[key] may be composed of two or more words, to match the value, use DP
            value_list = value.split(" ")
            # Top down DP
            # allocate memory
            # memo = [[0] * (len(value_list) + 1) for _ in range(len(query_list) + 1)]
            memo = np.zeros((len(value_list) + 1, len(query_list) + 1))
            # visit each word of the query, from the last one to the first one
            for i in range(0, len(query_list), 1):
                # visit each word of the attributes[key] from the last one to the first one
                for j in range(0, len(value_list), 1):
                    if similarity(query_list[i], value_list[j], algorithm, threshold):
                        memo[j + 1][i + 1] = memo[j][i] + 1
                        if memo[j][i] == 0:
                            # memo[j][i] == 0, so, it is the beginning of the label
                            label_list_memo[i].add("B-" + key)
                        else:
                            # memo[j][i] != 0, so, it is not the beginning of the label
                            label_list_memo[i].add("I-" + key)
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
                                label_list[column_index_cache - 1] = label_list[column_index_cache - 1].union(label_list_memo[column_index_cache - 1])
                                # statistic the different labels of the query, longest match function need this info
                                attribute_set = attribute_set.union(label_list_memo[column_index_cache - 1])
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
            label_list[i].add("O")
        # if one token has more than one labels, we need use longest_value_match function
        elif len(label_list[i]) > 1:
            multi_label_flag = 1
        # store each word and the corresponding labels in the dictionary
        label_dict[query_list[i]] = label_list[i]
        returned_label_list.append(label_dict)
    # if need longest_value_match
    if multi_label_flag == 1:
        longest_match_flag, trash1, trash2 = get_memo_matrix(returned_label_list, attribute_set)
        if longest_match_flag == 1:
            returned_label_list = longest_value_match(returned_label_list, attribute_set)
    return returned_label_list


def query_tagging(query_path, log_path, tagged_query_path, algorithm, threshold):
    """
    this function take the log_path and query_list as inputs and write
    :param query_path: a list of queries
    :param log_path: click log path
    :param tagged_query_path: the path of the outputted tagged query
    :param algorithm: the select algorithm to calculate similarity
    :param threshold: the threshold
    :return: write the predicted labels in the tagged_query_path
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
            with open(tagged_query_path, "a+") as tagged_query_txt:
                tagged_query_txt.write("query{}".format(index) + ": " + query_list.strip("\n") + "\n"
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
    parser.add_argument("query_path", type=str, help="the path of the input query file, " +
                        "the query file is of txt format each line of which is a query")
    parser.add_argument("log_path", type=str, help="the path of click")
    parser.add_argument("tagged_query_path", type=str,
                        help="the path of the outputted tagged query the format of which is txt")
    parser.add_argument("--algorithm", default="jaro-winkler", type=str, choices=["trigram", "jaro-winkler"],
                        help="select the algorithm to calculate similarity: trigram or jaro-winkler")

    parser.add_argument("--threshold", default=0.95, type=restricted_float,
                        help="if the similarity score of two words >= threshold, the two words are considered same")
    args = parser.parse_args()

    # for test
    # args.query_path = "special_case_query.txt"
    # args.log_path = "special_case.json"
    # args.tagged_query_path = "special_case_query_tagged.txt"
    #
    query_tagging(args.query_path, args.log_path, args.tagged_query_path, args.algorithm, args.threshold)
    # test get_memo_matrix
    # print(longest_value_match([{"t1": {"B-CO", "B-PT", "B-PD"}}, {"t2": {"B-PD", "I-CO"}}, {"t3": {"I-CO", "B-PT"}},
    #                            {"t4": {"I-CO"}}, {"t5": {"B-PT"}}, {"t6": {"I-PT"}}, {"t7": {"O"}}, {"t8": {"B-CO"}}],
    #                           {"B-CO", "B-PT", "B-PD", "I-CO", "I-PT", "O"}))


if __name__ == "__main__":
    main()
