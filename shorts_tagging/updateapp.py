import pandas as pd
import re
import numpy as np
from wordcloud import WordCloud
from wordcloud import WordCloud, ImageColorGenerator
from wordcloud import WordCloud, STOPWORDS 
import matplotlib.pyplot as plt
from collections import Counter 
import requests
import re
import random
from PIL import Image
import requests
from io import BytesIO
import glob
import pandas as pd
import requests
from bs4 import BeautifulSoup
import concurrent.futures

NUM_THREADS = 5

## Example list of urls to scrape
llist = []
def scrape_page(url):
    try:
        response = requests.get(url)
        print(response.url)
        print(response.history)
        if url == response.url:
            print(response.url)
            print(response.history)
            lin = url.split('/')[-1]
            print(url)
            llist.append(lin)
    except:pass   

files = glob.glob("Input/*.xlsx")
print('*******************  READ FILES +++++++++++++++++++++')
dfs = [pd.read_excel(f) for f in files]
df = pd.concat(dfs)

try:
    flag = input(str('Do You Want Sorts By Request Type Yes/yes Or No >>>>'))
    if flag == 'Yes' or flag == 'yes':
        df['Duration'] = df['Duration'].astype(str).replace('NONE',0)
        asd = df[(df['Duration'].astype(int) >= 1) & (df['Duration'].astype(int) <= 181)]
        asd['link'] = 'https://www.youtube.com/shorts/' + asd['Video_id'] 
        list_of_urls = asd['link'].to_list() 
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            executor.map(scrape_page, list_of_urls)
        asdf = pd.DataFrame({'Video_Id':llist})
        df1 = df[df["Video_id"].isin(asdf["Video_Id"])]
        df1['Shorts'] = 'Shorts'
        df = pd.concat([df1,df])
        
        df = df.drop_duplicates(subset = 'Video_id')
except:
    df = pd.concat(dfs)

df = df.replace(np.nan, 0)# changes in new libary
df['Duration'] = df['Duration'].astype(str).replace('NONE',0)

df['Duration_Min'] = (df['Duration'].astype(float) / 60).round(2)
df['Duration_Min'] = df['Duration_Min'].apply("int64")# changes in new libary

df['Duration_Between'] = np.select(
    [df['Duration_Min'] > 30,
     df['Duration_Min'] < 1,
     df['Duration_Min'].between(1, 2),
     df['Duration_Min'].between(2, 5),
     df['Duration_Min'].between(5, 10),
     df['Duration_Min'].between(10, 30)],

    ['30Min+', 'Below_1Min', '1-2Min', '2-5Min','5-10Min','10-30Min'],
    np.nan
)
df['View_count'] = df['View_count'].replace('NONE','0')
df['View_count'] = df['View_count'].astype(int)

df['View_count_Between'] = np.select(
    [df['View_count'] > 1000000,
     df['View_count'] < 100000,
     df['View_count'].between(100000, 500000),
    
     df['View_count'].between(500000, 1000000)],

    ['10Lakh+', 'below_1Lakh', '1-5Lakh', '5-10Lakh'],
    np.nan
)

df['Like_count'] = df['Like_count'].replace('NONE','0')

df['Comment_count'] = df['Comment_count'].replace('NONE','0')

tag = pd.read_excel('TAGFILE.xlsx')

import re

def pattern_searcher(search_str:str, search_list:str):

    search_obj = re.search(search_list, search_str)
    if search_obj :
        return_str = search_str[search_obj.start(): search_obj.end()]
    else:
        return_str = ''
    return return_str

Anchor = tag['Anchor'].dropna().unique().tolist()

Program = tag['Program'].dropna().unique().tolist()

def Anchor_matcher(x):
    for i in Anchor:
        if i.lower() in x.lower():
            return i.lower().replace('#','')
    else:
        return np.nan

def Program_matcher(x,y):
    for i in Program:
        if 'DNA' in x and y =='UCIvaYmXn910QMdemBG3v1pQ':
            return 'dna'
        elif 'OMG' in x and y =='UCttspZesZIDEwwpVIgoZtWQ':
            return 'omg'
        elif i.lower() in x.lower():
            return i.lower().replace('#','')
    else:
        return np.nan
try:
    df['Anchor_Name_In_Title'] = df['Title'].apply(Anchor_matcher)
    df["Anchor_Name_In_Title"] = df["Anchor_Name_In_Title"].str.replace('SudhirChaudhary','sudhir chaudhary').replace('sudhirchaudhary','sudhir chaudhary')
    df["Anchor_Name_In_Title"] = df["Anchor_Name_In_Title"].str.replace('ChitraTripathi','Chitra Tripathi')
except:pass
try:    
    df['Program_Name_In_Title'] = df.apply(lambda x: Program_matcher(x['Title'], x['Channel_id']), axis=1)
    df["Program_Name_In_Title"] = df["Program_Name_In_Title"].str.replace('blackandwhite','Black & White').replace('black and white','black & white').replace('dastak','dastak')
except:
    pass
try:
    df["#Aajtakdigital_In_Title_&_Description"] = df[['Title', 'Description']].apply(lambda x: x.str.contains('#aajtakdigital',case=False)).any(axis=1).astype(str)
    df["#Aajtakdigital_In_Title_&_Description"] = df["#Aajtakdigital_In_Title_&_Description"].str.replace('False','').replace('True','#aajtakdigital')
except:
    pass
try:
    df["AT2_In_Title_&_Description"] = df[['Title', 'Description']].apply(lambda x: x.str.contains('AT2',case=False)).any(axis=1).astype(str)
    df["AT2_In_Title_&_Description"] = df["AT2_In_Title_&_Description"].str.replace('False','').replace('True','AT2')
except:
    pass
try:
    df["#Shorts_In_Title_&_Description"] = df[['Title', 'Description']].apply(lambda x: x.str.contains('#Shorts',case=False)).any(axis=1).astype(str)
    df["#Shorts_In_Title_&_Description"] = df["#Shorts_In_Title_&_Description"].str.replace('False','').replace('True','#shorts')
except:
    pass
try:
    df["#tvchunks_In_Description"] = df['Description'].str.contains('#tvchunks',case=False).astype(str)
    df["#tvchunks_In_Description"] = df["#tvchunks_In_Description"].str.replace('False','').replace('True','#tvchunks')
except:
    pass
try:
    df["#TV9D_In_Title"] = df['Title'].str.contains('#TV9D',case=False).astype(str)
    df["#TV9D_In_Title"] = df["#TV9D_In_Title"].str.replace('False','').replace('True','#tv9d')
except:
    pass
try:
    df["Breaking_In_Title"] = df['Title'].str.contains('Breaking',case=False).astype(str)
    df["Breaking_In_Title"] = df["Breaking_In_Title"].str.replace('False','').replace('True','breaking')
except:
    pass

def Convert(string):
    li = list(string.split(","))
    return li

tag.drop(['Program','Anchor','#Aajtakdigital_In_Title_&_Description','AT2_In_Title_&_Description','#Shorts_In_Title_&_Description','#tvchunks_In_Description','#TV9D_In_Title','Breaking_In_Title'],axis = 1, inplace = True)
for (colname,colval) in tag.items():# changes in new libary
    print(colname, [x for x in colval.values if str(x) != 'nan'])
    title = colname
    values = [x for x in colval.values if str(x) != 'nan']
    mylist = Convert(''.join(values))
    if len(mylist[0]) <= 3:
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.')
        pattern = '|'.join(mylist)
        df[str(title)+"_In_Title"]  = df['Title'].str.contains(pattern,na=False).astype(str)
        df[str(title)+"_In_Title"]  = df[str(title)+"_In_Title"].astype(str)
        df[str(title)+"_In_Title"]  = df[str(title)+"_In_Title"].replace('False','').replace('True',str(title).lower())
        # import pdb;pdb.set_trace()
    else:
        try:
            print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
            pattern = '|'.join(mylist)
            df[str(title)+"_In_Title"] = df['Title'].apply(lambda x: pattern_searcher(search_str=x.lower(), search_list=pattern.lower()))
            df[str(title)+"_In_Title"] = df[str(title)+"_In_Title"].replace(mylist,str(title).lower())
        except:
            pass
print('*******************  MAKE TAGGING FILES +++++++++++++++++++++')

df.to_excel('Output/Combine_File.xlsx',index = False)

print('******************* MAKE WORDCLOUDS +++++++++++++++++++++')
def english(text,title):
    import numpy as np
    from PIL import Image
    # mask = np.array(Image.open('/home/machine/Downloads/star.png'))
    
    text = str(text).replace('[','').replace(']','').replace("'",'').replace('xa',' ')
    text = "".join(text)
    text = (re.sub(r'[^a-zA-Z]', ' ', text)).strip()

    stopwords = set(STOPWORDS)
    stop_words = STOPWORDS.update(["White", "WHITE", "white",'Black','BLACK','black','Dangal','dangal','Halla','halla','Bol','Shankhnaad','shankhnaad','Specialreport','Special Report','DasTak','Das Tak','Tak','Aaj','Special','Report'])

    wordcloud = WordCloud(width = 1000, height = 800, random_state=1,max_font_size=100,background_color='Black',colormap='Set2', collocations=False, stopwords = STOPWORDS).generate(text)
    plt.figure(figsize=(30,18),facecolor='green')
    
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title(str(title)+' Program At YT ',fontsize=27,color= 'Green', fontweight='bold', y= 1.05)
    fig1 = plt.gcf()
    fig1.savefig('Wordcloud/'+ str(title)+'-english'+'.png', facecolor="white", edgecolor="none")

    
Bw = df[(df.Program_Name_In_Title == 'black and white')| (df.Program_Name_In_Title == 'black and white') | (df.Program_Name_In_Title == 'black&white') | (df.Program_Name_In_Title == 'black & white')]

HallaBol = df[(df.Program_Name_In_Title == 'hallabol')|(df.Program_Name_In_Title == 'halla bol')]

Dangal = df[(df.Program_Name_In_Title == 'dangal')]

SpecialReport =  df[(df.Program_Name_In_Title == 'specialreport')|(df.Program_Name_In_Title == 'special report')]

Shankhnaad = df[(df.Program_Name_In_Title == 'shankhnaad')]

Dastak = df[(df.Program_Name_In_Title == 'dastak') | (df.Program_Name_In_Title == 'das tak') | (df.Program_Name_In_Title == 'dastak')]

Bw = Bw['Title'].to_list()
HallaBol = HallaBol['Title'].to_list()
Dangal = Dangal['Title'].to_list()
SpecialReport = SpecialReport['Title'].to_list()
Shankhnaad = Shankhnaad['Title'].to_list()
Dastak = Dastak['Title'].to_list()

english(text=Bw,title='Black & White')
english(text=HallaBol,title='Halla Bol')
english(text=Dangal,title='Dangal')
english(text=SpecialReport,title='Special Report')
english(text=Shankhnaad,title='Shankhnaad')
english(text=Dastak,title='DasTak')



