import re
import urllib
import numpy as np
import urllib.request


def count_segments(line):
    if len(line) == 0:
        return 0
    if line[len(line) - 1] == '/':
        line = line[0:len(line) - 1]
    return line.count('/', 0, len(line)) - 2


def extract_subsegments(segment):
    if segment.find(':') == -1:
        return []
    return re.split(':', segment)


def has_end_slash(line):
    if line[-1] == '/':
        return True
    return False


def extract_segments(path):
    return filter(bool, path.split('/'))


def get_extension(segment):
    ext_begin = segment.rfind('.')
    if ext_begin == -1:
        return ""
    return segment[ext_begin + 1: len(segment)]


def count_commas(segment):
    return np.sum(np.array(list(segment)) == ',')


def count_underscore(segment):
    return np.sum(np.array(list(segment)) == '_')


def has_upper(segment):
    return segment != segment.lower()


def is_not_ascii(segment):
    return segment != urllib.parse.unquote(segment)


def is_correct_path(url):
    try:
        urllib.request.url2pathname(url)
    except IOError:
        return False
    return True


# extracts features from one url
def extract(url):
    # print urllib.parse.unquote(url)
    features = list()

    # feature 1
    features.append("segments:" + str(count_segments(url.path)))
    # feature 2
    for name in url.params:
        features.append("param_name:" + name)
    # feature 3
    for name in url.params:
        features.append("param:" + name + "=" + url.params[name])
    # features 4a - 4f ans 5
    segments = extract_segments(url.path)
    for pos, segment in enumerate(segments):
        segment_decoded = urllib.parse.unquote(segment)
        regex_res = re.findall("[^\\d]+\\d+[^\\d]+$", segment_decoded)
        # feature 4a
        features.append("segment_name_" + str(pos) + ":" + segment)
        # feature 4b
        if segment.isdigit():
            features.append("segment_[0-9]_" + str(pos) + ":1")
        # feature 4c
        if len(regex_res) == 1 and regex_res[0] == segment_decoded:
            features.append("segment_substr[0-9]_" + str(pos) + ":1")
        # feature 4d
        extension = get_extension(segment)
        if len(extension) != 0:
            features.append("segment_ext_" + str(pos) + ":" + extension)
        # feature 4e
        if len(regex_res) == 1 and regex_res[0] == segment_decoded and len(extension) != 0:
            features.append("segment_ext_substr[0-9]_" + str(pos) + ":" + extension)
        # feature 4f
        features.append("segment_len_" + str(pos) + ":" + str(len(segment)))
        # feature 5
        # segment contains subsegments like <name>: ... : <name>
        subsegments = extract_subsegments(segment_decoded)
        #feature 5.1
        features.append("subsegments_" + str(pos) + ":" + str(len(subsegments)))
        for spos, subsegments in enumerate(subsegments):
            features.append("subsegment_name_" + str(pos) + ":" + subsegments)
        # feature 6
        if is_not_ascii(segment):
            features.append("segment_lang_" + str(pos) + ":not_ascii")
        # feature 6
        if has_upper(segment):
            features.append("segment_has_upper_" + str(pos) + ":1")

    str_url = str(url)
    # feature 7
    features.append("commas:" + str(count_commas(str_url)))
    # feature 8
    features.append("underscore:" + str(count_underscore(str_url)))
    # feature 9
    if is_correct_path(url.path):
        features.append("correct:True")
    # feature 10
    if has_end_slash(url.path):
        features.append("correct:True")
    return features


# extract_features("./data/urls.wikipedia.general", "./data/urls.wikipedia.general", "./check/wikipedia.fea.res")
