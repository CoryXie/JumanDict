# JumanDict
A Japanese Study Tool based on Juman &amp; KNP &amp; Jamdict.

# Why JumanDict?

Japanese is a complex language, it builds up a sentence with mix of Kanji and Kana (hiragana and katakana) without good sign of word boundary (like the whitespace in English). So if you are not taught of a word, seeing it the 1st time in a sentence, without good knowledge of the language itself (like what can be a sign of word/clause boundary), you will be at hard time. This is a basic problem that I had when trying to learn Japanese (Nihongo) - how to read through a Japanse sentence with correct words broken down - I had even a problem in selecting the part of a sentence to search on Google.

So I need a tool to help break down the setence in grammarly correct parts, better, it can help get to the meaning of these words automatically. I also wanted to be able to save these words ever leart (meaning I tried to search for their meanings) and be able to review later, better, it can help me get the frequence it occured to me (thus the significance of remembering these words).

With these expectations, I found some way to breakdown the sentence into grammarly correct parts using Juman (https://github.com/ku-nlp/jumanpp) and further KNP (https://github.com/ku-nlp/knp), further, based on the borken down parts (the dictionary form of words) I can search through the dictionary (https://github.com/neocl/jamdict) to get to the meaning. I could then use Python with SQLite to save the words from the sentences I searched, with meaning and occurence count (frequence) information.

# Current Status

Currently it is a POC rototype with basic CLI loop, accepting a sentence or a paragraph and shows everything it parses, recording in a SQLite database and shows the recordings on each loop.

# Next Plans

- Make the code more organized for better evolution.
- Add GUI support with more ways to interact with.

