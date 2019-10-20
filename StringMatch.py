"""
This program is to label the search query with the corresponding attributes from the click logs

PT: product type
BR: brand
GR: gender
CO: color
CH: character
AV: age
AU: age unit
AT: age type
SV: size value
SU: size unite
ST: size type
QV: quantity value
QU: quantity unite
QT: quantity type
PD: product type description
PL: product line
PR: price
MI: miscellaneous
"""

import json
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
    query_list = query.split(" ")
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


def query_tagging(query_list, log_path, tagged_query_path, algorithm, threshold):
    """this function take the log_path and query_list as inputs and write
    Args:
        query_list: a list of queries
        log_path: click log path
        tagged_query_path: the path of the outputted tagged query
        algorithm: the select algorithm to calculate similarity
        threshold: the threshold
    Returns:
        write the predicted labels in the tagged_query_path
    """
    # open the log file and load data
    with open(log_path) as logs_json:
        logs = json.load(logs_json)
    for index in range(len(query_list)):
        # print(string_match(query, logs, algorithm, threshold))
        tagged_query = string_match(query_list[index], logs, algorithm, threshold)
        # with open(tagged_query_path, "a+") as tagged_query_json:
        #     json.dump(tagged_query, tagged_query_json)
        with open(tagged_query_path, "a+") as tagged_query_txt:
            tagged_query_txt.write("query{}".format(index) + ": " + query_list[index] + "\n" +
                                   "Tagged Query: " + str(tagged_query)+"\n")
    # read the json file


def main():
    """
    test similarity
    """
    # print(trigram("definition"))
    # print(similarity("definition", "definitions", "trigram", 0.9))
    # print(similarity("definition", "definitions", "jaro-winkler", 0.9))

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
    bestbuy_query = ['apple watch', 'ipad', 'apple watch series 3', 'apple watch series 2', 'apple laptop', 'apple homepod', 'apple watch series 3 42mm', 'apple tv', 'iphone x', 'airpods wireless', 'amiibo', 'amazon fire stick', 'all-in-one computers', 'arlo pro', 'air fryer', 'iphone', 'asus laptop', 'ipad pro 10.5 inch', 'antennas hdtv antenna', 'alienware laptop', 'apple watch', 'ipad', 'apple watch series 3', 'apple watch series 2', 'apple laptop', 'apple homepod', 'apple watch series 3 42mm', 'apple tv', 'iphone x', 'airpods wireless', 'beats solo3 wireless', 'beats wireless', 'bluetooth speakers', 'bose wireless headphones', 'blu-ray', 'bluetooth headphones', 'beats studio wireless', 'beats headphones', 'chromebook', 'camera', 'call of duty world war 2', 'cell phones', 'chromecast', 'canon camera', 'computer', 'computer monitors', 'iphone x case', 'call of duty wwii', 'desktop computers', 'dishwasher', 'dell laptop', 'dvd player', 'drones with camera', 'dryer', 'dyson vacuum', 'dell xps 13', 'external hard drive', 'external hard drive', 'essential phone', 'earbud headphones', 'echo dot', 'ethernet cable', 'earphones', 'easystore 8tb', 'refrigerator', 'fitbit', 'fire stick', 'fingerlings baby monkeys', 'xbox one x', 'fitbit charge 2', 'fitbit ionic', 'freezer', 'gopro', 'gaming laptop', 'gaming desktop', 'google home', 'graphics card', 'google home mini', 'gps navigation', 'google pixel 2', 'gps for cars', 'television', 'headphones', 'hp laptop', 'horizon zero dawn', 'hard drive', 'hp spectre x360', 'home theater system', 'horizon zero dawn ps4', 'hoverboard', 'ipad', 'iphone x', 'ipad pro 10.5 inch', 'iphone x case', 'ipad pro 12.9 inch', 'iphone 8', 'iphone 6', 'ipad mini', 'iphone 7 plus', 'apple watch', 'jbl bluetooth speaker', 'jaybird', 'jaybird x3', 'jbl charge 3', 'jbl wireless headphones', 'jaybird freedom f5', 'jaybird freedom', 'just dance 2018', 'kitchenaid stand mixer', 'keurig', 'kindle fire', 'keyboard', '4k tv', 'kitchenaid', 'klipsch speakers', 'kids tablets', 'sony 4k', 'karaoke machine', 'laptop', 'laptops under $300', 'laptops under $500', 'lenovo laptop', 'lg tv', 'laptops under $200', 'logitech mouse', 'lenovo yoga 720', 'lg oled 65', 'macbook pro', 'macbook', 'ipad mini', 'macbook air', 'monitor', 'microwave', 'micro sd', 'cell phones', 'microphone', 'mini refrigerators', 'nintendo switch', 'nintendo classic edition', 'note8', 'nest thermostat', 'nintendo switch games', 'nintendo switch console', 'need for speed payback', 'nvidia shield tv', 'note8 unlocked', 'nintendo 3ds xl console', 'xbox one x', 'xbox one', 'oculus rift', 'oled tv', 'over the range microwave', 'otterbox', 'onkyo receivers', 'call of duty world war 2', 'playstation 4', 'projector', 'iphone x', 'ps4 games', 'ipad', 'macbook pro', 'playstation ps4 console', 'printers all one wireless', 'ps4 pro', 'ipad pro 10.5 inch', 'qled 4k tv', 'qi wireless charging', 'qled samsung smart tv', 'qi wireless charger', 'quicken 2018', 'quickbooks pro 2018', 'refrigerator', 'ring video doorbell', 'roku', 'remote car starter', 'router', 'receiver', 'roku streaming stick', 'refrigerators with french doors', 'roku tv', 'laptop', 'samsung galaxy s8', 'soundbar', 'samsung galaxy s8 unlocked', 'samsung gear s3 smartwatch', 'samsung tv', 'apple watch series 3', 'apple watch series 2', 'samsung galaxy s7 edge unlocked', 'television', 'tablets', 'xbox one x', 'iphone x', 'tv stands', 'tv wall mount', 'apple watch series 3', 'laptop', 'apple watch series 2', 'tablets under $100', 'unlocked cell phones', 'usb flash drive', 'uncharted lost legacy', 'laptops under $300', 'wii u console', 'upright freezer', 'usb-c to usb adapter', 'universal remote', 'vacuum', 'vizio 4k tv', 'vacuum cleaners', 'vizio', 'graphics card', 'verizon cell phones', 'video camera', 'vizio soundbar', 'ring video doorbell', 'ipad pro 10.5 inch', 'wireless headphones', 'wireless earbuds', 'apple watch', 'apple watch series 3', 'apple watch series 2', 'washer dryer combo', 'wifi extender', 'washer and dryer', 'beats solo3 wireless', 'xbox one x', 'xbox one', 'iphone x', 'xbox', 'xbox one controller', 'xbox x', 'xbox one x scorpio', 'iphone x case', 'xbox one games', 'xbox one x console', 'yamaha receiver', 'yoga 920', 'yoga 720', 'yamaha soundbar', 'your name blu-ray', 'yoga 910', 'yeti microphone', 'yamaha yas 207 soundbar', 'yoga 710', 'zagg invisibleshield glass', 'zagg iphone x', 'horizon zero dawn', 'zelda nintendo switch', 'moto z2 force', 'zte blade spark', 'zte maven 3', 'zte axon 7 unlocked', 'aa battery', 'aaa battery', 'aaaa battery', 'aa battery charger', 'aaa rechargeable battery', 'aa lithium rechargeable battery', 'aaxa projector', 'rechargeable aa battery', 'ab switch', 'ableton live 9', 'dyson v8 absolute', 'ableton', 'above the rim', 'about time blu-ray', 'acer chromebook', 'acer laptop', 'ac adapter', 'acer aspire e15', 'action camera', 'acer monitor', 'acer predator laptop', 'activity tracker', 'acer chromebook 15', 'accessories for iphone 7', 'best buy black friday ad', 'adapter', 'adobe photoshop', 'adapters for iphone 7', 'adapter for macbook pro', 'adobe premiere', 'adapters and converters', 'adobe photoshop elements 2018', 'aerosmith', 'aegis 3', 'aeon wall mount', 'aerosmith cd', 'aeroccino milk frother', 'aerosmith vinyl', 'aeon projector screen', 'aesthetica of a rogue hero', 'aeon flux', 'aftershokz headphones', 'aftershokz trekz titanium', 'afterglow headset for xbox one', 'afterglow headset', 'after shokz', 'afterglow ag 9', 'aftershokz', 'afterglow xbox one controller', 'af-p dx nikkor 10-20mm', 'afterglow headset ps4', 'ag 9 wireless headset', 'agents of mayhem', 'agitator washing machine', 'ag 9 xbox one headset wireless', 'age of ultron', 'age of empires', 'age of adaline', 'ahs roanoke', 'whirlpool wod93ec0ah', 'whirlpool wos92ec0ah', 'asus vx24ah', 'ahbbp-401', 'airpods wireless', 'air fryer', 'airpods', 'air purifier', 'amiibo', 'air pods', 'air conditioners', 'macbook air', 'airport extreme', 'airpods accessories', 'akg headphones', 'akai', 'akracing', 'akira blu-ray', 'akg n60 nc', 'akg wireless', 'akiba"s beat', 'akracing chair', 'akame ga kill', 'akira', 'all-in-one computers', 'alienware laptop', 'alexa echo', 'alienware desktop', 'alexa', 'alienware', 'alarm clock', 'all-in-one printer', 'all-in-one desktop', 'altec lansing speakers', 'amiibo', 'amazon fire stick', 'amazon echo', 'amazon fire tv', 'amazon fire 7" tablet', 'amazon fire tablet', 'amazon fire hd 8', 'amplifier', 'am fm radio', 'am-fm radios', 'antennas hdtv antenna', 'antenna', 'android tv box', 'android tablet', 'anti virus software', 'android smartwatch', 'android phone', 'anki overdrive', 'anti-virus software', 'anker power', 'aoc 27" monitor', 'aoc monitor', 'aoc 21.5', 'aoc 4k monitor', 'aoc 24" monitor', 'aoc 21.5" ips led hd monitor black', 'aoc portable monitor', 'aoc gaming monitor', 'aoc 23" monitor', 'aoc agon', 'apple watch', 'apple watch series 3', 'apple watch series 2', 'ipad', 'apple laptop', 'apple homepod', 'apple watch series 3 42mm', 'apple tv', 'apple watch series 1', 'apple watch series 3 38mm', 'aquabot', 'aquarium', 'aquarius season 2', 'aquasana water filter', 'aqua teen hunger force', 'aqua bose wireless headphones', 'aquarius', 'arlo pro', 'arlo pro 2', 'arlo security camera', 'arlo', 'arris cable modem', 'arris cable modem router', 'arlo q', 'arris surfboard sb6190', 'ark survival evolved ps4', 'arlo pro security camera', 'asus laptop', 'assassins creed origins', 'asus 2 in 1 laptop', 'astro a40 headset', 'asus monitor', 'astro a50 wireless', 'assassin"s creed', 'asus zenbook', 'assassin"s creed origins xbox one', 'at&t prepaid phones', 'at&t', 'at&t zte maven', 'at&t gophone', 'atomic blonde', 'at&t cell phones', 'atomic blonde steelbook', 'at&t prepaid iphone', 'at&t gophone iphone', 'audio-technica', 'automatic car starter', 'august smart lock', 'aux cord', 'audio cable', 'audio receiver', 'aux cable for car', 'audioquest hdmi cables', 'aux bluetooth adapter', 'av to hdmi', 'av cable', 'av adapter', 'av receiver bluetooth', 'av 10 pin to rca cable', 'avatar blu-ray', 'av receivers with wifi', 'av stand', 'awolnation', 'aw-650 white', 'awakening the zodiac', 'awg power cord', 'aw17r4-7000slv', 'awg cable', 'lowepro protactic 450 aw', 'aw17r4', 'spirited away', 'axon 7', 'axon 7 mini', 'axiom verge switch', 'axess speaker', 'axon 7 unlocked', 'axiom verge multiverse edition', 'axxess aswc-1', 'axon zte 7 cell phone', 'azure striker gunvolt striker pack', 'azus', 'azulle mini pc', 'azure washer', 'azure blue washer', 'backpack', 'battery', 'baby monitor', 'back up camera', 'battlefront 2 ps4', 'battery pack', 'battery backup', 'backup camera', 'battlefield 1', 'bb-8 droid', 'bb-9e', 'bbq grills', 'bb king', 'sphero bb-8', 'bbq grill set', 'bc 30 wireless back-up camera', 'bc 30', 'bc-trx battery charger', 'garmin bc 30', 'bcciv', 'garmin bc-30', 'sony gtkxb7bc', 'one million bc', 'bdi tv stands', 'bd-r 50gb', 'bd-re', 'bd-j5700', 'bdi furniture', 'bd-j6300 blu-ray player', 'bd-j5700 za', 'beats solo3 wireless', 'beats wireless', 'beats studio wireless', 'beats headphones', 'beats', 'beats solo 2 wireless', 'beats studio 2', 'beats powerbeats 3', 'beats studio 3', 'beats pill speaker', 'bfg blu-ray', 'bfg dvd', 'doom 3 bfg edition', 'the bfg blu-ray', 'bg-e20', 'bg-e16', 'canon bg-e16 battery grip', 'canon bg-e20 battery grip', 'np-bg1', 'np-bg1 battery charger', 'frigidaire bggf3045rf', 'binoculars', 'big bang theory season 10', 'bissell carpet cleaner', 'bioshock the collection', 'bissell crosswave', 'bissell vacuum', 'fitbit', 'big krit', 'bike', 'bje200xl', 'best of b.j. thomas cd', 'lc 71 bk', 'tn221bk', 'lc101bk', 'lc203bk', 'lc103bk', 'lc61bk', 'brother lc103bk', 'brother lc203bk', 'ns-cf26bk6', 'lc75bk', 'bluetooth speakers', 'blu-ray', 'bluetooth headphones', 'bluetooth headset', 'bluetooth earbuds', 'bluetooth adapter', 'bluetooth transmitter', 'acer aspire e 15 e5-575-33 bm', 'bmw installation kit', 'bmi scale', 'bmw 3 series', 'bmw radio replacement', 'bmw dash kit', 'bmx bandits', 'bmw installation kit 3 series', 'bmw radio kit', 'bnc cable', 'bnc adapter', 'bnc connectors', 'bnc coupler', 'bnc extension cable', 'bnc camera cables', 'bnc camera', 'np-bn1', 'bnc extension', 'bose wireless headphones', 'bose speakers', 'bose headphones', 'bose bluetooth speaker', 'boost mobile cell phones', 'bose', 'bose soundbar', 'bosch dishwasher', 'bose quietcomfort 35', 'bose home theater system', 'bp monitor', 'bp 9080', 'bp-511 canon battery', 'bp-808 battery', 'bp-718', 'bp9060', 'lowepro fastpack bp 250 aw ii', 'lg bp 350', 'canon bp-718 battery', 'evga 850w modular bq power supply', '15m-bq021dx', 'brother printer', 'breville toaster oven', 'breath of the wild amiibo', 'brother laser printer', 'breville smart oven air', 'breville', 'bread maker', 'bragi dash pro', 'bs015dx', 'sony xb50bs extra bass', 'sony xb50bs wireless headphones', 'whirlpool wfg505m0bs', 'sony xb80bs', 'rf-2w1b-sp', 'wfg320m0bs', 'xb50bs', 'xb80bs', 'gua2600bst', 'bt headphones', 'bt transmitter', 'bt headset', 'bt earbuds', 'bt speakers', 'jbl reflect mini bt', 'bt-300', 'razer hammerhead bt', 'built in oven', 'xbox one s 1tb bundle', 'built in wine cooler', 'bunn coffee makers', 'bvmc-pstx91', 'bw speakers', 'b&w speakers', 'b&w headphones', 'b&w 685 s2', 'b&w 702 s2', 'b&w subwoofer', 'b&w 700 series', 'b&w center speaker', 'b&w px', 'b&w m1', 'bxt1', 'np-bx1 battery', 'sony np-bx1', 'bxf130', 'beats by dre', 'refrigerator side-by-side', 'side by side refrigerator', 'bytten stacks', 'beats by dr. dre studio 2', 'beats by dre beats x', 'beats by dre studio wireless', 'camera', 'canon camera', 'call of duty wwii', 'car stereo', 'iphone x case', 'car stereo with bluetooth', 'video camera', 'canon g7x mark ii', 'cb radio', 'cb radio antenna', 'cb radio kit', 'cb antenna', 'cb antenna mount', 'cb antenna kit', 'cb antenna wire', 'cb radio mount', 'cb5-132t-c9kk', 'cctv security cameras', 'cctv system', 'cctv camera', 'cctv monitor', 'cctv cable', 'cctv', 'ccm 683', 'ccm664', 'ccm663', 'cd player', 'cd player with speakers', 'cd player and radio', 'cd player with bluetooth', 'cd drive', 'cd players and tuners', 'cd burner', 'cd-r', 'cd-rom drive', 'cell phones', 'cell phones with no contract', 'unlocked cell phones', 'cell phone signal booster', 'ceiling speakers', 'cell phone accessories', 'cell phones for t-mobile', 'cell phone car mount', 'cell phones no contract unlocked', 'cf memory card', 'cf card', 'cf card reader', 'cf memory card reader', 'cf card adapter', 'cfast 2.0 card', 'cf reader', 'cfast memory card', 'cfast 128gb', 'cf391 curved led monitor', 'mc17j8000cg', 'mc11k7035cg', 'cgs-5020', 'whirlpool w3cg3014xs', 'whirlpool w3cg3014xb', 'chromebook', 'chromecast', 'chest freezer', 'chromecast 2', 'charger for iphone', 'chromebook laptop', 'chefman air fryer', 'champion amiibo', 'chromecast ultra', 'cintiq', 'cinnamon hdmi', 'circle by disney', 'cinderella dvd', 'circle 2', 'cisco', 'cities skylines', 'wt1901ck', 'lg wd100ck', 'lg wt1901ck', 'clock radio', 'super nintendo classic', 'nintendo classic edition', 'vacuum cleaners', 'clothes dryer', 'clock radio with cd player', 'cm 700 modem', 'cm storm', 'cm 4550', 'cm1000', 'cmos battery', 'cm600', 'cm10', 'cm500', 'cnco', 'computer', 'computer monitors', 'coffee makers', 'counter depth refrigerator', 'computer speakers', 'desktop computers', 'cordless home phones', 'computer desk', 'corsair keyboard', 'cooktop', 'cpu cooler', 'cpu processor', 'cpu cooling fan', 'cpu fan', 'cpu fan & heatsink', 'computer processor', 'cpu water cooler', 'cpu pc', 'kontrolfreek cqc', 'chromecast', 'cricket wireless phones', 'crock pot', 'cricket cell phones', 'crash bandicoot', 'cricket sim card', 'cr 2032 battery', 'cs go', 'csi crime scene investigation', 'cs 9080', 'csr audio', 'csi complete series', 'cs-9060', 'csi final season', 'usb type c-to-usb type c', 'usb type c-to-micro usb adapter', 'ctl490dw', 'usb type c-to-usb type a', 'mg11h2020ct', 'curved tv', 'curved monitor', 'curve tv', 'cuphead xbox one', 'cuisinart coffee maker', 'curved gaming monitor', 'cuisinart', 'wd100cv', 'lg wd200cv', 'dell cvxgf toner cartridge black', 'cwm663', 'wm3270cw', 'wt7200cw', 'lg wt7200cw', 'lg wt7500cw', 'lg wt1501cw', 'lg wm3270cw', 'wt1501cw', 'wt7500cw', 'cx amplifier', 'cx750m', 'cxa 600', 'ti-nspire cx', 'cx675', 'cx440', 'texas instruments ti-nspire cx', 'activeon cx hd action camera', 'kicker cx 1200', 'sennheiser cx 2.00g', 'cyber power pc', 'cyberpower pc', 'cyberpowerpc desktop gaming pc', 'cyberpowerpc', 'cybertron pc', 'cyberpower battery backup', 'cyberpower', 'cyber power ups', 'dash cam', 'dash camera', 'horizon zero dawn', 'dash cam front and rear', 'horizon zero dawn ps4', 'dash cam for car', 'dc universe 10th', 'dc 10th anniversary', 'dc to ac power inverter', 'dc power supply', 'dc adapter', 'dc 5v charger', 'dc 4k collection', 'ddr4 memory', 'ddr3 ram', 'ddr4 ram', 'ddr3 ram for laptop', 'ddr3', 'ddr3 desktop ram', 'ddr4', 'ddr4 2400 ram', 'ddr4 ram laptop', 'ddr3l laptop memory', '08g-p4-6173-kb', '120hz led tv', '4k tv', '50ft ethernet cable', 'aa aaa battery charger', 'aaa battery', 'aaxa projector', 'ableton', 'acer laptop', 'acer predator laptop', 'action camera', 'adapter for macbook pro', 'adobe photoshop elements 2018', 'afterglow headset for xbox one', 'afterglow xbox one controller', 'air pods', 'airpods', 'alexa', 'amazon echo', 'amazon fire 7" tablet', 'amazon fire hd 8', 'amplifier', 'antennas hdtv antenna', 'apple tv', 'apple watch series 2 38mm', 'aquabot', 'aquasana water filter', 'arlo q', 'assassin"s creed', 'astro a40 headset', 'asus chromebook flip c302ca-dhm4', 'asus laptop', 'asus monitor 144hz', 'asus vx24ah', 'at&t', 'at&t gophone', 'at&t prepaid phones', 'audio receiver', 'audioquest hdmi cables', 'av cable', 'av receivers with wifi', 'awolnation', 'b&w headphones', 'battery', 'battery pack', 'bd-j5700', 'bdi tv stands', 'beats by dr. dre studio 2', 'beats ep headphones', 'beats solo 2 wireless', 'binoculars', 'bioshock the collection', 'bissell carpet cleaner', 'blu-ray', 'bluetooth headset', 'bluetooth transmitter', 'bmw dash kit', 'bnc camera', 'bnc coupler', 'bose soundbar', 'bt earbuds', 'bt speakers', 'call of duty world war 2', 'canon bg-e20 battery grip', 'canon sx730 hs', 'canon vixia hf r82', 'car stereo with bluetooth', 'cb3-431-c5ex', 'cctv camera', 'cctv security cameras', 'cd player with speakers', 'cell phone accessories', 'cell phone car mount', 'cell phones for t-mobile', 'cf memory card', 'charger for iphone', 'chefman air fryer', 'cm600', 'cpu water cooler', 'cs-9060', 'curve tv', 'cx675', 'cxa 600', 'dc adapter', 'ddr4 ram laptop', 'dell gaming s2417dg', 'dell s2417dg', 'dell xps 15', 'digital camera', 'dlp projector 1080p', 'dmp-ub900', 'dp cable adapter', 'dryer', 'dual monitor stand', 'dv42h5000ew', 'dvd and blu-ray player', 'dvd movies', 'dvr recorder', 'dvr tv recorders', 'dw80m9550us', 'dyson vacuum', 'ebay gift cards', 'ebike', 'eero pro', 'ef-s 18-55mm is stm lens', 'egyptian lover', 'either net cable', 'electric dryer', 'en-el 14a battery nikon', 'envy x360', 'epson 220 ink cartridges', 'epson 410 ink cartridge', 'equator washer', 'ergonomic keyboard', 'escort radar detector', 'essential oils ellia', 'essential phone case', 'ethernet cable', 'ethernet cable coupler', 'ethernet splitter']
    bestbuy_log = "bestbuy_click_log.json"
    query_with_tag_path_3 = "bestbuy_query.txt"
    query_tagging(bestbuy_query, bestbuy_log, query_with_tag_path_3, "jaro-winkler", 0.9)


if __name__ == "__main__":
    main()




