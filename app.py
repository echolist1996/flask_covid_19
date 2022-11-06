from flask import Flask
from flask import render_template
from flask import jsonify
from flask import render_template
from flask import jsonify
from config import DB_URI
from sqlalchemy import create_engine,text
import utils

app = Flask(__name__)
# print(SQLALCHEMY_DATABASE_URI)

engine = create_engine(url=DB_URI, echo=True, future=True)

        
@app.route('/')
def hello_world():
    return render_template('main.html')

@app.route('/c1')
def get_c1_data():
	data = utils.get_c1_data()
	return jsonify({"confirm":data[0],"suspect":0,"heal":data[1],"dead":data[2]})

@app.route('/c2')
def get_c2_data():
    res = []
    for tup in utils.get_c2_data():
        res.append({"name":tup[0],"value":int(tup[1])})
    return jsonify({"data":res})

@app.route("/l1")
def get_l1_data():
    data = utils.get_l1_data()
    day,confirm,heal,dead = [],[],[],[]
    for date,c,h,d in data:   
        day.append(date.strftime("%Y-%m-%d")) 
        confirm.append(c)
        heal.append(h)
        dead.append(d)
    return jsonify({"day":day,"confirm": confirm, "heal": heal, "dead": dead})

@app.route("/l2")
def get_l2_data():
    data = utils.get_l2_data()
    day, confirm_add, heal_add = [], [], []
    for a, b, c in data[7:]:
        day.append(a.strftime("%Y-%m-%d"))  
        confirm_add.append(b)
        heal_add.append(c)
    return jsonify({"day": day, "confirm_add": confirm_add, "suspect_add": heal_add})# 疑似改治愈

@app.route("/r1")
def get_r1_data():
    data = utils.get_r1_data()
    province = []
    confirm = []
    for k,v in data:
        province.append(k)
        confirm.append(int(v))
    return jsonify({"province": province, "confirm": confirm})

if __name__ == '__main__':
    app.run()