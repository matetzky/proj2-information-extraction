import requests
import lxml.html
import rdflib
import sys
import time

wiki_prefix = "http://en.wikipedia.org"


def clean_string(s):
    while '[' in s:
        a = s.index('[')
        b = s.index(']')
        s = s[:a] + s[b + 1:]
    for c in s:
        if c in '()[]':
            s = s.replace(c, '')
    s = s.replace('  ', ' ')
    s = s.strip()
    s = s.lstrip()
    return s


def get_capital(infobox):
    b = infobox[0].xpath("//table//th[contains(text(), 'Capital')]")
    try:
        capital = b[0].xpath("./../td//a/text()")[0]
        capital = clean_string(capital)
    except:  # some small countries don't have a capital
        capital = 'None'
    return capital


def get_government(infobox):
    c = infobox[0].xpath("//table//th//a[contains(text(), 'Government')]")  # in some countries its a link
    if not c:
        c = infobox[0].xpath("//table//th[contains(text(), 'Government')]")  # in some countries its not a link
        if not c:
            government = 'None'
        else:
            government = " ".join(c[0].xpath("./../td//a/text()"))
    else:
        government = " ".join(c[0].xpath("./../../td//a/text()"))
    government = clean_string(government)
    return government


def find_date(l):
    for s in l:
        a = s.split('-')
        if len(a) == 3:
            return s
    return 'None'


def get_date_of_birth(url):
    res = requests.get(url)
    doc = lxml.html.fromstring(res.content)
    if 'Wikipedia does not have an article with this exact name' in " ".join(doc.xpath('//text()')):
        return 'None'
    infobox = doc.xpath("//table[contains(@class, 'infobox')]")
    if not infobox:
        return 'None'
    dob = infobox[0].xpath("//table//th[contains(text(), 'Born')]")
    if not dob:
        return 'None'
    dob = dob[0].xpath('../td//text()')
    dob = find_date(dob)
    return dob


def get_president(infobox):
    d = infobox[0].xpath("//table//th//a[contains(text(), 'President')]")
    if d:
        try:
            ref = d[0].xpath("./../../../td//a/@href")[0]
        except:
            try:
                ref = d[0].xpath("./../../td//a/@href")[0]
            except:
                return "None", "None"
        president = ref.split('/')[-1]
        dob = get_date_of_birth(wiki_prefix + ref)
    else:
        president = "None"
        dob = "None"

    return president, dob


def get_pm(infobox):
    e = infobox[0].xpath("//table//th//a[contains(text(), 'Prime Minister')]")
    if e:
        try:
            ref = e[0].xpath("./../../../td//a/@href")[0]
        except:
            ref = e[0].xpath("./../../../../td//a/@href")[0]
        prime_minister = ref.split('/')[-1]
        dob = get_date_of_birth(wiki_prefix + ref)
    else:
        prime_minister = "None"
        dob = "None"

    return prime_minister, dob


def get_area(infobox):
    f = infobox[0].xpath("//table//th//a[contains(text(), 'Area')]")  # sometimes a link
    if not f:
        f = infobox[0].xpath("//table//th[contains(text(), 'Area')]")  # sometimes not a link
    try:
        areas = f[0].xpath('./../../following-sibling::tr/td')[0].text_content().split('(')
    except:
        try:
            areas = f[0].xpath(".//../../../tr//th//div[contains(text(), 'Total')]//../../td")[0].text_content().split(
                "(")
        except:
            areas = f[0].xpath('./../following-sibling::tr/td')[0].text_content().split("(")
    for area in areas:  # find area in km2
        if 'km2' in area:
            break
    area = clean_string(area)
    return area


def get_population(infobox):
    h = infobox[0].xpath("//table//th//a[contains(text(), 'Population')]")  # sometimes a link
    if not h:
        h = infobox[0].xpath("//table//th[contains(text(), 'Population')]")  # sometimes not a link
    try:
        population = h[0].xpath('./../../following-sibling::tr/td')[0].text_content().split('(')[0]
    except:
        population = h[0].xpath('./../following-sibling::tr/td')[0].text_content().split('(')[0]
    population = clean_string(population)
    return population


def get_info_from_country(country, url, g):
    res = requests.get(url)
    doc = lxml.html.fromstring(res.content)
    a = doc.xpath("//table[contains(@class, 'infobox')]")

    capital = get_capital(a)
    if country == 'Vatican_City':  # cheating here
        capital = 'Vatican City'
    if country == 'Singapore':  # also here
        capital = 'Singapore'
    print("Capital city: ", capital)

    government = get_government(a)
    print("Government: ", government)

    president, dob_pres = get_president(a)
    if president != 'None':
        print("President: ", president, ", born: ", dob_pres)
    else:
        print("President: Does not have a president")

    prime_minister, dob_pm = get_pm(a)
    if prime_minister != 'None':
        print("Prime minister: ", prime_minister, ", born: ", dob_pm)
    else:
        print("Prime minister: Does not have prime minister")

    area = get_area(a)
    print("Area: ", area)

    population = get_population(a)
    print("Population: ", population)

    from rdflib import Literal, XSD
    ontology_prefix = 'http://geo.org/'
    government_rel          = rdflib.URIRef(ontology_prefix + 'government')
    president_of_rel           = rdflib.URIRef(ontology_prefix + 'president_of')
    prime_minister_of_rel      = rdflib.URIRef(ontology_prefix + 'prime_minister_of')
    president_rel           = rdflib.URIRef(ontology_prefix + 'president')
    prime_minister_rel      = rdflib.URIRef(ontology_prefix + 'prime_minister')
    area_rel                = rdflib.URIRef(ontology_prefix + 'area')
    population_rel          = rdflib.URIRef(ontology_prefix + 'population')
    capital_rel             = rdflib.URIRef(ontology_prefix + 'capital')
    born_rel                = rdflib.URIRef(ontology_prefix + 'born')

    country                 = rdflib.URIRef(ontology_prefix + country)
    capital                 = rdflib.URIRef(ontology_prefix + capital.replace(' ','_'))
    area                    = rdflib.URIRef(ontology_prefix + area.replace(' ','_'))
    population              = rdflib.URIRef(ontology_prefix + population.replace(' ','_'))
    government              = rdflib.URIRef(ontology_prefix + government.replace(' ','_'))
    president               = rdflib.URIRef(ontology_prefix + president)
    prime_minister          = rdflib.URIRef(ontology_prefix + prime_minister)
    born_pm                 = rdflib.URIRef(ontology_prefix + dob_pm.replace(' ','_'))
    born_pres               = rdflib.URIRef(ontology_prefix + dob_pres.replace(' ','_'))

    g.add((country, area_rel, area))
    g.add((country, population_rel, population))
    g.add((country, government_rel, government))
    g.add((country, capital_rel, capital))
    g.add((country, prime_minister_rel, prime_minister))
    g.add((country, president_rel, president))
    if prime_minister != 'None':
        g.add((prime_minister, prime_minister_of_rel, country))
        g.add((prime_minister, born_rel, born_pm))
    if president != 'None':
        g.add((president, president_of_rel, country))
        g.add((president, born_rel, born_pres))


def get_countries(url, g):
    start_time = time.time()
    res = requests.get(url)
    doc = lxml.html.fromstring(res.content)

    countries = doc.xpath("//table[@class='nowrap sortable mw-datatable wikitable']//tr//td[1]")
    # for i in range(8,len(countries)):
    for i in range(len(countries)):
        country_url = countries[i].xpath(".//a/@href")[0]
        name = country_url.split('/')[-1]
        print(name, " ", wiki_prefix + country_url)
        get_info_from_country(name, wiki_prefix + country_url, g)
        print()
    print("ontology creation time: %s seconds" % (time.time() - start_time))


def query(w, entity, relation):
    entity = entity.replace(" ", "_")
    query = None
    if w == "who":

        if relation == "president":
            query = """SELECT ?born WHERE {
                ?born <http://geo.org/president_of> <http://geo.org/""" + entity + """>
                       }"""

        elif relation == "prime minister":
            query = """SELECT ?born WHERE {
                           ?born <http://geo.org/prime_minister_of> <http://geo.org/""" + entity + """>
                       }"""
        elif relation == "":
            query = """SELECT ?country WHERE {
                            <http://geo.org/""" + entity + """> <http://geo.org/president_of> ?country
                       }"""
            for ans in g.query(query):
                print("President of " + ans["country"].split("/")[-1].replace("_", " "))
            query = """SELECT ?country WHERE {
                                        <http://geo.org/""" + entity + """> <http://geo.org/prime_minister_of> ?country
                                   }"""
            for ans in g.query(query):
                print("Prime minister of " + ans["country"].split("/")[-1].replace("_", " "))
            return
    elif w == "what":
        query = """SELECT ?""" + relation + """ WHERE {
            <http://geo.org/""" + entity + """> <http://geo.org/""" + relation + """> ?""" + relation + """
        }"""

    elif w == "when":
        if relation == "president":
            query = """SELECT ?born WHERE {
                ?person <http://geo.org/president_of> <http://geo.org/""" + entity + """>  .
                ?person <http://geo.org/born> ?born .
            }"""
        elif relation == "prime minister":
            query = """SELECT ?born WHERE {
                ?person  <http://geo.org/prime_minister_of> <http://geo.org/""" + entity + """> .
                ?person <http://geo.org/born> ?born .
            }"""

    for ans in g.query(query):
        ans_dict = ans.asdict()
        if len(ans_dict) > 1:
            print("Got multiple results:")
            print(ans_dict)

        if relation == "prime minister" or relation == "president":
            print(ans["born"].split("/")[-1].replace("_", " "))
        elif relation == "area" or relation == "population" or relation == "government" or relation == "capital":
            print(ans[relation].split("/")[-1].replace("_", " "))


one_word_relation = {"president", "population", "area", "government", "capital"}
two_word_relation = {"prime minister"}

def fetch_relation(relation_arr):
    if relation_arr[0].lower() in one_word_relation:
        return relation_arr[0]
    else:
        return " ".join(relation_arr[0:2])

# Cases:
# Who is the <relation> of <entity>?
# Who is <entity>?
def handle_who_question(who_arr):
    if who_arr[2] == 'the':
        relation = fetch_relation(who_arr[3:])
        entity = " ".join(who_arr[2+len(relation.split())+2:])
        query(w="who", entity=entity, relation=relation)

    elif who_arr[1] == 'is':
        entity = " ".join(who_arr[2:])
        query(w="who", entity=entity, relation="")

# Cases:
# What is the <relation> of <entity>?
def handle_what_question(what_arr):
    relation = fetch_relation(what_arr[3:])
    entity = " ".join(what_arr[2 + len(relation.split()) + 2:])
    query(w="what", entity=entity, relation=relation)

# Cases:
# When was the <relation> of <entity> born?
def handle_when_question(when_arr):
    relation = when_arr[3] if when_arr[3] == "president" else " ".join(when_arr[3:5])
    entity = " ".join(when_arr[4 +  len(relation.split(" ")):-1])
    query(w="when", entity=entity, relation=relation)


def answer_question(question_arr):
    question_arr[-1] = question_arr[-1].replace("?", "")
    w_question = question_arr[0]

    if w_question.lower() == "who":
        handle_who_question(question_arr)
    elif w_question.lower() == "what":
        handle_what_question(question_arr)
    elif w_question.lower() == "when":
        handle_when_question(question_arr)
    else:
        sys.exit("Unrecognized first word!")


g = None
def main(argv):
    global g
    if len(argv) < 1:
        sys.exit("Wrong amount of arguments!")
    elif argv[1] == 'create' and len(argv) == 3:
        g = rdflib.Graph()
        get_countries("https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)", g)
        g.serialize(argv[2], format='nt')
        # get_info_from_country("Tanzania", "http://en.wikipedia.org/wiki/Tanzania")

    elif argv[1] == 'question':
        g = rdflib.Graph()
        g.parse("ontology.nt", format="nt")
        if len(argv) < 5:
            sys.exit("Question too short!")
        answer_question(argv[2:])
    else:
        sys.exit("Invalid argument!")


if __name__ == '__main__':
    main(sys.argv)
