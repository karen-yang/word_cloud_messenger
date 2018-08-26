#!/usr/bin/python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import os 
from wordcloud import WordCloud
import numpy as np
import re
from collections import Counter 
from PIL import Image, ImageDraw, ImageFont
import emoji


def seperate_message(s, names):
    ignores = ['Dec', 'Nov', 'Oct' , 
               'Sep ','Aug ', 'Jul ', 
               'Jun ', 'May ','Apr ', 
               'Mar ','Feb ', 'Jan ',
               'https://'] + list(names)
    for m in ignores:
        i = s.find(m)
        if i != -1:
            s =  s[:i]
    return s

def extract_html_to_txt(read_file, record_chat, output_dir):
    print("Extracting html into txt .....")
    with open(read_file) as fp:
        soup = BeautifulSoup(fp, 'lxml')
    names = soup.findAll('div',attrs={"class":"_3-96 _2pio _2lek _2lel"})
    names_count = Counter([n.text for n in names])
    for k in names_count.keys():
        print(k, 'had', names_count[k], 'messages in this chat history.\n')
    
    names = list(names_count.keys())

    alltext = soup.text
    texts = []
    for i in range(len(names)):
        person = alltext.split(names[i])
        person_cleaned= []
        for t in person[1:]: # ignore first
            person_cleaned.append(seperate_message(t, names)) 
        filename = '{}/{}_chat.txt'.format(output_dir, '_'.join(names[i].split()))
        if(record_chat):
            with open(filename, 'w') as fp:
                for text in person_cleaned:
                    fp.write('%s\n' % text)
            print(filename , "generated.\n")
        texts.append('\n'.join(person_cleaned))
    return texts, names

def get_emoji_frequency(text):
    emoji_pattern =  re.compile(
            '[\U00002000-\U0010ffff]', 
            flags=re.UNICODE)
    _emojiCounter = Counter(emoji_pattern.findall(text))
    emojiCounter= Counter()
    for w in _emojiCounter:
        if w not in ['’','','-','“','”','‘','️','—','⬜']:   # ignore criterion
            emojiCounter[w] = _emojiCounter[w]  
    return emojiCounter

def get_word_frequency(text):
    _wordcounter = Counter(text.split(" "))
    stopwords = open("stopwords.txt",'r').read().lower().split()
    wordCounter = Counter()
    for w in _wordcounter:
        if w.lower() not in stopwords and len(w) > 3:   # ignore criterion
            wordCounter[w] = _wordcounter[w] 
    return wordCounter

def generate_image(freq):
    heart_mask = np.array(Image.open("heart.png"))
    wc = WordCloud(background_color="white", max_words=min(300,len(freq)),
                     mask=heart_mask)
    wc =  wc.generate_from_frequencies(freq)
    img = wc.to_image()
    return img

def ngrams(words, length):
    return zip(*[words[i:] for i in range(length)])

def extract_phrases(text,length):
    phrase_counter = Counter()
    text=text.lower()
    for sent in text.split('\n'):
        words = sent.split()
        for phrase in ngrams(words, length):
            if not np.array([ s in phrase for s in ['’',':',' ',',','click','.','a'] ]).any():
                phrase_counter[phrase] += 1
    return phrase_counter
 
def main(message_file, record_chat, output_dir):
    # parse messages from FB chat

    try:
        os.stat(output_dir)
    except:
        os.mkdir(output_dir)   

    texts, names = extract_html_to_txt(message_file, record_chat, output_dir)

    font = ImageFont.truetype("Symbola.ttf", 20)
    for i in range(len(names)):
        phrase_counter = extract_phrases(texts[i],3)
        print("{}'s 10 most frequent 3-word phrases: ".format('_'.join(names[i].split())))
        for p in phrase_counter.most_common(10):
            print(' '.join(p[0]),':',p[1])

        word_frequqncy = get_word_frequency(texts[i]) 
        emoji_frequency = get_emoji_frequency(texts[i])
        image = generate_image(word_frequqncy)
        
        # add text onto image
        draw = ImageDraw.Draw(image)
        W,H = image.size
        
        # words 
        draw.text(
            (W*1/5,H*9/10), 
            "{}'s 10 most frequent words: ".format('_'.join(names[i].split())), 
            font=font,fill=(0,0,0))
        most_frequent_str = ""
        print("{}'s 10 most frequent words: \n".format('_'.join(names[i].split())),word_frequqncy.most_common(10))
        for w in word_frequqncy.most_common(10):
            most_frequent_str +=  w[0] + ": " + str(w[1]) + "  "
        draw.text(
            (W*1/5,H*9/10+25), 
            most_frequent_str, 
            font=font,fill=(0,0,0))

        # emojis
        if len(emoji_frequency) >= 1 :
            draw.text(
                (W*1/5,H*9/10+25*2), 
                "{}'s 5 most frequent emojis: ".format('_'.join(names[i].split())), 
                font=font,fill=(0,0,0))
            most_frequent_str = ""
            print("{}'s 5 most frequent emojis: \n".format('_'.join(names[i].split())), emoji_frequency.most_common(5))
            for w in emoji_frequency.most_common(5):
                most_frequent_str += w[0] + ": " + str(w[1]) + "  "
            draw.text(
                (W*1/5,H*9/10+25*3), 
                most_frequent_str, 
                font=font,fill=(0,0,0))

        # save image
        filename = '{}/{}_wordcloud.png'.format(output_dir,'_'.join(names[i].split()))
        image.save(filename, format='png', optimize=True)
        print('{} generated \n'.format(filename))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Parse your chat history with someone (message.html)  to generate word cloud image in the shape of a heart.')
   
    parser.add_argument('-f','--message_file', dest='message_file', default='message.html',
                        help='path to message.html file. Default is current directory.')
    parser.add_argument('-r','--record', dest='record_chat', action='store_true',
                        help='If set, will write a chat file for each person in the chat.')
    parser.add_argument('-o', '--output_dir', dest='output_dir', default='out',
                        help='Directory to store the output files.')


    args = parser.parse_args()


    main(args.message_file, args.record_chat, args.output_dir)

   