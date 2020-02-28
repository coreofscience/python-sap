import jellyfish
from collections import OrderedDict
import re

def parse_entry(txt):
    head_line = re.compile(r'(?P<head>[A-Z0-9]{2})\s(?P<line>.+)')
    lines = txt.split('\n')
    data = OrderedDict()
    section = "UNKW"

    for line, next in zip(lines, lines[1:] + ['']):
        match_line = head_line.match(line)
        match_next = head_line.match(next)
        if match_line is not None:
            section = match_line.group('head')
            if match_next is not None or next == '':
                data[section] = match_line.group('line')
            else:
                data[section] = [match_line.group('line')]
        else:
            if section in data:
                data[section].append(line.strip())
            else:
                data[section] = [line.strip()]

    return data


def get_entry_label(entry):
    from string import punctuation

    label_parts = []

    mask = dict(zip(list(punctuation), [None] * len(punctuation)))
    clear = lambda s: s.translate(mask)

    if isinstance(entry['AU'], str):
        author = entry['AU']
    else:
        author = entry['AU'][0]

    first_name = author.split(', ')[0]
    last_name = author.split(', ')[-1]

    label_parts.append(first_name + ' ' + clear(last_name))
    label_parts.append(entry.get('PY', ''))
    label_parts.append(entry.get('J9', ''))
    label_parts.append('V' + entry.get('VL', ''))
    if 'BP' in entry:
        label_parts.append('P' + entry['BP'])
    elif 'AR' in entry:
        label_parts.append('p' + entry['AR'].upper())
    if 'DI' in entry:
        label_parts.append('DOI ' + entry['DI'])

    return ', '.join(label_parts)


def get_referenced_labels(entry):
    if 'CR' in entry:
        references = entry['CR']
        if isinstance(references, str):
            return [references, ]
        else:
            return references
    else:
        return []


def get_label_list(entries):
    labels = []

    for entry in entries:
        labels.append(get_entry_label(entry))
        labels.extend(get_referenced_labels(entry))

    return sorted(list(set(labels)))


def extract_edge_relations(entries):
    edges = []

    for entry in entries:
        label = get_entry_label(entry)
        references = get_referenced_labels(entry)
        edges.extend(zip([label] * len(references), references))

    return edges


def detect_duplicate_labels(labels,
                            similarity=jellyfish.jaro_winkler,
                            shared_first_letters=2,
                            threshold=0.96,
                            inverted=False):
    sorted_labels = sorted(labels)
    num_labels = len(sorted_labels)
    duplicates = dict()

    if inverted:
        comp = lambda x, y: x < y
    else:
        comp = lambda x, y: x > y

    for i in range(num_labels):
        label = duplicates.get(sorted_labels[i], sorted_labels[i])
        start_letters = label[:shared_first_letters]

        for j in range(i + 1, num_labels):
            other = sorted_labels[j]

            if not other.startswith(start_letters):
                break

            sim = similarity(label, other)

            if comp(sim, threshold):
                duplicates[other] = label

    return duplicates


def patch_list(items, patch):
    return list(map(patch.get, items, items))


def patch_tuple_list(items, patch):
    keys, values = zip(*items)
    keys = patch_list(keys, patch)
    values = patch_list(values, patch)
    return list(zip(keys, values))
