import xml.dom.minidom
import xml.dom
from operator import itemgetter

from decimal import *

markables = [] 
markables_dict = {}
clusters = {} 

coreferences = []


# TOY coreferences
# coreferences = [["9","4"],["10","1"]]


getcontext().prec = 7

threshold = 9999



xmldoc = xml.dom.minidom.parse('data/coreference_enriched.xml') 

def main():

    
    initAndMarkAll()
    
    """
    m_x = buildVectorFromMarkable(markableFromId("17"))
    m_y = buildVectorFromMarkable(markableFromId("14"))
    """
    
    for m in markables:
        markables_dict[m] =  buildVectorFromMarkable(m)
    
    print 'Markables dictionary: ',markables_dict
    
    print 'Markables number: ',len(markables_dict.keys())   
    
    print 'Clusters sets dictionary: ', clusters
    
    """
    Testing on single markables
    print m_x
    print m_y
    
    print 'lemmasMatch',lemmasMatch(m_x, m_y)
    print 'headMatch',headMatch(m_x, m_y)
    print 'pos_distance', posDistance(m_x,m_y)
    print 'NPs subsuming', npSubsuming(m_x,m_y)
    print 'Number match', numberMatch(m_x,m_y)
    print 'Animacy match',animacyMatch(m_x,m_y)
    
    final_distance = distance(m_x,m_y)
    print 'Final distance:', final_distance
    """

    
    scanMarkables()
    
    print '\n == FOUND COREFERENCES == ',coreferences
    
    fillOutputXML()
    
def scanMarkables():
    
    inv_markables = sorted(markables, reverse=True)
    print inv_markables
    
    # possible referent
    for np_i in inv_markables[5:6]:
        print '\nconsidering np_i:', markables_dict[np_i]["id"]
        
        # adding here all the possible antecedents to np_i and their distance,
        # in order to collect the compatible one with minimum distance to np_i
        possible_ants = []
        
        # possible antecedents (except referent itself)
        for np_j in inv_markables[inv_markables.index(np_i)+1:]:
            dis = distance(markables_dict[np_i], markables_dict[np_j])
            print '*** distance(id',markables_dict[np_i]["id"],', id',markables_dict[np_j]["id"],') = ',dis
            
            # if distance between two considered markables is minor than threshold (r)
            if dis < threshold:
                print '*** found distance (',dis,') under threshold (set to:',threshold,')'
                # CHECK COMPATIBILITY
                if allNpsCompatible(clusters[np_i],clusters[np_j]) == True:
                    
                    print '*** found compatibility amongst 2 clusters, adding them in a list (later will compute best minimum)...'
                    
                    # list of possible antecedents of np_i with their distances
                    # antecedent, dis
                    possible_ants.append((np_j, dis))
                    print '*** unordered possible ants', possible_ants
                
                else: print 'they\'re not compatible, stepping to the next one'
        
        # if at least one possible antecedents seems to exist
        if (possible_ants != []):   
            print '*********** SEARCHING FOR MINIMUM:'
            # selecting the minimum distance from possible_ants of np_i
            possible_ants = sorted(possible_ants,key=itemgetter(1),reverse=False)
            print '*** ordered possible ants', possible_ants
            
            # when found the minimum:
            print '*** minimum d for np_i: ',possible_ants[0][0], possible_ants[0][1]
            
            min_d_compatible_np_j = possible_ants[0][0]
            
            # upgrade clusters dictionary with a union of them for both np_i and min_d_compatible_np_j
            # i.e. UNION(clusters(np_i), clusters(min_d_compatible_np_j))
            clusters[np_i] = clusters[np_i].union(clusters[min_d_compatible_np_j])
            clusters[min_d_compatible_np_j] = clusters[np_i]
            print 'clusters np_i (unified):'
            print clusters[np_i]
            print 'clusters min_d_np_j (unified):'
            print clusters[min_d_compatible_np_j]
    
            # saving our coref in order to provide COREF_USL children
            # the coreferences list is in the form:
            # [[referent_markable_id, antecedent_markable_id (aka src)], ... ]
            coreferences.append([markables_dict[np_i]["id"],markables_dict[min_d_compatible_np_j]["id"]])



    
    
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
    
    # for every markable, create his personal cluster
    for m in markables:
        clusters[m] = set([m])
    


def allNpsCompatible (cluster_i, cluster_j):
    for m_x in cluster_i:
        for m_y in cluster_j:
            if (distance(markables_dict[m_x],markables_dict[m_y]) > threshold):
                return False
    return True





#######################
# Distance computing
#######################

# given two markables dictionaries, return distance between them
# output distance expressed in Decimal object
def distance(m_x,m_y):
    getcontext().prec = 7
    
    # initialise distance as a Decimal = 0
    d = Decimal(0)
    
    infinity = 9999999
    
    # right things for weights below
    """
    'subsuming'         : Decimal(-infinity) ,                    
    'number'            : Decimal(infinity) ,
    'animacy'           : Decimal(infinity) }
    """
    weights =   { 
                    'words_match'       : Decimal(10) ,
                    'head_match'        : Decimal(1) ,
                    'position'          : Decimal(5) ,
                    'subsuming'         : Decimal(1) ,                    
                    'number'            : Decimal(1) ,
                    'animacy'           : Decimal(1) }
                    
    
    #print 'starting distance:',d
    d = d + weights['words_match'] * lemmasMatch(m_x, m_y)
    #print 'after wordmatch:',d
    d = d + weights['head_match'] * headMatch(m_x, m_y)
    #print 'after position:',d
    d = d + weights['position'] * posDistance(m_x, m_y)
    #print 'after subsuming:',d
    d = d + weights['subsuming'] * npSubsuming(m_x, m_y)
    #print 'after number:',d
    d = d + weights['number'] * numberMatch(m_x, m_y)
    #print 'after animacy:',d
    d = d + weights['animacy'] * animacyMatch(m_x, m_y)
    
    
    return d


# returns 0 if numbers (or animacies) are different, 1 otherwise
def numberMatch(m_x, m_y):
    if m_x["number"] != m_y["number"]:
        return 0
    else: 
        return 1

def animacyMatch(m_x, m_y):
    if m_x["animacy"] != m_y["animacy"]:
        return 0
    else: 
        return 1



# TO-CHECK: all NPs subsuming? or just head?
# head words subsuming
def wordSubString(m_x, m_y):
    if m_x["head_word"] in m_y["head_word"] or m_y["head_word"] in m_x["head_word"]:
        return 1
    else: 
        return 0
    
# NPs subsuming
# TO-DO: Let's think to a better way to get subsuming (e.g., intersection?)
def npSubsuming(m_x, m_y):
    
    if set(m_x["words"]) <= set(m_y["words"]) or set(m_x["words"]) >= set(m_y["words"]):
        return 1
    
    else: 
        return 0
        
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
    
    
    
# method to write a brand new xml file, enriched with new coreferences
# new coreferences will be in the form of:
# <COREF_US COMMENT="This coreference has been generated by an Unsupervised ML Algo" ID="US0" SRC="4"/>
def fillOutputXML():
    output_xml_parsed = xml.dom.minidom.parse('data/coreference_enriched.xml') 
    markable_dad = ''
    
    f = open ("/home/jacopo/Desktop/us_coref.xml","w+")
    
    for c in coreferences:

        # searching for markable to which will be added a COREF child
        for m in output_xml_parsed.getElementsByTagName("MARKABLE"):
            if m.getAttribute("ID") == c[0]:
                markable_dad = m
        
        # coref_us Element
        coref_el = xml.dom.minidom.Element("COREF_US")
        
        src_attr = xml.dom.minidom.Attr("SRC")
        src_attr.value = c[1]
        coref_el.setAttributeNode(src_attr)
        
        comment_attr = xml.dom.minidom.Attr("COMMENT")
        comment_attr.value = "This coreference has been generated by an Unsupervised ML Algo"
        coref_el.setAttributeNode(comment_attr)
        
        id_attr = xml.dom.minidom.Attr("ID")
        id_attr.value = "US"+str(coreferences.index(c))
        coref_el.setAttributeNode(id_attr)
        
        type_attr = xml.dom.minidom.Attr("TYPE_REL")
        type_attr.value = "IDENTITY"
        coref_el.setAttributeNode(type_attr)
        
        #print 'coref',coref_el
        #print 'dad',markable_dad
        
        markable_dad.insertBefore(coref_el,markable_dad.firstChild)
        
    f.write( output_xml_parsed.toprettyxml() )
    f.close

# this is the main part of the program
if __name__ == "__main__":
    main()
