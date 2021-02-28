#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pyknp import Juman
from pyknp import KNP
from jamdict import Jamdict
import sqlite3
import sys
import click

@click.command()
@click.option('--file', '-f', default="", help='File to be analyzed for study.')
@click.option('--savedump', '-s', default="dumping.txt", help='File to be saved with dump for study.')
@click.option('--database', '-d', default="records.db", help='Database file to be used for record saving.')
@click.option('--records', '-r', default=5, help='Number of history records to show.')
@click.option('--orderby', '-o', default="id", type=click.Choice(['id', 'count'], case_sensitive=False),
                help='Sort order of history records to show.')
def mainloop(file, database, savedump, records, orderby):
    """Get user Janpanse input then parse it and record new words into database."""
    jmd = Jamdict()
    knp = KNP()

    jumandict = sqlite3.connect(database)
    dictcursor = jumandict.cursor()
    dictcursor.execute("CREATE TABLE IF NOT EXISTS words (id INTEGER PRIMARY KEY, name TEXT UNIQUE, desc TEXT, count INTEGER)")
    dumper = open(savedump, 'w')

    while True:
        userinput = ""
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

            userinput = click.edit()
            if userinput is None:
                print("你啥也没输入啊！")
                continue
        else:
            with open(file, 'r') as reader:
                lines = reader.readlines()
                userinput = "".join(lines)

        userinput = userinput.strip()
        userinput = userinput.encode('utf-8','surrogatepass').decode('utf-8')

        print("=================================")
        print(userinput)
        dumper.write(userinput + "\n\n")

        result = knp.parse(userinput.replace("\n", ""))

        print("=================================")
        print("词素")
        for mrph in result.mrph_list(): # 访问每个词素
            if mrph.midasi in {"、", "。", "「", "」", "\␣"}:
                continue
            message = "\tID:{}, 词汇:{}, 读法:{}, 原形:{}, 词性:{}, 词性细分:{}, 活用型:{}, 活用形:{}, 语义信息:{}, 代表符号:{}".format(
                mrph.mrph_id, mrph.midasi, mrph.yomi, mrph.genkei, mrph.hinsi, mrph.bunrui, mrph.katuyou1, mrph.katuyou2, mrph.imis, mrph.repname);
            print(message)
            dumper.write(message + "\n")
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
                dumper.write("\n" + desc + "\n")
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

        if file != "":
            break

    jumandict.close()
    dumper.close()

if __name__ == '__main__':
    mainloop()
