# ------------------ Imports -----------------------------------------------------

import xml.sax
import re
from collections import defaultdict, OrderedDict
import Stemmer
from os import path
import sys
import pickle
import timeit
import heapq

# ----------------------------------------------------------------------------------
# ------------------ Global Definitions --------------------------------------------

pages = []

pageCount  = 0
fileCount = 0
offset = {}
dictID = 0
indexMap = defaultdict(list)
filemap = defaultdict(list)

stemmer = Stemmer.Stemmer('english')

stem_map = {}                                               # Hash Map for significantly faster stemming

stem_num_map = {}
stem_count = 0

with open('stopwords.pickle', 'rb') as handle:
    stop_dict = pickle.load(handle)
handle.close()

# postings = defaultdict(lambda: defaultdict())
# postings_without_pos = defaultdict(lambda: defaultdict(lambda: 0))
# postings_without_pos = {}
# reference_postings = {}
# category_postings = defaultdict(lambda: [])

# ----------------------------------------------------------------------------------

class Page():

    def __init__(self,title,text,id):
        self.text = text
        self.title = self.case_fold(title)
        self.id = int(pageCount)
        self.infobox = ''
        self.categories = ''
        self.links = ''
        self.references = ''

        self.split_text()
        self.index()

    def process(self,text):
        data = self.tokenize(text)
        data = self.stopword_removal(data)
        data = self.stem(data)

        return data

    def getTitle(self, text):

        return self.process(text)


    def getBody(self, text):

        data = re.sub(r'\{\{.*\}\}', r' ', text)

        return self.process(data)


    def getInfobox(self, text):

        data = text.split('\n')
        flag = 0
        info = []
        for line in data:
            if re.match(r'\{\{infobox', line):
                flag = 1
                info.append(re.sub(r'\{\{infobox(.*)', r'\1', line))
            elif flag == 1:
                if line == '}}':
                    flag = 0
                    continue
                info.append(line)

        return self.process(' '.join(info))


    def getReferences(self, text):

        data = text.split('\n')
        refs = []
        for line in data:
            if re.search(r'<ref', line):
                refs.append(re.sub(r'.*title[\ ]*=[\ ]*([^\|]*).*', r'\1', line))

        return self.process(' '.join(refs))


    def getCategories(self, text):
        
        data = text.split('\n')
        categories = []
        for line in data:
            if re.match(r'\[\[category', line):
                categories.append(re.sub(r'\[\[category:(.*)\]\]', r'\1', line))
        
        return self.process(' '.join(categories))


    def getExternalLinks(self, text):
        
        data = text.split('\n')
        links = []
        for line in data:
            if re.match(r'\*[\ ]*\[', line):
                links.append(line)
        
        return self.process(' '.join(links))

    def split_text(self):
        self.text = self.text.encode("ascii", errors="ignore").decode()
        text = self.case_fold(self.text)
        data = re.split(r'== ?references ?==',text)

        global pageCount
        global titlefile
        pageCount += 1
        print(pageCount)

        if len(data) == 1:
            self.references = []
            self.links = []
            self.categories = []
        else:
            self.references = self.getReferences(data[1])
            self.links = self.getExternalLinks(data[1])
            self.categories = self.getCategories(data[1])

        # print(self.title)
        titlefile = open('./index/titles','a')
        string = str(self.id)+' '+self.title
        string = string.strip().encode("ascii", errors="ignore").decode() + '\n'
        titlefile.write(string)
        titlefile.close()

        self.infobox = self.getInfobox(data[0])
        self.text = self.getBody(data[0])
        self.title = self.getTitle(self.title)

        # print(self.title)
        # titlefile.write(str(self.id)+' '+self.title)

        return self

    def tokenize(self,text):

        tokens = re.split(r' |,|\(|\)|\||\{|\}|\]|\[|@|#|\n|\<..*\>|=|/|\.|\'|\"|:|\-|\?|\!|\&|\:|\;|\+|\-|\~|\_|\%|\$|\*|\n|\t', text)
        text = tokens

        return text

    def case_fold(self,text):
        
        text = text.lower()
        return text

    def stopword_removal(self,text):
        index_words = []

        for token in text:
            if token not in stop_dict:
                index_words.append(token)

        text = index_words

        return text

    def stem(self,text):
        stems = []

        for token in text:
            if token in stem_map:
                stems.append(stem_map[token])
            else:
                stem_map[token] = stemmer.stemWord(token)
                stems.append(stem_map[token])

        text = stems

        return text

    def index(self):
        global pageCount
        global fileCount
        global indexMap
        global offset
        global dictID
        global filemap

        ID = pageCount
        totalFreq = defaultdict(lambda: 0)

        d = defaultdict(lambda: 0)
        for word in self.title:
            d[word] += 1
            totalFreq[word] += 1
        title = d
        
        d = defaultdict(lambda: 0)
        for word in self.text:
            d[word] += 1
            totalFreq[word] += 1
        body = d

        d = defaultdict(lambda: 0)
        for word in self.infobox:
            d[word] += 1
            totalFreq[word] += 1
        info = d
	
        d = defaultdict(lambda: 0)
        for word in self.categories:
            d[word] += 1
            totalFreq[word] += 1
        categories = d
        
        d = defaultdict(lambda: 0)
        for word in self.links:
            d[word] += 1
            totalFreq[word] += 1
        links = d
        
        d = defaultdict(lambda: 0)
        for word in self.references:
            d[word] += 1
            totalFreq[word] += 1
        references = d
    
        for word in totalFreq.keys():
            t = title[word]
            b = body[word]
            i = info[word]
            c = categories[word]
            l = links[word]
            r = references[word]
            string = 'd'+str(self.id)
            if t:
                string += 't' + str(t)
            if b:
                string += 'b' + str(b)
            if i:
                string += 'i' + str(i)
            if c:
                string += 'c' + str(c)
            if l:
                string += 'l' + str(l)
            if r:
                string += 'r' + str(r)
        
            indexMap[word].append(string)
        
        # print(indexMap)

        if pageCount%20000 == 0:
            
            orderedMap = []

            for key in sorted(indexMap.keys()):
                string = key + ':'
                posting_list = indexMap[key]
                string += ' '.join(posting_list)
                orderedMap.append(string)

            write_partial_index('\n'.join(orderedMap),fileCount)

            indexMap = defaultdict(list)
            dictID = {}
            orderedMap = []
            fileCount += 1

# ------------------------------------------------------------------------------------

class DocHandler( xml.sax.ContentHandler ):

    def __init__(self):
        self.CurrentData = ''
        self.title = ''
        self.text = ''
        self.id = ''
        self.hashed = 0

    # Call when an element starts
    def startElement(self, tag, attributes):

        self.CurrentData = tag

    # Call when an elements ends
    def endElement(self, tag):

        if tag == 'page':
            wiki_page = Page( self.title, self.text, self.id )
            # pages.append(wiki_page)

            self.title = ''
            self.text = ''
            self.hashed = 0
            self.id = ''

    # Call when a character is read
    def characters(self, content):

        if self.CurrentData == 'title':
            self.title += content
        if self.CurrentData == 'text':
            self.text += content
        if self.CurrentData == 'id' and not self.hashed:
            self.id = content
            self.hashed = 1
        

# ---------------------------------------------------------------------------------

def basic_search(keyword):
    starttime = timeit.default_timer()
    keyword = stemmer.stemWord(keyword)
    endtime = timeit.default_timer() 
    return indexMap[keyword], starttime - endtime

def save_index(file):

    inv_index = str(indexMap)
    inv_index = inv_index.replace(" ","")

    with open(file,"w+") as f:
        f.write(inv_index)

    return

def save_stems():

    word_stems = str(stem_map)

    with open('word_stems.txt',"w+") as f:
        f.write(word_stems)

    return

def load_index():

    if path.exists("inv_index.txt"):
        with open('inv_index.txt','r') as f:
            inv_index = f.read()
            print("Index loaded")

        postings = eval(inv_index)
    
    return

def load_stems():
    if path.exists("word_stems.txt"):
        with open('word_stems.txt','r') as f:
            stems = f.read()
            print("Stems loaded")

        stem_map = eval(stems)

    return

def write_partial_index(indexString,fno):

    p_ind_file = './index/pindex'+ str(fno)
    
    with open(p_ind_file,"w+") as f:
        f.write(indexString)
    
    return

def mergefiles():

    global fileCount
    global offset

    filereaders = {}
    curline = {}
    wordpostings = defaultdict(lambda: [])
    words = {}
    heap = []
    wordfilemap = defaultdict(lambda: [])

    filecomplete = [0 for i in range(fileCount)]

    finishflag = 1
    flag = 0

    indexFile = './index/index'
    ind = open(indexFile,'w+')
    off = open('./index/offset','w+')

    for i in range(fileCount):
        filename = './index/pindex' + str(i)
        filereaders[i] = open(filename, 'r')

    for i in range(fileCount):
        curline[i] = filereaders[i].readline().strip()
        word = curline[i].split(':')[0]

        wordfilemap[word].append(i)
        wordpostings[word] += curline[i].split(':')[1].split(" ")

        if word not in heap:
            heapq.heappush(heap,word)

    while (finishflag):
        minword = heapq.heappop(heap)

        # print(wordpostings[minword])
        string = minword + ':' + str(ind.tell())
        string = string.strip() + '\n'
        off.write(string)

        string = minword + ":" + " ".join(wordpostings[minword]) + "\n"
        ind.write(string)

        filenum = wordfilemap[minword]
        # print(wordfilemap)
        wordfilemap.pop(minword)

        for num in filenum:
            nextline = filereaders[num].readline().strip()

            if nextline == '':
                filecomplete[num] = 1

            else:
                newword = nextline.split(':')[0]
                wordpostings[newword] += nextline.split(':')[1].split(" ")

                # print(wordfilemap[newword])
                if not wordfilemap[newword]:
                    heapq.heappush(heap,newword)
                    wordfilemap[newword].append(num)
                
                else:
                    wordfilemap[newword].append(num)

        for i in range(fileCount):
            flag = filecomplete[i] + flag
        flag = int(flag/(fileCount))

        if flag==1:
            finishflag = 0

    for i in range(fileCount):
        filereaders[i].close()

    ind.close()
    off.close()

    return

# ------------------- Main Function -----------------------------------------

if __name__ == '__main__':

    infile = sys.argv[1]

    try:
        titlefile = open('./index/titles','x')
    except:
        pass

    print("Making xml parser")
    xml_parser = xml.sax.make_parser()                                  # Create XML Parser
    xml_parser.setFeature(xml.sax.handler.feature_namespaces, 0)        # Turns off namespaces

    Handler = DocHandler()                                              # Use Custom Handler
    xml_parser.setContentHandler( Handler )

    xml_parser.parse(infile)

    orderedMap = []
    titlefile.close()

    for key in sorted(indexMap.keys()):
        # print(key)
        string = key + ':'
        posting_list = indexMap[key]
        string += ' '.join(posting_list)
        orderedMap.append(string)

    write_partial_index('\n'.join(orderedMap),fileCount)
    # titlefile.close()

    # print("fileCount is: ", fileCount)
    fileCount += 1
    mergefiles()
