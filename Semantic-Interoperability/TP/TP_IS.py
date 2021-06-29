import requests
import json
import textwrap
import pymysql
import time
import os
from prettytable import PrettyTable

MY_API_KEY = "5397c52589baa538eff6390b91b4ed3e"
HOST = "localhost"
USERNAME = "root"
PASSWORD = "root"

def getOrcidsVerified():
    database = pymysql.connect(host="localhost", user="root", passwd="root", db="orcid_db")
    cursor = database.cursor()
    status = "VERIFIED"
    sql = "select count(*) from orcid_authors where status=%s"
    cursor.execute(sql, [status])
    data = cursor.fetchall()
    for n in data:
        return str(n[0])

def getOrcidsInserted():
    database = pymysql.connect(host="localhost", user="root", passwd="root", db="orcid_db")
    cursor = database.cursor()
    valor = 0
    sql = "select count(distinct orcid) from orcid_eid_wos"
    cursor.execute(sql)
    data = cursor.fetchall()
    for n in data:
        return str(n[0])

def getSizeTable(table):
    database = pymysql.connect(host="localhost", user="root", passwd="root", db="orcid_db")
    cursor = database.cursor()
    try:
        sizeKB = 0
        sizeMB = 0
        db = "orcid_db"
        query_analyze = "analyze table " + table
        cursor.execute(query_analyze)
        database.commit()
        new_query = "select round(((data_length + index_length)/1024),2), round(((data_length + index_length)/1024/1024),2) from information_schema.TABLES "
        new_query += "where table_schema=%s and table_name=%s"
        cursor.execute(new_query, (db, table))
        data = cursor.fetchall()
        for row in data:
            sizeKB = row[0]
            sizeMB = row[1]
    except(pymysql.Error, pymysql.Warning) as e:
        print(e)
    database.close()
    return sizeKB, sizeMB

def hasData():
    lOrcids = []
    lEids = []
    database = pymysql.connect(host="localhost", user="root", passwd="root", db="orcid_db")
    cursor = database.cursor()
    sql = "select distinct orcid from orcid_eid_wos"
    cursor.execute(sql)
    data = cursor.fetchall()
    for n in data:
        lOrcids.append(n[0])
    database.commit()
    cursor2 = database.cursor()
    sql2 = "select eid from scopusid"
    cursor2.execute(sql2)
    data2 = cursor2.fetchall()
    for n2 in data2:
        lEids.append(n2[0])
    database.commit()
    for elem in lOrcids:
        flag = 1
        cursor3 = database.cursor()
        sql3 = "select eid from orcid_eid_wos where orcid=%s"
        cursor3.execute(sql3, [elem])
        data3 = cursor3.fetchall()
        for n3 in data3:
            if s(n3[0]) not in lEids:
                break
        addHTML(elem)

def addHTML(orcid):
    orcid = orcid.replace("'","")
    script_dir = os.path.dirname(__file__)
    rel_path = "website/templates/escolhe.html"
    abs_file_path = os.path.join(script_dir, rel_path)
    with open(abs_file_path, "r", encoding='utf8') as file:
        readFile = file.read()
    addText = """   <form method="post" action="list/"""+orcid+"""">
          <input type="hidden" name="extra_submit_param" value="submit_param">
          <button type="submit" name="submit_param" value="submit_value" class="link-button">
            <p class="texto2">Orcid número: """+orcid+"""</p>
          </button>
        </form>""" + "\n" + """</div>
{% endblock %}"""
    newFile = readFile.replace("""</div>
{% endblock %}""", addText)
    with open(abs_file_path, "w", encoding='utf8') as file2:
        file2.write(newFile)




def verifyOrcid(orcid):
    database = pymysql.connect(host="localhost", user="root", passwd="root", db="orcid_db")
    cursor = database.cursor()
    status = "VERIFIED"
    sql = "update orcid_authors set status=%s where orcid=%s"
    cursor.execute(sql, (status, orcid))
    database.commit()

def timeStr(time):
    if time > 60:
        time = time/60
        minutes = str(round(time)) + " minutes"
        sec = (time % 1)*60
        seconds = str(round(sec)) + " seconds"
        time = minutes + " and " + seconds
    else:
        time = str(round(time, 2)) + " seconds"
    return time

def getOrcids():
    database = pymysql.connect(host="localhost", user="root", passwd="root", db="orcid_db")
    cursor = database.cursor()
    l = []
    sql = "select orcid from orcid_authors"
    cursor.execute(sql)
    data = cursor.fetchall()
    for n in data:
        l.append(n[0])
    return l

def getOrcidName(orcid):
    name = ""
    url = ("https://pub.orcid.org/v3.0/"+orcid)
    resp = requests.get(url, headers={'Accept':'application/json'})
    results = resp.json()
    try:
        first_name = results['person']['name']['given-names']['value'] 
    except:
        first_name = ""
    try:
        last_name = results['person']['name']['family-name']['value']
    except:
        last_name = ""
    if first_name == "" and last_name == "":
        all_name = ""
    elif last_name == "":
        all_name = first_name
    elif first_name == "":
        all_name = last_name
    else:
        all_name = first_name + " " + last_name
    return all_name

def addOrcids():
    oldSizeKB, oldSizeMB = getSizeTable("orcid_authors")
    oldSizeKB = float(oldSizeKB)
    oldSizeMB = float(oldSizeMB)
    database = pymysql.connect(host="localhost", user="root", passwd="root", db="orcid_db")
    cursor = database.cursor()
    timeStart = time.time()
    url = ("https://pub.orcid.org/v3.0/search?q=affiliation-org-name:Universidade do Minho")
    resp = requests.get(url, headers={'Accept':'application/json'})
    results = resp.json()
    for r in results['result']:
        if r['orcid-identifier']['path'] not in getOrcids():
            name = getOrcidName(r['orcid-identifier']['path'])
            status = "UNVERIFIED"
            sql = "insert into orcid_authors (orcid,grupo,lab,nome,integrado,status) values (%s,null,null,%s,null,%s)"
            cursor.execute(sql, (r['orcid-identifier']['path'], name, status))
            print("\nOrcid "+r['orcid-identifier']['path']+" inserted\n")
            database.commit()
    database.close()
    newSizeKB, newSizeMB = getSizeTable("orcid_authors")
    newSizeKB = float(newSizeKB)
    newSizeMB = float(newSizeMB)
    timeEnd = time.time()
    timeStatus = timeEnd - timeStart
    newsizeKB = newSizeKB - oldSizeKB
    newsizeMB = newSizeMB - oldSizeMB
    return timeStr(timeStatus), str(newsizeKB), str(newsizeMB)

def menuAuthor():
    database = pymysql.connect(host="localhost", user="root", passwd="root", db="orcid_db")
    cursor = database.cursor()
    nome = input("Nome: ")    
    grupo = input("Grupo: ")
    lab = input("Lab: ")
    integrado = input("Integrado em: ")
    orcid = input("Número do orcid: ")
    status = "UNVERIFIED"
    sql = "insert into orcid_authors (orcid,grupo,lab,nome,integrado,status) values (%s,%s,%s,%s,%s,%s)"
    cursor.execute(sql, (orcid,grupo,lab,nome,integrado,status))
    database.commit()
    database.close()
    print("\nRegisto feito com sucesso\n")

def s(texto_):
    return "'" + texto_.replace("'"," ") + "'"

def ss(texto_):
    return "\"" + texto_ + "\""

def sss(texto_):
    texto_ = texto_.replace("'","")
    return texto_

def get_scopus_info(SCOPUS_ID):
    url = ("http://api.elsevier.com/content/abstract/scopus_id/" + SCOPUS_ID + "?field=creator,title,publicationName,volume,issueIdentifier," 
        + "prism:pageRange,coverDate,article-number,doi,issn,citedby-count,prism:aggregationType,subtypeDescription,affiliation")
    resp = requests.get(url, headers={'Accept':'application/json', 'X-ELS-APIKey' : MY_API_KEY})
    return json.loads(resp.text.encode('utf-8'))

def getSJR(issn):
    resp = requests.get("https://api.elsevier.com/content/serial/title/issn/"+issn, headers={'Accept':'application/json', 'X-ELS-APIKey' : MY_API_KEY})
    results = resp.json()
    try:
        for r in results['serial-metadata-response']['entry']:
            for n in r['SJRList']['SJR']:
                data = n['$']
    except:
        data = ""
    return data


def get_eids_wos(ORCID_ID):
    my_list = []
    my_dic = {}
    try:
        resp = requests.get("https://pub.orcid.org/v3.0/"+ORCID_ID+"/works", headers={'Accept':'application/json'})
        results = resp.json()
    except:
        return my_dic
    for r in results['group']:
        for r2 in r['work-summary']:
            try:
                my_list.append(r2['url']['value'])
            except:
                my_list.append('')

    for r in my_list:
        if r.find('eid=') > 0:
            k1 = r.find('eid=')
            k2 = r.find('&',k1)
            if r[k1+11:k2] not in my_dic:
                my_dic[r[k1+11:k2]] = '-'
        elif r.find('KeyUT=') > 0:
            v1 = r.find('KeyUT=')
            v2 = r.find('&',v1)
            try:
                my_dic[list(my_dic.keys())[-1]] = r[v1+10:v2] 
            except:
                print("Can't get wos!\n")

    return my_dic


def work(number):
    timeStart = time.time()
    oldSizeKB_scopus, oldSizeMB_scopus = getSizeTable("scopusid")
    oldSizeKB_scopus = float(oldSizeKB_scopus)
    oldSizeMB_scopus = float(oldSizeMB_scopus)
    database = pymysql.connect(host="localhost", user="root", passwd="root", db="orcid_db")
    print("Ligação à base de dados efetuada com sucesso")
    i=0

    cursor = database.cursor()
    status = "UNVERIFIED"
    sql = "select orcid,grupo,lab,nome,integrado,status from orcid_authors where status like %s limit " + number
    cursor.execute(sql, [status])
    data = cursor.fetchall()
    print(data)

    for resultado in data:
        ORCID_ID = resultado[0]
        verifyOrcid(ORCID_ID)
        for sid, wos in get_eids_wos(ORCID_ID).items():
            i += 1
            print(i)
            print(sid)
            print(ORCID_ID)
            print(wos)
            print("\n")
            gravar = 1
            sql = "select * from scopusid where eid = " + ss(s(sid))
            cursor2 = database.cursor()
            cursor2.execute(sql)
            resultSet = cursor2.fetchone()
            if (resultSet == None):
                results = get_scopus_info(sid)

                title = ""
                journal = ""
                volume = ""
                issn = ""
                date = ""
                doi = ""
                localization = ""
                type_publication = ""
                sjr = ""
                cites = 0
                gravar = 0

                try:
                    authors = ', '.join([au['ce:given-name'] + " " + au['ce:surname'] for au in results['abstracts-retrieval-response']['coredata']['dc:creator']['author']])
                except:
                    authors = ""
                if authors == "":
                    try:
                        authors = ', '.join([au['preferred-name']['ce:given-name'] + " " + au['preferred-name']['ce:surname'] for au in results['abstracts-retrieval-response']['coredata']['dc:creator']['author']])
                    except:
                        authors = "-"

                try:
                    title = results['abstracts-retrieval-response']['coredata']['dc:title']
                    gravar = 1
                except:
                    title = "-"

                try:
                    journal = results['abstracts-retrieval-response']['coredata'].get('prism:publicationName', '')
                except:
                    journal = "-"

                try:
                    volume = results['abstracts-retrieval-response']['coredata'].get('prism:volume', '-')
                except:
                    volume = "-"

                try:
                    issn = results['abstracts-retrieval-response']['coredata'].get('prism:issn', "-")
                except:
                    issn = "-"
                if " " in issn:
                    data = issn.split(" ")
                    issn = data[1]

                try:
                    date = results['abstracts-retrieval-response']['coredata']['prism:coverDate']
                    date = date[0:4]
                except:
                    date = "-"

                try:
                    doi = results['abstracts-retrieval-response']['coredata'].get('prism:doi', "-")
                except:
                    doi = "-"

                try:
                    localization = results['abstracts-retrieval-response']['affiliation']['affiliation-city'] + ", " + results['abstracts-retrieval-response']['affiliation']['affiliation-country']
                except:
                    localization = "-"

                try:
                    type_publication = results['abstracts-retrieval-response']['coredata']['subtypeDescription']
                except:
                    type_publication = "-"

                if issn == "-":
                    sjr = "-"
                else:
                    try:
                        sjr = getSJR(issn)
                    except:
                        sjr = "-"

                try:
                    cites = int(results['abstracts-retrieval-response']['coredata']['citedby-count'])
                except:
                    cites = 0

                if (gravar==1):
                    try:
                        sql = "insert into scopusid (eid,authors,title,year,source,cited,issn,doi,localization,publication_type,sjr) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                        cursor = database.cursor()
                        cursor.execute(sql, (s(sid), authors, s(title), date, s(journal), str(cites), issn, doi, localization, type_publication, sjr))
                        database.commit()
                    except:
                        print(authors)
                        print(title)
                        print(date)
                        print(journal)
                        print(str(cites))
                        print(issn)
                        print(doi)
                        print(localization)
                        print(type_publication)
                        print(sjr)
                        gravar = 0

            if (gravar==1):
                sql = "select * from orcid_eid_wos where eid = %s and orcid = %s and wos = %s"
                cursor3 = database.cursor()
                cursor3.execute(sql, (sss(sid), sss(ORCID_ID), sss(wos)))
                resultSet = cursor3.fetchone()
                if (resultSet == None):
                    sql = "insert into orcid_eid_wos (orcid,eid,wos) values (%s,%s,%s)" 
                    cursor = database.cursor()
                    cursor.execute(sql, (ORCID_ID, sid, wos))
                    database.commit()
                cursor3.close()
            cursor2.close()
    cursor.close()
    database.close()
    print("Ligação à base de dados encerrada com sucesso")
    timeEnd = time.time()
    newSizeKB_scopus, newSizeMB_scopus = getSizeTable("scopusid")
    newSizeKB_scopus = float(newSizeKB_scopus)
    newSizeMB_scopus = float(newSizeMB_scopus)
    timeStatus = timeEnd - timeStart
    newsizeKB_scopus = newSizeKB_scopus - oldSizeKB_scopus
    newsizeMB_scopus = newSizeMB_scopus - oldSizeMB_scopus
    return timeStr(timeStatus), str(newsizeKB_scopus), str(newsizeMB_scopus)


def main():
    while True:
        print("\nBem-Vindo ao registo de docentes.\n")
        print("\n1 - Registar docente\n")
        print("\n2 - Adicionar publicações dos docentes\n")
        print("\n3 - Guardar orcids de docentes da Universidade do Minho\n")
        print("\n0 - Saír\n")
        print("\n_______________________________________________________\n")

        option = input("Enter: ")
        if option=="1":
            menuAuthor()
        elif option=="2":
            new_option = input("\nIntroduza a quantidade de orcids que quer verificar: ")
            while not new_option.isnumeric():
                new_option = input("\nIntroduza a quantidade de orcids que quer verificar: ")

            time, sizeKB_scopus, sizeMB_scopus = work(new_option)
            hasData()
            number_orcids = getOrcidsInserted()
            table = PrettyTable()
            table.field_names = ['Number of Orcids Verified', 'Adding information', 'Size Of scopusid Table (KB)', 'Size Of scopusid Table (MB)']
            table.add_row([number_orcids, time, sizeKB_scopus, sizeMB_scopus])
            with open("Complexidade_AdicionarInfo.txt", "a") as file:
                file.write("\n\n" + str(table))
            print(table)
        elif option=="3":
            time, sizeKB, sizeMB = addOrcids()
            number_orcids = getOrcidsVerified()
            table = PrettyTable()
            table.field_names = ['Number of Orcids Inserted', 'Time adding Orcids', 'Size Of Orcids Table (KB)', 'Size Of Orcids Table (MB)']
            table.add_row([number_orcids, time, sizeKB, sizeMB]) 
            with open("Complexidade_AdicionarOrcids.txt", "a") as file:
                file.write("\n\n" + str(table))
            print(table)
        elif option=="0":
            break
        elif True:
            print("\nInvalid Option!\n")
            time.seep(1)


if __name__ == "__main__":
    main()
