#encoding: utf-8

import scrapy
import unicodecsv
import sys
import re
from collections import defaultdict

id_pattern = re.compile(r'Fogy_kpv.kepv_adat%3FP_azon%3D([a-z]\d{3})')


def remove_accents(string):
    letter_map = zip(
        list(u'áéíóöőúüű '),
        list(u'aeiooouuu_')
    )
    string = string.lower()
    for old, new in letter_map:
        string = string.replace(old, new)
    return string


def extract_first(selector):
        try:
            return selector.extract()[0]
        except IndexError:
            return ''


def extract_text(selector):
    try:
        return selector.xpath('text()').extract()[0]
    except IndexError:
        try:
            return selector.xpath('a/text()').extract()[0]
        except IndexError:
            return ''


def repair_row(row, row_before):
    for key in row.iterkeys():
        if row[key] == '':
            row[key] = row_before[key]
    return row


def add_index_to_multiple_list_elements(in_list):
    d = defaultdict(int)
    for item in in_list:
        d[item] += 1
    out_list = []
    for item in in_list:
        if d[item] > 1:
            out_list.append('{}_{}'.format(item, d[item]))
            d[item] -= 1
        else:
            out_list.append(item)
    return out_list


def parse_individual(response):
    response = response.replace(body=response.body.replace('<br />', '\n'))
    pid = id_pattern.findall(response.url)[0]
    tables = response.xpath('.//tbody[.//th][.//th/@colspan][not(.//img)]')
    table_names = add_index_to_multiple_list_elements(
        map(remove_accents, tables.xpath('.//th[./@colspan]/text()').extract()))

    def extract_fieldnames(table):
        fieldnames = []
        fields = table.xpath('.//th[not(./@colspan)]')
        for field in fields:
            fieldnames.append('_'.join(field.xpath('text()').extract()))
        return fieldnames

    table_field_names = map(extract_fieldnames, tables)

    print 'THIS IS THE CURRENT PID: {}'.format(pid)

    for table_name, table, field_names in zip(table_names, tables, table_field_names):
        file_name = './output/{}_{}.csv'.format(table_name, pid)
        field_names = ['pid'] + field_names
        writer = unicodecsv.DictWriter(open(file_name, 'wb'), field_names)
        writer.writeheader()
        rows = table.xpath('.//tr[not(./th)]')
        row_before = defaultdict(str)
        for row in rows:
            in_values = row.xpath('td')
            out_values = [pid] + map(extract_text, in_values)
            row = repair_row(dict(zip(field_names, out_values)), row_before)
            row_before = row
            writer.writerow(row)


class ParlSpider(scrapy.Spider):
    name = "parlament"
    start_urls = [
        "http://www.parlament.hu/valasztokeruletek?p_auth=07O4kcB9&p_p_id=pairproxy_WAR_pairproxyportlet_" +
        "INSTANCE_9xd2Wc9jP4z8&p_p_lifecycle=1&p_p_state=normal&p_p_mode=view&p_p_col_id=column-1&p_p_col_count=1&_" +
        "pairproxy_WAR_pairproxyportlet_INSTANCE_9xd2Wc9jP4z8_pairAction=%2Finternet%2Fcplsql%2Fogy_kpv.kepv_" +
        "valkorzet%3FP_EGYENI%3DI%26P_VKSZ%3Dnull%26P_CIKLUS%3DNULL%26P_VALKORZET%3Dnull%26P_MEGYE%3Dnull%26P_" +
        "VALKER%3Dnull%26P_LISTAS%3DI%26P_CKL%3D40",
    ]

    def parse(self, response):
        data = response.xpath('//center//tbody/tr')
        field_names = map(lambda x: x.replace(', ', '_'), data[0].xpath('th/text()').extract())
        field_names += ['link', 'pid']
        writer = unicodecsv.DictWriter(open('main_table.csv', 'wb'), field_names)
        writer.writeheader()
        row_before = dict()
        pid_to_link = dict()
        for item in data[1:]:
            item.xpath('td//text()')
            in_values = item.xpath('td')
            link = item.xpath('td/a/@href').extract()[0]
            pid = id_pattern.findall(link)[0]
            out_values = map(extract_text, in_values) + [link, pid]
            row = repair_row(dict(zip(field_names, out_values)), row_before)
            writer.writerow(row)
            row_before = row
            pid_to_link[pid] = link
        for pid, link in pid_to_link.iteritems():
            yield scrapy.Request(link, callback=parse_individual)
