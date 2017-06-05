import sys, os
import ElementTreeUtils as ETUtils
import sys, os
from collections import defaultdict
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/..")
import Core.SentenceGraph as SentenceGraph
import Utils.InteractionXML.InteractionXMLUtils as IXMLUtils
import Utils.Range as Range

def getEntities(sentence):
    return sentence.findall("entity") + [x for x in sentence.iter("span")]

def getEntityTokens(entity, tokens):
    entityTokens = []
    for entityOffset in Range.charOffsetToTuples(entity.get("charOffset")):
        for token in tokens:
            if Range.overlap(entityOffset, Range.charOffsetToSingleTuple(token.get("charOffset"))):
                entityTokens = []
    return entityTokens

def findHeads(input, parseName, tokenization=None, output=None, removeExisting=True, iterate=False):
    xml = ETUtils.ETFromObj(input)    
    print >> sys.stderr, "Removing existing head offsets"
    counts = defaultdict(int)
    removeCount = 0
    totalCount = 0
    xml = ETUtils.ETFromObj(input)
    for document in xml.getroot().findall("document"):
        counts["documents"] += 1
        for sentence in document.findall("sentence"):
            counts["sentences"] += 1
            parse = IXMLUtils.getParseElement(sentence, parseName, False, False)
            tokens = None
            if parse:
                tokenization = IXMLUtils.getTokenizationElement(sentence, parse.get("tokenizer"), False, False)
                tokens = tokenization.findall("token")
            for entity in getEntities(sentence):
                counts["entities"] += 1
                totalCount += 1
                if entity.get("headOffset") != None:
                    counts["heads-existing"] += 1
                    if removeExisting:
                        counts["heads-removed"] += 1
                        removeCount += 1
                        del entity.attrib["headOffset"]
    if removeExisting:
        print >> sys.stderr, "Removed head offsets from", counts["heads-removed"], "out of", counts["entities"], "entities"
    
    # SentenceGraph automatically calculates head offsets and adds them to entities if they are missing
    print >> sys.stderr, "Determining head offsets using parse", parse, "and tokenization", tokenization
    corpusElements = SentenceGraph.loadCorpus(xml, parse, tokenization)
    
    # Make sure every parse gets head scores
    for sentence in corpusElements.sentences:
        if sentence.sentenceGraph == None:
            continue
        if sentence.sentenceGraph.tokenHeadScores == None:
            sentence.sentenceGraph.getTokenHeadScores()
    
    if output != None:
        print >> sys.stderr, "Writing output to", output
        ETUtils.write(corpusElements.rootElement, output)
    return xml

# def findHeads(input, parse, tokenization=None, output=None, removeExisting=True, iterate=False):
#     if iterate:
#         from Utils.ProgressCounter import ProgressCounter
#         import InteractionXML.SentenceElements as SentenceElements
#         print >> sys.stderr, "Determining head offsets using parse", parse, "and tokenization", tokenization
#         print >> sys.stderr, "Removing existing head offsets"
#         removeCount = 0
#         counter = ProgressCounter(None, "Find heads")
#         counter.showMilliseconds = True
#         for sentences in SentenceElements.getCorpusIterator(input, output, parse, tokenization):
#             for sentence in sentences:
#                 if removeExisting:
#                     for e in getEntities(sentence.sentence):
#                         if e.get("headOffset") != None:
#                             removeCount += 1
#                             del e.attrib["headOffset"]
#                 graph = SentenceGraph.SentenceGraph(sentence.sentence, sentence.tokens, sentence.dependencies)
#                 graph.mapInteractions(sentence.entities, sentence.interactions)
#                 # Make sure every parse gets head scores
#                 #if graph.tokenHeadScores == None:
#                 #    graph.getTokenHeadScores()
#             counter.update(len(sentences), "Finding heads ("+sentences[-1].sentence.get("id")+"): ")                
#         print >> sys.stderr, "Removed head offsets from", removeCount, "entities"    
#     else:
#         xml = ETUtils.ETFromObj(input)
#         if removeExisting:
#             print >> sys.stderr, "Removing existing head offsets"
#             removeCount = 0
#             xml = ETUtils.ETFromObj(input)
#             for d in xml.getroot().findall("document"):
#                 for s in d.findall("sentence"):
#                     for e in getEntities(s):
#                         if e.get("headOffset") != None:
#                             removeCount += 1
#                             del e.attrib["headOffset"]
#             print >> sys.stderr, "Removed head offsets from", removeCount, "entities"
#         
#         # SentenceGraph automatically calculates head offsets and adds them to entities if they are missing
#         print >> sys.stderr, "Determining head offsets using parse", parse, "and tokenization", tokenization
#         corpusElements = SentenceGraph.loadCorpus(xml, parse, tokenization)
#         
#         # Make sure every parse gets head scores
#         for sentence in corpusElements.sentences:
#             if sentence.sentenceGraph == None:
#                 continue
#             if sentence.sentenceGraph.tokenHeadScores == None:
#                 sentence.sentenceGraph.getTokenHeadScores()
#         
#         if output != None:
#             print >> sys.stderr, "Writing output to", output
#             ETUtils.write(corpusElements.rootElement, output)
#         return xml
    
if __name__=="__main__":
    import sys
    print >> sys.stderr, "##### Calculating entity head token offsets #####"
    
    from optparse import OptionParser
    # Import Psyco if available
    try:
        import psyco
        psyco.full()
        print >> sys.stderr, "Found Psyco, using"
    except ImportError:
        print >> sys.stderr, "Psyco not installed"

    optparser = OptionParser(usage="%prog [options]\nRecalculate head token offsets.")
    optparser.add_option("-i", "--input", default=None, dest="input", help="Corpus in interaction xml format", metavar="FILE")
    optparser.add_option("-o", "--output", default=None, dest="output", help="Output file in interaction xml format.")
    optparser.add_option("-p", "--parse", default=None, dest="parse", help="Parse element name for calculating head offsets")
    optparser.add_option("-t", "--tokenization", default=None, dest="tokenization", help="Tokenization element name for calculating head offsets")
    optparser.add_option("-r", "--iterate", default=False, action="store_true", dest="iterate", help="")
    (options, args) = optparser.parse_args()
    
    findHeads(input=options.input, output=options.output, parse=options.parse, tokenization=options.tokenization, iterate=options.iterate)
    
