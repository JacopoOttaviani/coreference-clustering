import xml.dom.minidom
from decimal import *

markables = [] 
clusters = {} 

getcontext().prec = 7

xmldoc = xml.dom.minidom.parse('data/coreference_enriched.xml') 

def main():

    initAndMarkAll()

    m_x = buildVectorFromMarkable(markableFromId("17"))
    m_y = buildVectorFromMarkable(markableFromId("14"))
    
    print m_x
    print m_y
    """
    print 'lemmasMatch',lemmasMatch(m_x, m_y)
    print 'headMatch',headMatch(m_x, m_y)
    print 'pos_distance', posDistance(m_x,m_y)
    print 'NPs subsuming', npSubsuming(m_x,m_y)
    print 'Number match', numberMatch(m_x,m_y)
    print 'Animacy match',animacyMatch(m_x,m_y)
    """
    final_distance = distance(m_x,m_y)
    print 'Final distance:', final_distance
    
# build a dictionary associated to a markable
# storing all the useful information parsed from XML file
# an example of toy markable:
# <MARKABLE HEAD="W94" NUMBER="P" ARTICLE="D" SEM_CLASS="FRUIT" PROPER_NAME="TRUE" ANIMACY="TRUE" COMMENT="" ID="10">
def buildVectorFromMarkable(m):
    
    np_i_dict = {}
    
    np_i_dict["id"] = m.getAttribute("ID")
    
    np_i_dict["head_id"] = m.getAttribute("HEAD")
    np_i_dict["head_word"] = wordFromId(np_i_dict["head_id"])
    np_i_dict["head_lemma"] = lemmaFromId(np_i_dict["head_id"])
    
    np_i_dict["words"] = wordsFromMarkable(m)
    np_i_dict["lemmas"] = markableLemmasFromId(np_i_dict["id"]) 
    
    np_i_dict["pos"] = m.getAttribute("HEAD")
    
    np_i_dict["number"] = m.getAttribute("NUMBER")
    
    np_i_dict["article"] = m.getAttribute("ARTICLE")
    
    np_i_dict["sem_class"] = m.getAttribute("SEM_CLASS")
    
    np_i_dict["proper_name"] = m.getAttribute("PROPER_NAME")
    
    np_i_dict["animacy"] = m.getAttribute("ANIMACY")
    
    return np_i_dict

# input: nil
# create a cluster for each markable found in XML and save it in a clusters dictionary
def initAndMarkAll():
    # markables list sorted as found in the XML annotated document
    
    for m in xmldoc.getElementsByTagName('MARKABLE'):
        markables.append(m)
    
    """ cluster dictionary structure: 
            key              :    value
            markable (obj)   :    set([markables_in_same_cluster])
    """
    clusters = {} 
    
    # for every markable, create his personal cluster
    for m in markables:
        clusters[m] = set([m])
    


def allNpsCompatible (cluster_i, cluster_j):
    threshold_infinity = 9999999999999
    for m_x in cluster_i:
        for m_y in cluster_j:
            if (distance(m_x,m_y) > threshold_infinity):
                return False
    return True


# given two markables dictionaries, return distance between them
# output distance expressed in Decimal object
def distance(m_x,m_y):
    getcontext().prec = 7
    
    d = Decimal(0)
    
    infinity = 99999999999
    
    weights =   { 
                    'words_match'       : Decimal(10) ,
                    'head_match'        : Decimal(1) ,
                    'position'          : Decimal(5) ,
                    'subsuming'         : Decimal(-infinity) ,                    
                    'number'            : Decimal(infinity) ,
                    'animacy'           : Decimal(infinity) }
    
    print 'start d:',d
    d = d + weights['words_match'] * lemmasMatch(m_x, m_y)
    print 'after wordmatch:',d
    d = d + weights['head_match'] * headMatch(m_x, m_y)
    print 'after position:',d
    d = d + weights['position'] * posDistance(m_x, m_y)
    print 'after subsuming:',d
    d = d + weights['subsuming'] * npSubsuming(m_x, m_y)
    print 'after number:',d
    d = d + weights['number'] * numberMatch(m_x, m_y)
    print 'after animacy:',d
    d = d + weights['animacy'] * animacyMatch(m_x, m_y)
    
    
    return d


# returns FALSE if number (or animacy) are different
def numberMatch(m_x, m_y):
    if m_x["number"] != m_y["number"]:
        return False
    else: 
        return True

def animacyMatch(m_x, m_y):
    if m_x["animacy"] != m_y["animacy"]:
        return False
    else: 
        return True



# TO-CHECK: all NPs subsuming? or just head?
# head words subsuming
def wordSubString(m_x, m_y):
    if m_x["head_word"] in m_y["head_word"] or m_y["head_word"] in m_x["head_word"]:
        return True
    else: 
        return False
    
# NPs subsuming
# TO-DO: Let's think to a better way to get subsuming (e.g., intersection?)
def npSubsuming(m_x, m_y):
    
    if set(m_x["words"]) <= set(m_y["words"]) or set(m_x["words"]) >= set(m_y["words"]):
        return True
    
    else: 
        return False
        
# input = two markables dictionaries
# returns diff positions / max_distance (last word_id)
def posDistance(m_x,m_y):
    
    if m_x["pos"] > m_y["pos"]:
        diff_pos = int(m_x["pos"][1:]) - int(m_y["pos"][1:])
    else:
        diff_pos = int(m_y["pos"][1:]) - int(m_x["pos"][1:])
    
    pos_distance = Decimal(diff_pos) / Decimal(maxDistance()[1:])
    return pos_distance

# input = nil
# returns last id of last word of last markable
def maxDistance():
    id = markables[len(markables)-1].getAttribute("ID")
    words  = markableWordsIdsFromId(id)
    return words[len(words)-1]

# input = two markables dictionaries
# returns 1 if heads match, 0 otherwise
def headMatch(m_x,m_y):
    if (m_x["head_word"] == m_y["head_word"]):
        return Decimal(1)
    else:
        return Decimal(0)

# input = two markables dictionaries
# returns len(different_lemmas) / len(longest_markable)
def lemmasMatch(m_x,m_y):
    
    lemmas_match_ratio = 0
    diff_lemmas = 0
    
    getcontext().prec = 7
    
    if (len(m_x["lemmas"]) > len(m_y["lemmas"])):
        
        for lemma in m_x["lemmas"]:
            if lemma not in m_y["lemmas"]:
                diff_lemmas = diff_lemmas + 1
                
        lemmas_match_ratio = Decimal(diff_lemmas) / Decimal(len(m_x["lemmas"]))
        return lemmas_match_ratio 
    
    else:
        
        for lemma in m_y["lemmas"]:
            if lemma not in m_x["lemmas"]:
                diff_lemmas = diff_lemmas + 1
                
        lemmas_match_ratio = Decimal(diff_lemmas) / Decimal(len(m_y["lemmas"]))
        return lemmas_match_ratio 

    return lemmas_match_ratio 
    
    
    
#########################
# XML support functions 
#########################
def markableWordsFromId(id):
    words = []
    for m in xmldoc.getElementsByTagName("MARKABLE"):
        if m.getAttribute("ID") == id:
            for w in m.getElementsByTagName("W"):
                words.append(w.firstChild.nodeValue)
    return words

def markableWordsIdsFromId(id):
    words = []
    for m in xmldoc.getElementsByTagName("MARKABLE"):
        if m.getAttribute("ID") == id:
            for w in m.getElementsByTagName("W"):
                words.append(w.getAttribute("ID"))
    return words

def markableLemmasFromId(id):
    lemmas = []
    for m in xmldoc.getElementsByTagName("MARKABLE"):
        if m.getAttribute("ID") == id:
            for w in m.getElementsByTagName("W"):
                lemmas.append(w.getAttribute("LEMMA"))
    return lemmas

def markableFromId(id):
    for m in xmldoc.getElementsByTagName("MARKABLE"):
        if m.getAttribute("ID") == id:
            return m
    return ''

def wordFromId(id):
    # just check if the input wordID starts with W, if not: add W at beginning
    if id[0] != 'W':
        id = "W"+id
        
    # search for word inside XML file
    for w in xmldoc.getElementsByTagName("W"):
        if w.getAttribute("ID") == id:
            return w.firstChild.nodeValue
    return ''

def lemmaFromId(id):
    # just check if the input wordID starts with W, if not: add W at beginning
    if id[0] != 'W':
        id = "W"+id
        
    # search for lemma inside XML file
    for w in xmldoc.getElementsByTagName("W"):
        if w.getAttribute("ID") == id:
            return w.getAttribute("LEMMA")
    return ''
    

def wordsFromMarkable(m):
    words = []
    for w in m.getElementsByTagName("W"):
        words.append(w.firstChild.nodeValue)
    return words
    

# this is the main part of the program
if __name__ == "__main__":
    main()
