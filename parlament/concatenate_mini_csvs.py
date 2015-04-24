#encoding: utf-8

import os
import re
import unicodecsv

DATA_DIR = './output'

id_suffix_pattern = re.compile(r'(_*\d*_[a-z]\d{3})')

files = filter(lambda x: '.csv' in x, os.listdir(DATA_DIR))
file_categories = list(set(map(lambda x: id_suffix_pattern.split(x)[0], files)))


def remove_accents(string):
    letter_map = zip(
        list(u'áéíóöőúüű '),
        list(u'aeiooouuu_')
    )
    string = string.lower()
    for old, new in letter_map:
        string = string.replace(old, new)
    return string


def get_field_names(file_name):
    reader = unicodecsv.DictReader(open(file_name, 'rb'))
    return reader.fieldnames


def generate_category_all_csv(csv_category):
    files_in_category = map(lambda x: '{}/{}'.format(DATA_DIR, x), filter(lambda x: csv_category in x, files))
    output_file = '{}/all/{}.csv'.format(DATA_DIR, csv_category)
    # print output_file

    in_fieldnames = reduce(lambda x, y: list(set(x+y)), map(get_field_names, files_in_category))
    out_fieldnames = map(remove_accents, in_fieldnames)
    writer = unicodecsv.DictWriter(open(output_file, 'wb'), out_fieldnames)
    print 'Field names for file {} are the following:\n{}'.format(output_file, writer.fieldnames)
    writer.writeheader()
    for file_name in files_in_category:
        reader = unicodecsv.DictReader(open(file_name, 'rb'))
        # print file_name
        for inrow in reader:
            outrow = dict()
            for key in inrow.keys():
                outrow[remove_accents(key)] = inrow[key]
            try:
                writer.writerow(outrow)
            except ValueError:
                #print 'PROBLEM with pid {} in file {}!!'.format(row['pid'], file_name)
                #print row
                pass

print file_categories
for csv_category in file_categories:
    generate_category_all_csv(csv_category)