#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pyknp import Juman
from pyknp import KNP
from jamdict import Jamdict
import configparser
import sqlite3
import sys
import click
import re
import requests
import random
import json
from hashlib import md5

# Generate salt and sign
def make_md5(s, encoding='utf-8'):
    return md5(s.encode(encoding)).hexdigest()

@click.command()
@click.option('--file', '-f', default="", help='File to be analyzed for study.')
@click.option('--savedump', '-s', default="dumping.md", help='File to be saved with dump for study.')
@click.option('--database', '-d', default="records.db", help='Database file to be used for record saving.')
@click.option('--cfgfile', '-i', default="config.ini", help='Config file to be used.')
@click.option('--records', '-r', default=5, help='Number of history records to show.')
@click.option('--orderby', '-o', default="id", type=click.Choice(['id', 'count'], case_sensitive=False),
                help='Sort order of history records to show.')
@click.option('--compact', '-c', default="false", type=click.Choice(['true', 'false'], case_sensitive=False),
                help='Whether use compat form of senses')
@click.option('--known', '-k', default="knownlist.cfg", help='File with known words not to shown.')
@click.option('--verbose', '-v', default="half", type=click.Choice(['full', 'half', 'none'], case_sensitive=False),
                help='Whether verbose showing all words even known')
@click.option('--nosense', '-n', default="false", type=click.Choice(['true', 'false'], case_sensitive=False),
                help='Whether disable all senses')
@click.option('--translate', '-t', default="true", type=click.Choice(['true', 'false'], case_sensitive=False),
                help='Whether translate inputs')
@click.option('--destlang', '-l', default="zh", type=click.Choice(['zh', 'cht', 'en'], case_sensitive=True),
                help='Which target language to translate')
def mainloop(file, savedump, database, cfgfile, records, orderby, compact, known, verbose, nosense, translate, destlang):
    """Get user Janpanse input then parse it and record new words into database."""
    jmd = Jamdict()
    knp = KNP()

    knownlist = {}
    with open(known, 'r') as reader:
        lines = reader.readlines()
        for line in lines:
            if re.match("^#", line):
                continue
            entry = line.split(",")
            if len(entry) == 2:
                knownlist[entry[0].strip()] = entry[1].strip()

    appid = ""
    appkey = ""
    if translate == "true":
        # See https://fanyi-api.baidu.com/
        # See https://fanyi-api.baidu.com/api/trans/product/desktop?req=developer
        # See https://docs.python.org/3/library/configparser.html
        config = configparser.ConfigParser()
        config.read(cfgfile)
        # Set your own appid/appkey.
        appid = config['api.fanyi.baidu.com']['appid']
        appkey = config['api.fanyi.baidu.com']['appkey']
        #print("appid=" + appid)
        #print("appkey=" + appkey)

    jumandict = sqlite3.connect(database)
    dictcursor = jumandict.cursor()
    dictcursor.execute("CREATE TABLE IF NOT EXISTS words (id INTEGER PRIMARY KEY, name TEXT UNIQUE, desc TEXT, count INTEGER)")
    dumper = open(savedump, 'w')
    dumper.write("# 日语学习记录\n\n")

    while True:
        userinputs = ""
        if file == "":
            try:
                if not click.confirm('想要进入编辑器输入日文句子或段落进行分析吗?'):
                    continue
            except EOFError:
                print("\n你选择退出了哦！")
                break
            except click.Abort:
                print("\n你选择退出了哦！")
                break

            if records > 0:
                rows = dictcursor.execute("SELECT id, name, desc, count FROM words ORDER BY {} DESC LIMIT {}".format(orderby, records)).fetchall()
                words = len(rows)
                if words > 0:
                    if orderby == "id":
                        print("最近保存过的{}个单词（最近优先排序）：".format(words))
                    else:
                        print("出现频率最高的{}个单词（高频优先排序）：".format(words))
                count = 0
                for row in rows:
                    print('{} [{} ({}次)]:\n'.format(row[0], row[1], row[3]))
                    print(row[2])

            userinputs = click.edit()
            if userinputs is None:
                print("你啥也没输入啊！")
                continue
        else:
            with open(file, 'r') as reader:
                lines = reader.readlines()
                userinputs = "".join(lines)

        if translate == "true":
            # For list of language codes, please refer to `https://api.fanyi.baidu.com/doc/21`
            from_lang = 'jp'
            to_lang = destlang

            endpoint = 'http://api.fanyi.baidu.com'
            path = '/api/trans/vip/translate'
            url = endpoint + path

            salt = random.randint(32768, 65536)
            sign = make_md5(appid + userinputs + str(salt) + appkey)

            # Build request
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            payload = {'appid': appid, 'q': userinputs, 'from': from_lang, 'to': to_lang, 'salt': salt, 'sign': sign}

            # Send request
            r = requests.post(url, params=payload, headers=headers)
            result = r.json()

            # Show response
            print("=================================")
            print(userinputs)
            dumper.write("```\n")
            dumper.write(userinputs)
            print("=================================")
            dumper.write("=================================\n")
            trans_result = result["trans_result"]
            for i in range(len(trans_result)):
                dst = trans_result[i]["dst"]
                print(dst)
                dumper.write(dst + "\n")
            dumper.write("```\n")

        inputsentences = [x+"。" for x in userinputs.split("。") if x.strip() != ""]
        for userinput in inputsentences:
            userinput = userinput.strip()
            userinput = userinput.encode('utf-8','surrogatepass').decode('utf-8')

            print("=================================")
            print(userinput)
            dumper.write("## "+ userinput + "\n\n")

            result = knp.parse(userinput.replace("\n", ""))
            dumper.write("```\n")
            dumper.write(userinput + "\n")
            length = 0
            for bnst in result.bnst_list(): # 访问每个词组
                phrase = "".join(mrph.midasi for mrph in bnst.mrph_list())
                phrase = phrase.replace("\␣", " ")
                print("  " * length + phrase)
                dumper.write("  " * length + phrase + "\n")
                length = length + len(phrase)
                if length > 80:
                    length = 0

            dumper.write("```\n")
            print("=================================")
            for mrph in result.mrph_list(): # 访问每个词素
                found = False
                for known in knownlist.keys():
                    if mrph.genkei == known:
                        types = knownlist[known].split("|")
                        for type in types:
                            if mrph.hinsi == type:
                                found = True
                                break

                if ((found == True) and (verbose == "none")) or (mrph.hinsi == "特殊"):
                    continue

                message = "ID:{}".format(mrph.mrph_id)
                if mrph.midasi:
                    message += ", 词汇:{}".format(mrph.midasi)
                if mrph.yomi:
                    message += ", 读法:{}".format(mrph.yomi)
                if mrph.genkei:
                    message += ", 原形:{}".format(mrph.genkei)
                if mrph.hinsi and mrph.hinsi != "*":
                    message += ", 词性:{}".format(mrph.hinsi)
                if mrph.bunrui and mrph.bunrui != "*":
                    message += ", 词性细分:{}".format(mrph.bunrui)
                if mrph.katuyou1 and mrph.katuyou1 != "*":
                    message += ", 活用型:{}".format(mrph.katuyou1)
                if mrph.katuyou2 and mrph.katuyou2 != "*":
                    message += ", 活用形:{}".format(mrph.katuyou2)
                if mrph.imis and mrph.imis != "NIL":
                    message += ", {}".format(mrph.imis) #语义信息:
                elif mrph.repname:
                    message += ", 代表符号:{}".format(mrph.repname)
                print("\t" + message)
                dumper.write("### " + message + "\n")

                if nosense == "true" or (found == True and verbose == "half"):
                    continue

                # use exact matching to find exact meaning
                dictcheck = jmd.lookup(mrph.genkei)
                if len(dictcheck.entries) == 0:
                    dictcheck = jmd.lookup(mrph.midasi)
                    if len(dictcheck.entries) == 0:
                        dictcheck = jmd.lookup(mrph.yomi)
                if len(dictcheck.entries) > 0:
                    desc = ""
                    print("\n")
                    dumper.write("\n")
                    for entry in dictcheck.entries:
                        text = ""
                        if compact == "true":
                            text = entry.text(compact=False, no_id=True)
                            text = re.sub('[`\']', '"', text)
                            print(text)
                        else:
                            tmp = []
                            if entry.kana_forms:
                                tmp.append(entry.kana_forms[0].text)
                            if entry.kanji_forms:
                                tmp.append("({})".format(entry.kanji_forms[0].text))
                            header = " ".join(tmp)
                            tmp = []
                            if entry.senses:
                                for sense, idx in zip(entry.senses, range(len(entry.senses))):
                                    tmps = [str(x) for x in sense.gloss]
                                    if sense.pos:
                                        s = '{gloss} ({pos})'.format(gloss='/'.join(tmps), pos=('(%s)' % '|'.join(sense.pos)))
                                    else:
                                        s = '/'.join(tmps)
                                    s = re.sub('[`\']', '"', s)
                                    tmp.append('    {i}. {s}\n'.format(i=idx + 1, s=s))
                            senses = "".join(tmp)
                            print(header)
                            print(senses)
                            text = "**" + header + "**\n" + senses
                        desc = desc + text + "\n"
                        text = re.sub('[|]', '\|', text)
                        dumper.write("- " + text + "\n")
                    dictcursor.execute('INSERT INTO words (name, desc, count) VALUES ("{}", "{}", "{}") ON CONFLICT (name) DO UPDATE SET count = count + 1'
                                        .format(mrph.genkei.replace('"', '""'), desc.replace('"', '""'), 1))
            jumandict.commit()

        dumper.flush()

        if file != "":
            break

    jumandict.close()
    dumper.close()

if __name__ == '__main__':
    mainloop()
