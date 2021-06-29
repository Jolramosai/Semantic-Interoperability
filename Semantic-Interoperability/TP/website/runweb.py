from flask import Flask, redirect, url_for, render_template, request
import pymysql

app = Flask(__name__)


def s(texto_):
    return "'" + texto_.replace("'"," ") + "'"

def getInfo(orcid):
    database = pymysql.connect(host="localhost", user="root", passwd="root", db="orcid_db")
    cursor = database.cursor()
    temp = []
    l = []
    sql0 = "select eid, wos from orcid_eid_wos where orcid=%s"
    cursor.execute(sql0, [orcid])
    data = cursor.fetchall()
    for elem in data:
        sql = "select title, year, localization, publication_type, authors, cited, sjr from scopusid where eid = %s"
        cursor.execute(sql, [s(elem[0])])
        data2 = cursor.fetchall()
        temp.append(elem[0])
        temp.append(elem[1])
        l += [temp+list(i) for i in data2]
        temp.clear()
    return l




def author(orcid):
    database = pymysql.connect(host="localhost", user="root", passwd="root", db="orcid_db")
    cursor = database.cursor()
    sql = "select nome from orcid_authors where orcid=%s"
    cursor.execute(sql, [orcid])
    data = cursor.fetchall()
    for elem in data:
        auth = elem[0]
    return auth



@app.route("/")
def home():
    return render_template("index.html")

@app.route("/list", methods=['GET', 'POST'])
def escolhe():
    if request.method == 'POST':
        return redirect(url_for('home'))
    return render_template("escolhe.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    f = request.form 
    for key in f.keys():
        value = f.getlist(key)
    if request.method == "POST":
        return redirect(url_for("lista", orcid=value))
    else:
        return render_template("escolhe.html")



@app.route("/list/<orcid>", methods=['GET', 'POST'])
def lista(orcid):
    l = getInfo(orcid)
    auth = author(orcid)
    if request.method == 'POST':
        return render_template('lista.html', content=l, orc=orcid, author=auth)
    else:
        return redirect(url_for('home'))



if __name__ == "__main__":
    app.run()