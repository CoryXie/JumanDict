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
@click.option('--guimode', '-g', default="web", help='GUI mode to be used for interacting with user.')
def mainloop(file, database, savedump, records, orderby, guimode):
    """Get user Janpanse input then parse it and record new words into database."""
    jmd = Jamdict()
    knp = KNP()

    jumandict = sqlite3.connect(database)
    dictcursor = jumandict.cursor()
    dictcursor.execute("CREATE TABLE IF NOT EXISTS words (id INTEGER PRIMARY KEY, name TEXT UNIQUE, desc TEXT, count INTEGER)")
    dumper = open(savedump, 'w')

    # Pass any command line argument for Web use 
    if guimode == "web": # if there is use the Web Interface 
        import PySimpleGUIWeb as sg
        import socket
    elif guimode == "tk": # default uses the tkinter GUI
        import PySimpleGUI as sg
    elif guimode == "qt":
        import PySimpleGUIQt as sg
    else:
        import PySimpleGUIWx as sg

    # All the stuff inside your window.
    header_list = ["ID", "词汇", "读法", "原形", "词性", "词性细分", "活用型", "活用形", "语义信息", "代表符号"]
    uifont = "Ariel 32"
    left_column_layout = [
        [sg.T("输入日语"), sg.FolderBrowse(),],
        [sg.Multiline("", size=(60,10) , key="nihongo"),],
        [sg.Button("分析", size=(30,3), font=uifont, button_color=('white','green'), key="submit"),
         sg.Button("退出", size=(30,3), font=uifont, button_color=('white','red'), key="exit")],
        [sg.Listbox(values=[], enable_events=True, size=(60, 20), key="parsedwords")],
    ]
    right_column_layout = [
        [sg.T("词汇意义")],
        [sg.Listbox(values=[], enable_events=True, size=(60, 35), key="foundentries")],
    ]
    layout = [
        [
            sg.VSeperator(),
            sg.Column(left_column_layout),
            sg.VSeperator(),
            sg.Column(right_column_layout),
        ]
    ]
    # Create the Window
    if guimode == "web":
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print("local_ip is " + local_ip)
        window = sg.Window('日语学习', layout,
            web_ip=local_ip, web_port = 8888, web_start_browser=False)
    else:
        window = sg.Window('日语学习', layout)

    resultlist = []
    # Run the Event Loop
    while True:
        event, values = window.read()
        if event == "exit" or event == sg.WIN_CLOSED:
            break
        # Folder name was filled in, make a list of files in the folder
        if event == "submit":
            userinput = values["nihongo"]
            print("=================================")
            print(userinput)
            userinput = userinput.strip()
            userinput = userinput.encode('utf-8','surrogatepass').decode('utf-8')

            dumper.write(userinput + "\n\n")

            result = knp.parse(userinput.replace("\n", ""))

            print("=================================")
            print("词素")
            resultlist = result.mrph_list()
            parsedwords = []
            for mrph in resultlist: # 访问每个词素
                if mrph.midasi in {"、", "。", "「", "」", "\␣"}:
                    continue
                message = "\tID:{}, 词汇:{}, 读法:{}, 原形:{}, 词性:{}, 词性细分:{}, 活用型:{}, 活用形:{}, 语义信息:{}, 代表符号:{}".format(
                    mrph.mrph_id, mrph.midasi, mrph.yomi, mrph.genkei, mrph.hinsi, mrph.bunrui, mrph.katuyou1, mrph.katuyou2, mrph.imis, mrph.repname);
                print(message)
                dumper.write(message + "\n")
                parsedwords += [message]

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
            window["parsedwords"].update(parsedwords)

        elif event == "parsedwords":  # A file was chosen from the listbox
            selectedword = values["parsedwords"][0]
            print(selectedword)
            selectedid = int(selectedword.split(',')[0].split(':')[1].strip())
            print("selectedid=" + str(selectedid) + " among " + str(len(resultlist)) + " entries")
            foundentries = []
            for mrph in resultlist: # 访问每个词素
                print("mrph.mrph_id=" + str(mrph.mrph_id))
                if selectedid != mrph.mrph_id:
                    continue
                message = "\tID:{}, 词汇:{}, 读法:{}, 原形:{}, 词性:{}, 词性细分:{}, 活用型:{}, 活用形:{}, 语义信息:{}, 代表符号:{}".format(
                    mrph.mrph_id, mrph.midasi, mrph.yomi, mrph.genkei, mrph.hinsi, mrph.bunrui, mrph.katuyou1, mrph.katuyou2, mrph.imis, mrph.repname);
                print(message)
                # use exact matching to find exact meaning
                dictcheck = jmd.lookup(mrph.genkei)
                if len(dictcheck.entries) == 0:
                    dictcheck = jmd.lookup(mrph.midasi)
                    if len(dictcheck.entries) == 0:
                        dictcheck = jmd.lookup(mrph.yomi)
                foundentries += [message]
                foundentries += ["==================================="]
                if len(dictcheck.entries) > 0:
                    for entry in dictcheck.entries:
                        desc = entry.text(compact=False, no_id=True)
                        print("\n" + desc)
                        foundentries += [desc]
            
            window["foundentries"].update(foundentries)

    window.close()
    jumandict.close()
    dumper.close()

if __name__ == '__main__':
    mainloop()
