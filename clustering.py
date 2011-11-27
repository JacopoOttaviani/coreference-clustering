import xml.dom.minidom
import xml.dom
from operator import itemgetter
from decimal import *
import time

#######################
# Main data structures
#######################
markables = [] 
markables_dict = {}
clusters = {} 
coreferences = []

getcontext().prec = 7
distance_iterations = 0

upper_limit = 15

folder = 'data/'
filename = 'oscar.xml'
output_folder = "/home/jacopo/Desktop/"

threshold = 9999


xmldoc = xml.dom.minidom.parse(folder+filename) 


def main():
    
    # time checking
    # t0 = time.strftime('%S')
    
    # initialize the algorithm's data structures
    initAndMarkAll()
    
    for m in markables:
        markables_dict[m] =  buildVectorFromMarkable(m)
    
    # clean empty markables from data structures
    for m_dict in markables_dict.keys():
        if markables_dict[m_dict] == {}: 
            markables_dict.pop(m_dict)
            markables.remove(m_dict)
            clusters.pop(m_dict)
    
    testWhyNot = ["10","1"]
    
    scanMarkables(testWhyNot)
    
    print 'Markables dictionary: ',markables_dict
    print 'Markables number: ',len(markables_dict.keys())   
    print 'Clusters sets dictionary: ', clusters
    print 'Number of keys in Clusters: ', len(clusters.keys())
    
    print '\n DISTANCE ITERATIONS:', distance_iterations
    print '\n PREFOUND ALL COREFERENCES: ', numberOfAllExCoref()
    print '\n PREFOUND IDENT COREFERENCES: ', numberOfIdentExCoref()
    print '\n NEW FOUND COREFERENCES_US: ', len(coreferences)
    print '\n NUMBER OF CLUSTERS FOUND (also with 1 element): ',len(clusters)

    print '\n NUMBER OF ACTUAL CLUSTERS (also with 1 element): ',len(actualNumberOfClusters(1))
    print '\n NUMBER OF ACTUAL CLUSTERS (len > 1 element): ',len(actualNumberOfClusters(2))
    print '\n ACTUAL CLUSTER WITH LEN > 2: ', actualNumberOfClusters(3)    
    print '\n ACTUAL CLUSTER WITH LEN > 3: ', actualNumberOfClusters(4)
    
    print '\n ACTUAL CLUSTER WITH LEN > 1: ', actualNumberOfClusters(2)
    
    coinc = countSameCorefs()
    print '\n NUMBER OF COINCIDENT COREF: ', coinc[0]
    print '\n COINCIDENT COREF IDs:',coinc[1]
    
    #t1= time.strftime('%S')
    #timediff = int(t0)-int(t1)
    #print t0, t1
    # change time
    #print '\nTIME ELAPSED:', timediff,' seconds.'
    
def scanMarkables(testWhyNot):
    
    inv_markables = sorted(markables, reverse=True)
    
    debug_single_coref = False 
    
    # possible referent
    for np_i in inv_markables:
        print 'considering np_i:', markables_dict[np_i]["id"]
        
        # adding here all the possible antecedents to np_i and their distance,
        # in order to collect the compatible one with minimum distance to np_i
        possible_ants = []
        
        # possible antecedents (except referent itself)
        for np_j in inv_markables[inv_markables.index(np_i)+1:]:
            
            
            # useful to debug single coreferences buggy instances
            if np_j == markableFromId(testWhyNot[1]) and np_i == markableFromId(testWhyNot[0]):
                debug_single_coref = True
                print '\n################### DEBUG SESSION STARTS ###################\n'
            else: debug_single_coref = False
            
            if debug_single_coref:
                print "(?) Why is ", markableWordsFromId(testWhyNot[0]) ,"coreferring to ",markableWordsFromId(testWhyNot[1]),"\n"
            
            dis = distance(markables_dict[np_i], markables_dict[np_j],debug_single_coref)
            if (debug_single_coref): print '*** distance(id',markables_dict[np_i]["id"],', id',markables_dict[np_j]["id"],') = ',dis
            

            
            # if distance between two considered markables is minor than threshold (r)
            if dis < threshold:
                if (debug_single_coref): print '*** found distance (',dis,') under threshold (set to:',threshold,')'
                # CHECK COMPATIBILITY
                if allNpsCompatible(clusters[np_i],clusters[np_j],debug_single_coref) == True:
                    
                    if (debug_single_coref):print '*** found compatibility amongst 2 clusters, adding them in a list (later will compute best minimum)...'
                    
                    # list of possible antecedents of np_i with their distances
                    # antecedent, dis
                    possible_ants.append((np_j, dis))
                    if (debug_single_coref):print '*** unordered possible ants', possible_ants
                
                #else: print 'they\'re not compatible, stepping to the next one'
            
            if (debug_single_coref): print '\n################### DEBUG SESSION ENDS ###################\n'

        # if at least one possible antecedents seems to exist
        if (possible_ants != []):   
            if (debug_single_coref):print '*********** SEARCHING FOR MINIMUM:'
            # selecting the minimum distance from possible_ants of np_i
            possible_ants = sorted(possible_ants,key=itemgetter(1),reverse=False)
            if (debug_single_coref):print '*** ordered possible ants', possible_ants
            
            # when found the minimum:
            if (debug_single_coref): print '*** minimum d for np_i: ',possible_ants[0][0], possible_ants[0][1]
            
            min_d_compatible_np_j = possible_ants[0][0]
            
            # upgrade clusters dictionary with a union of them for both np_i and min_d_compatible_np_j
            # i.e. UNION(clusters(np_i), clusters(min_d_compatible_np_j))
            clusters[np_i] = clusters[np_i].union(clusters[min_d_compatible_np_j])
            clusters[min_d_compatible_np_j] = clusters[np_i]
            if (debug_single_coref):print 'clusters np_i (unified):'
            if (debug_single_coref):print clusters[np_i]
            if (debug_single_coref):print 'clusters min_d_np_j (unified):'
            if (debug_single_coref):print clusters[min_d_compatible_np_j]
    
            # saving our coref in order to provide COREF_USL children
            # the coreferences list is in the form:
            # [[referent_markable_id, antecedent_markable_id (aka src)], distance... ]
            coreferences.append([markables_dict[np_i]["id"],markables_dict[min_d_compatible_np_j]["id"],possible_ants[0][1]])
        
    
# build a dictionary associated to a markable
# storing all the useful information parsed from XML file
# an example of toy markable:
# <MARKABLE HEAD="W94" NUMBER="P" ARTICLE="D" SEMANTIC_CLASS="FRUIT" PROPER_NAME="TRUE" ANIMACY="TRUE" COMMENT="" ID="10">
def buildVectorFromMarkable(m):
    
    np_i_dict = {}
    
    np_i_dict["id"] = m.getAttribute("ID")
    
    np_i_dict["head_id"] = m.getAttribute("HEAD")
    # if unuseful markable, return void dict (line #774)
    if np_i_dict["head_id"] == '':
        return {}
    np_i_dict["head_word"] = wordFromId(np_i_dict["head_id"])
    

    
    np_i_dict["head_lemma"] = lemmaFromId(np_i_dict["head_id"])
    
    np_i_dict["words"] = wordsFromMarkable(m)
    np_i_dict["lemmas"] = markableLemmasFromId(np_i_dict["id"]) 
    
    np_i_dict["pos"] = m.getAttribute("HEAD")
    
    np_i_dict["number"] = m.getAttribute("NUMBER")
    
    np_i_dict["article"] = m.getAttribute("ARTICLE")
    
    np_i_dict["sem_class"] = m.getAttribute("SEMANTIC_CLASS")
    
    np_i_dict["proper_name"] = m.getAttribute("PROPER_NAME")
    
    np_i_dict["animacy"] = m.getAttribute("ANIMACY")
    
    return np_i_dict

# input: nil
# create a cluster for each markable found in XML and save it in a clusters dictionary
def initAndMarkAll():
    # markables list sorted as found in the XML annotated document
    
    for m in xmldoc.getElementsByTagName('MARKABLE'):#[:upper_limit]:
        markables.append(m)
    
    """ cluster dictionary structure: 
            key              :    value
            markable (obj)   :    set([markables_in_same_cluster])
    """
    
    # for every markable, create his personal cluster
    for m in markables:
        clusters[m] = set([m])
    


def allNpsCompatible (cluster_i, cluster_j, debug):
    if (debug): print "### ENTRING ALL NPS COMPATIBLE ###"
    for m_x in cluster_i:
        for m_y in cluster_j:
            if (distance(markables_dict[m_x],markables_dict[m_y],debug) > threshold):
                if (debug): print "### FOUND INCOMPATIBILITY: EXITING ALL NPS COMPATIBLE ###"
                return False
    if (debug): print "### EXITING ALL NPS COMPATIBLE, CLUSTERS ARE COMPATIBLE ###"
    return True



#######################
# Distance computing
#######################

# given two markables dictionaries, return distance between them
# output distance expressed in Decimal object
def distance(m_x,m_y,verbose):
    
    global distance_iterations 
    distance_iterations = distance_iterations + 1
    getcontext().prec = 7
    
    # initialise distance as a Decimal = 0
    d = Decimal(0)
    
    infinity = 9999999
    
    # right things for weights below
    weights =   { 
                    'words_match'       : Decimal(10) ,
                    'head_match'        : Decimal(1) ,
                    'position'          : Decimal(5) ,
                    'sem_class'         : Decimal(infinity) ,
                    'subsuming'         : Decimal(-infinity) ,                    
                    'number'            : Decimal(infinity) ,
                    'animacy'           : Decimal(infinity) }

    if (verbose): print 'starting distance:',d
    d = d + weights['words_match'] * wMatch(m_x, m_y)
    if (verbose): print 'after lemma match:',d
    d = d + weights['head_match'] * headMatch(m_x, m_y)
    if (verbose): print 'after head match:',d
    d = d + weights['position'] * posDistance(m_x, m_y)
    if (verbose): print 'after position:',d
    d = d + weights['subsuming'] * npSubsuming(m_x, m_y)
    if (verbose): print 'after subsuming:',d
    d = d + weights['number'] * numberMatch(m_x, m_y)
    if (verbose): print 'after number match:',d
    d = d + weights['sem_class'] * semClassMatch(m_x, m_y)
    if (verbose): print 'after sem_class match:',d
    d = d + weights['animacy'] * animacyMatch(m_x, m_y)
    if (verbose): print 'after animacy match:',d
    
    return d


# returns 0 if numbers (or animacies) are different, 1 otherwise
def numberMatch(m_x, m_y):
    if m_x["number"] != m_y["number"]:
        return Decimal(1)
    else: 
        return Decimal(0)

def animacyMatch(m_x, m_y):
    if m_x["animacy"] != m_y["animacy"]:
        return Decimal(1)
    else: 
        return Decimal(0)



# TO-CHECK: all NPs subsuming? or just head?
# head words subsuming
def wordSubString(m_x, m_y):
    if m_x["head_word"] in m_y["head_word"] or m_y["head_word"] in m_x["head_word"]:
        return Decimal(1)
    else: 
        return Decimal(0)
    
# NPs subsuming
# TO-DO: Let's think to a better way to get subsuming (e.g., intersection?)
def npSubsuming(m_x, m_y):
    
    if set(m_x["words"]) <= set(m_y["words"]) or set(m_x["words"]) >= set(m_y["words"]):
        return Decimal(1)
    
    else: 
        return Decimal(0)
        
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
# returns 1 if they have a common semantics class, 0 otherwise
def semClassMatch(m_x,m_y):
    
    sem_class_x = listFromSemClassStr(m_x["sem_class"])
    sem_class_y = listFromSemClassStr(m_y["sem_class"])
    
    for s_c in sem_class_x:
        if s_c in sem_class_y:
            return 0
        
    for s_c in sem_class_y:
        if s_c in sem_class_x:
            return 0
    
    # else, intersection is empty
    return 1

def listFromSemClassStr(s):
    # string ['relation', 'substance', 'artifact', 'food'] --> list 
    s = s[1:len(s)-1]
    
    s = s.replace(" ","")
    
    l = s.split(",")
    
    for s in l:
        l[l.index(s)] = s[1:len(s)-1]
    return l
    
    
# input = two markables dictionaries
# returns len(different_lemmas) / len(longest_markable)
def lemmasMatch(m_x,m_y):
    
    lemmas_match_ratio = 0
    diff_lemmas = 0
    
    getcontext().prec = 7
    
    if (len(m_x["w"]) > len(m_y["lemmas"])):
        
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
    
# input = two markables dictionaries
# returns len(different_words) / len(longest_markable)
def wMatch(m_x,m_y):
    
    ws_match_ratio = 0
    diff_w = 0
    
    getcontext().prec = 7
    
    if (len(m_x["words"]) > len(m_y["words"])):
        
        for w in m_x["words"]:
            if w not in m_y["words"]:
                diff_w = diff_w + 1
                
        ws_match_ratio = Decimal(diff_w) / Decimal(len(m_x["words"]))
        return ws_match_ratio 
    
    else:
        
        for w in m_y["words"]:
            if w not in m_x["words"]:
                diff_w = diff_w + 1
                
        ws_match_ratio = Decimal(diff_w) / Decimal(len(m_y["words"]))
        return ws_match_ratio 

    return ws_match_ratio 
        
    
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
    
    
# just count all already found Corefs and Ident Corefs
# returns: string
def numberOfIdentExCoref():    
    ex_corefs = 0
    
    for m in xmldoc.getElementsByTagName("COREF"):
        if m.getAttribute("TYPE_REL") == 'IDENT':
            ex_corefs = ex_corefs + 1
    
    return ex_corefs

def numberOfAllExCoref():
    ex_corefs = 0
    
    for m in xmldoc.getElementsByTagName("COREF"):
        ex_corefs = ex_corefs + 1
    
    return ex_corefs    
    
# method to write a brand new xml file, enriched with new coreferences
# new coreferences will be in the form of:
# <COREF_US COMMENT="This coreference has been generated by an Unsupervised ML Algo" ID="US0" SRC="4"/>
def fillOutputXML():

    output_xml_parsed = xml.dom.minidom.parse(folder+filename) 
    markable_dad = ''
    
    f = open (output_folder+'us_coref_'+filename,"w+")
    
    for c in coreferences:

        # searching for markable to which will be added a COREF child
        for m in output_xml_parsed.getElementsByTagName("MARKABLE"):
            if m.getAttribute("ID") == c[0]:
                markable_dad = m
        
        # COREF_US Element
        coref_el = xml.dom.minidom.Element("COREF_US")
        
        src_attr = xml.dom.minidom.Attr("SRC")
        src_attr.value = c[1]
        coref_el.setAttributeNode(src_attr)
        
        """
        comment_attr = xml.dom.minidom.Attr("COMMENT")
        comment_attr.value = "This coreference has been generated by an Unsupervised ML Algo"
        coref_el.setAttributeNode(comment_attr)
        """
        
        id_attr = xml.dom.minidom.Attr("ID")
        id_attr.value = "US"+str(coreferences.index(c))
        coref_el.setAttributeNode(id_attr)
        
        type_attr = xml.dom.minidom.Attr("TYPE_REL")
        type_attr.value = "IDENT"
        coref_el.setAttributeNode(type_attr)
        
        # add a distance field
        d_attr = xml.dom.minidom.Attr("DISTANCE")
        d_attr.value = str(c[2])
        coref_el.setAttributeNode(d_attr)
        
        # add words of src to found coref_us element
        words_src_attr = xml.dom.minidom.Attr("SRC_W")
        words_src_attr.value = str(markableWordsFromId(c[1]))
        coref_el.setAttributeNode(words_src_attr)
        
        markable_dad.insertBefore(coref_el,markable_dad.firstChild)
        
    f.write( output_xml_parsed.toprettyxml() )
    f.close

# compares the number of new coreferences which are coincident with the old ones, 
# and retrieve them
def countSameCorefs():

    xmldoc_local = xml.dom.minidom.parse(output_folder+'us_coref_'+filename)
    coincident_corefs = 0
    c_c = []
    for m in xmldoc_local.getElementsByTagName("COREF"):
        if m.getAttribute("TYPE_REL") == 'IDENT':
            if (m.parentNode.childNodes[1].tagName == 'COREF_US'): 
                if m.getAttribute("SRC") == m.parentNode.childNodes[1].getAttribute("SRC"):
                    coincident_corefs = coincident_corefs + 1
                    c_c.append(m.parentNode.childNodes[1].getAttribute("ID"))

    return [coincident_corefs,c_c]

# print clusters with more than one element
def printInterestingClusters():
    for c in clusters.keys():
        if len (clusters[c]) > 1:
            print c, clusters[c]
            for m in clusters[c]:
                print '\t',wordsFromMarkable(m)

# return actual clusters
# I just filter out copies of the same clusters from clusters list
def actualNumberOfClusters(min_len):
    
    actualClusters = []
    
    for c in clusters.keys():
        if clusters[c] not in actualClusters and len(clusters[c]) > min_len:
            actualClusters.append(clusters[c])    
            
    return actualClusters

# this is the main part of the program
if __name__ == "__main__":
    main()