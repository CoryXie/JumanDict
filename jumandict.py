# -*- coding: utf-8 -*-
from pyknp import Juman
from pyknp import KNP
from jamdict import Jamdict
import sqlite3
import sys
import click

jmd = Jamdict()
knp = KNP()

jumandict = sqlite3.connect("records.db")
dictcursor = jumandict.cursor()
dictcursor.execute("CREATE TABLE IF NOT EXISTS words (id INTEGER PRIMARY KEY, name TEXT UNIQUE, desc TEXT, count INTEGER)")

while True:
    try:
        if not click.confirm('想要进入编辑器输入日文句子或段落进行分析吗?'):
            continue
    except EOFError:
        break
    except click.Abort:
        break
    rows = dictcursor.execute("SELECT id, name, desc, count FROM words").fetchall()
    words = len(rows)
    if words > 0:
        print("已经分析并保存过{}个单词：".format(words))
    for row in rows:
        print('{} [{} ({}次)]:\n'.format(row[0], row[1], row[3]))
        print(row[2])

    userinput = click.edit()
    if userinput is None:
        print("你啥也没输入啊！")
        continue

    userinput = userinput.strip()
    userinput = userinput.encode('utf-8','surrogatepass').decode('utf-8')
    if userinput == 'q':
        break

    print("=================================")
    print(userinput)
 
    result = knp.parse(userinput)

    print("=================================")
    print("词素")
    for mrph in result.mrph_list(): # 访问每个词素
        if mrph.midasi in {"、", "。", "「", "」", "\␣"}:
            continue
        print("\tID:%d, 词汇:%s, 读法:%s, 原形:%s, 词性:%s, 词性细分:%s, 活用型:%s, 活用形:%s, 语义信息:%s, 代表符号:%s" \
                % (mrph.mrph_id, mrph.midasi, mrph.yomi, mrph.genkei, mrph.hinsi, mrph.bunrui, mrph.katuyou1, mrph.katuyou2, mrph.imis, mrph.repname))
        # use exact matching to find exact meaning
        dictcheck = jmd.lookup(mrph.genkei)
        if len(dictcheck.entries) == 0:
            dictcheck = jmd.lookup(mrph.midasi)
            if len(dictcheck.entries) == 0:
                dictcheck = jmd.lookup(mrph.yomi)
        if len(dictcheck.entries) > 0:
            desc = ""
            for entry in dictcheck.entries:
                desc = desc + entry.text(compact=False, no_id=True) + "\n"
            #if mrph.hinsi in {"名詞", "形容詞", "動詞", "接続詞", "指示詞", "副詞"}:
            print("\n" + desc)
            dictcursor.execute('INSERT INTO words (name, desc, count) VALUES ("{}", "{}", "{}") ON CONFLICT (name) DO UPDATE SET count = count + 1'
                                .format(mrph.genkei.replace('"', '""'), desc.replace('"', '""'), 1))
    jumandict.commit()

    print("=================================")
    print(userinput)
    print("=================================")
    length = 0
    for bnst in result.bnst_list(): # 访问每个词组
        phrase = "".join(mrph.midasi for mrph in bnst.mrph_list())
        phrase = phrase.replace("\␣", " ")
        print("  " * length + phrase)
        length = length + len(phrase)
        if length > 80:
            length = 0

print("\n你选择退出了哦！")
jumandict.close()