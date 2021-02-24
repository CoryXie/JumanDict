# -*- coding: utf-8 -*-
from pyknp import Juman
from pyknp import KNP
from jamdict import Jamdict
import sqlite3
import sys

jmd = Jamdict()
knp = KNP()

jumandict = sqlite3.connect("records.db")
dictcursor = jumandict.cursor()
dictcursor.execute("CREATE TABLE IF NOT EXISTS words (id INTEGER PRIMARY KEY, name TEXT UNIQUE, desc TEXT, count INTEGER)")

while True:
#    line = input('请输入日语句子：')
#    while not line:
#        print('你啥都没输入哦！')
#        line = input('请输入日语句子：')

    lines = ""
    while True:
        if lines == "":
            print("你已经保存过：")
            rows = dictcursor.execute("SELECT id, name, desc, count FROM words").fetchall()
            for row in rows:
                print('{} [{} ({}次)]:\n'.format(row[0], row[1], row[3]))
                print(row[2])
            print("请输入日语句子：")
        x = input()
        if x == "" and lines != "":
            break
        else:
            lines += x

    userinput = lines.strip()
    #userinput = userinput.replace("\␣", "")
    if userinput == 'q':
        break

    print("=================================")
    print(userinput)
 
    result = knp.parse(userinput)

#   print("=================================")
#   print("词组")
#   for bnst in result.bnst_list(): # 访问每个词组
#       print("\tID:%d, 标题:%s, 依赖类型:%s, 父词组ID:%d, 特征:%s" \
#               % (bnst.bnst_id, "".join(mrph.midasi for mrph in bnst.mrph_list()), bnst.dpndtype, bnst.parent_id, bnst.fstring))

#   print("=================================")
#   print("基本句")
#   for tag in result.tag_list(): # 访问每个基本句
#       print("\tID:%d, 标题:%s, 依赖类型:%s, 父基本句ID:%d, 特征:%s" \
#               % (tag.tag_id, "".join(mrph.midasi for mrph in tag.mrph_list()), tag.dpndtype, tag.parent_id, tag.fstring))

    print("=================================")
    print("词素")
    for mrph in result.mrph_list(): # 访问每个词素
        if mrph.midasi in {"、", "。", "「", "」", "\␣"}:
            continue
        print("\tID:%d, 标题:%s, 读法:%s, 原形:%s, 词性:%s, 词性细分:%s, 活用型:%s, 活用形:%s, 语义信息:%s, 代表符号:%s" \
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

#   print("=================================")
#   print("基本句树")
#   result.draw_tag_tree()

#    print("=================================")
#    print("词组树")
#    result.draw_bnst_tree()

    print("=================================")
    length = 0
    for bnst in result.bnst_list(): # 访问每个词组
        phrase = "".join(mrph.midasi for mrph in bnst.mrph_list())
        phrase = phrase.replace("\␣", " ")
        print("  " * length + phrase)
        length = length + len(phrase)

jumandict.close()