# ------------------ Imports -----------------------------------------------------

import timeit
import Stemmer
import re
import pickle
import os
from collections import defaultdict

# ----------------------------------------------------------------------------------
# ------------------ Global Definitions --------------------------------------------

with open('stopwords.pickle', 'rb') as handle:
    stop_dict = pickle.load(handle)

stem_map = {}

stemmer = Stemmer.Stemmer('english')

indexsize = 0

# ----------------------------------------------------------------------------------

class Query():

    def __init__(self,text,qtype):

        self.text = self.process_query(text)
        self.start = 0
        self.end = 0
        self.qtype = qtype
        self.start = timeit.default_timer()
        docs = self.lookup(self.text)
        self.rank(docs)
        self.end = timeit.default_timer()

    def process_query(self,text):
        data = self.case_fold(text)
        data = self.tokenize(data)
        data = self.stopword_removal(data)
        data = self.stem(data)

        return data

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

    def lookup(self,tokens):
        query_listings = {}

        for token in tokens:
            query_listing = self.search(token,':',f = open('./index/offset','r')).strip().split(' ')
            # print(query_listing)

            for i in range(len(query_listing)):
                listing = query_listing[i]
                listingdict = self.fieldsplit(listing)

                query_listing[i] = listingdict
            
            query_listings[token] = query_listing
    
        return self.get_matches(query_listings)

    def fieldsplit(self,listing):
        listingdict = {}

        fields = ['t', 'b', 'i', 'c', 'r', 'l','d']
        postinglist = re.findall('[a-z]|[0-9]{1,1000}',listing)

        # print(postinglist)

        for item in range(len(postinglist)):
            cur = postinglist[item]
            if cur in fields:
                listingdict[cur] = int(postinglist[item+1])
        # print(listingdict)
        return listingdict

    def get_matches(self,query_listings):
        results = defaultdict(lambda: 0)
        docs = defaultdict(lambda: 0)
        weight = {'t':10000, 'b':50, 'i':25, 'c':10, 'r':10, 'l':10}

        print(len(query_listings))
        termcount = len(query_listings)

        for token in query_listings:
            for query_listing in query_listings[token]:
                # print(query_listing)
                for key in query_listing:
                    if key == 'd':
                        docs[query_listing['d']] += 1

        for token in query_listings:
            for query_listing in query_listings[token]:
                for key in query_listing:
                    if key == 'd':
                        curid = query_listing['d']
                    if key != 'd' and int(docs[curid]/termcount) == 1:
                        results[query_listing['d']] += query_listing[key]*docs[query_listing['d']]*weight[key]

        sorteddict = [(k, results[k]) for k in sorted(results, key=results.get, reverse=True)]
        # print(sorteddict)
        # print('\n')
        return sorteddict
            
    def search(self,token,delim,f):
        # Compute filesize of open file sent to us
        global indexsize
        indexsize = 0

        loc = token

        if indexsize == 0:
            indexsize = os.fstat(f.fileno()).st_size
        hi = indexsize

        lo=0
        lookfor=loc
        # print "looking for: ",lookfor
        while hi-lo > 1:
            # Find midpoint and seek to it
            loc = int((hi+lo)/2)
            # print(" hi = ",hi," lo = ",lo)
            # print "seek to: ",loc
            f.seek(loc)
            # Skip to beginning of line
            while f.read(1) != '\n':
                pass

            line = f.readline()
            row=line.split(delim)

            s = row[0]
            if delim == ' ':
                s=int(row[0])

            # post=row[1]
            # print(s)
            # print(lookfor>s)

            if lookfor == s:
                # print("Found: ",lookfor)
                if delim == ':':
                    offsetval = int(row[1])
                    ind = open('./index/index','r')
                    ind.seek(offsetval)
                    line = ind.readline()
                
                    post = line.split(':')[1]
                
                elif delim == ' ':
                    post = ''
                    for i in range(1,len(row)):
                        post += row[i]+' '

                f.close()
                return post  # Found

            if lookfor < s:
                # print('h1')
                # Split into lower half
                hi=loc

            if lookfor > s:
                # print('h2')
                # Split into higher half
                lo=loc
            
        # If not found
        # print("Not Found: ",lookfor)
        f.close()
        return False

    def rank(self,docs):
        for key,val in docs[:10]:
            fp = open("./index/titles",'r')
            # print(key)
            docs = self.search(key,' ',fp)
            print(key,": ",docs)
            fp.close()

        print("\n\n")
        return

#--------------------------------------------------------------------------------------------------

class FieldQuery():

    def __init__(self,text,qtype):

        self.text = self.process_query(text)
        self.start = 0
        self.end = 0
        self.qtype = qtype
        self.start = timeit.default_timer()
        term_labels = self.split(text)
        docs = self.lookup(self.text,term_labels)
        self.rank(docs)
        self.end = timeit.default_timer()

    def process_query(self,text):
        data = self.case_fold(text)
        data = self.tokenize(data)
        data = self.stopword_removal(data)
        data = self.stem(data)

        return data

    def split(self,text):
        query = text.strip().split(';')
        term_labels = defaultdict(lambda: ['d'])

        # print(query)

        for field in query:
            temp = field.split(':')
            f = temp[0] 
            terms = temp[1]

            terms = self.process_query(terms)
            for term in terms:
                term_labels[term].append(f[0])

        # print(term_labels)
        return term_labels

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

    def lookup(self,tokens,term_labels):
        query_listings = {}

        for token in term_labels:
            # print(token)
            query_listing = self.search(token,':',f = open('./index/offset','r')).strip().split(' ')
            # print(query_listing)

            for i in range(len(query_listing)):
                listing = query_listing[i]
                listingdict = self.fieldsplit(listing,term_labels[token])

                query_listing[i] = listingdict
            
            query_listings[token] = query_listing

        # print(query_listings)
        
        return self.get_matches(query_listings)

    # def lookup(self,tokens,term_labels):
    #     query_listings = {}

    #     for token in tokens:
    #         query_listing = self.search(token).strip().split(' ')
    #         # print(query_listing)

    #         for i in range(len(query_listing)):
    #             listing = query_listing[i]
    #             listingdict = self.fieldsplit(listing,term_labels)

    #             query_listing[i] = listingdict
            
    #         query_listings[token] = query_listing
    
    #     return self.get_matches(query_listings)

    def fieldsplit(self,listing,fields):
        listingdict = {}
        # print(fields)

        postinglist = re.findall('[a-z]|[0-9]{1,1000}',listing)

        # print(postinglist)
        # print(listing)

        for item in range(len(postinglist)):
            cur = postinglist[item]
            if cur in fields:
                # print(cur)
                listingdict[cur] = int(postinglist[item+1])
        # print(listingdict)
        return listingdict

    def get_matches(self,query_listings):
        results = defaultdict(lambda: 0)
        docs = defaultdict(lambda: 1)
        weight = {'t':100000, 'b':50, 'i':25, 'c':10, 'r':10, 'l':10}

        for token in query_listings:
            for query_listing in query_listings[token]:
                # print(query_listing)
                for key in query_listing:
                    if key == 'd':
                        docs[query_listing['d']] *= 2
                    elif key != 'd':
                        if key == 't':
                            # print('weight,100000: ',query_listing['d'])
                            results[query_listing['d']] += query_listing[key]*docs[query_listing['d']]*weight[key]

        sorteddict = [(k, results[k]) for k in sorted(results, key=results.get, reverse=True)]
        print(sorteddict)
        # print('\n')
        return sorteddict
            
    def search(self,token,delim,f):
        # Compute filesize of open file sent to us
        global indexsize
        indexsize = 0

        loc = token

        if indexsize == 0:
            indexsize = os.fstat(f.fileno()).st_size
        hi = indexsize

        lo=0
        lookfor=loc
        # print "looking for: ",lookfor
        while hi-lo > 1:
            # Find midpoint and seek to it
            loc = int((hi+lo)/2)
            # print(" hi = ",hi," lo = ",lo)
            # print "seek to: ",loc
            f.seek(loc)
            # Skip to beginning of line
            while f.read(1) != '\n':
                pass

            line = f.readline()
            row=line.split(delim)

            s = row[0]
            if delim == ' ':
                s=int(row[0])

            # post=row[1]
            # print(s)
            # print(lookfor>s)

            if lookfor == s:
                # print("Found: ",lookfor)
                if delim == ':':
                    offsetval = int(row[1])
                    ind = open('./index/index','r')
                    ind.seek(offsetval)
                    line = ind.readline()
                
                    post = line.split(':')[1]
                
                elif delim == ' ':
                    post = ''
                    for i in range(1,len(row)):
                        post += row[i]+' '

                f.close()
                # print("Found: ",lookfor)
                return post  # Found

            if lookfor < s:
                # print('h1')
                # Split into lower half
                hi=loc

            if lookfor > s:
                # print('h2')
                # Split into higher half
                lo=loc
            
        # If not found
        # print("Not Found: ",lookfor)
        f.close()
        return False

    def rank(self,docs):
        for key,val in docs[:10]:
            fp = open("./index/titles",'r')
            # print(key)
            docs = self.search(key,' ',fp)
            print(key,": ",docs)
            fp.close()

        print("\n\n")
        return

# ------------------- Main Function -----------------------------------------

if __name__ == '__main__':

    while (1):
        print("--------------------------------------------------------------------------------------------------------------")
        print("Query Type\n1: Regular Text\n2: Field Query")
        qtype = int(input())

        if qtype == 1:
            print("Enter your query")
        
            query = Query(input(),qtype)
            print("Time :- ",query.end - query.start,'sec')

        if qtype == 2:
            print("Enter your query")

            query = FieldQuery(input(),qtype)
            print("Time :- ",query.end - query.start,'sec')
        # print(query.text)