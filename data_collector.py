import requests,json,time,datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date,func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import argparse

HOST = '127.0.0.1'
PORT = 3306
USERNAME = 'root'
PASSWORD = 'No.89757'
DB = 'covid_19'
DB_URI = f'mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DB}'

Base = declarative_base()
engine = create_engine(url=DB_URI, echo=True, future=True)
class historical_records(Base):
    __tablename__ = 'historical_records'
    date= Column(Date, primary_key = True)
    confirm = Column(Integer, nullable = False)
    heal = Column(Integer, nullable = False)
    dead = Column(Integer, nullable = False)
    confirm_add = Column(Integer, nullable = False)
    heal_add = Column(Integer, nullable = False)
    dead_add = Column(Integer, nullable = False)

class details_records(Base):
    __tablename__ = 'details_records'
    id = Column(Integer, primary_key = True)
    update_time = Column(DateTime(), nullable = False)
    province = Column(String(100), nullable = False)
    city = Column(String(100), nullable = False)
    confirm = Column(Integer(), nullable = False)
    confirm_add = Column(Integer(), nullable = False)
    heal = Column(Integer(), nullable = False)
    dead = Column(Integer(), nullable = False) 

def collect_data():
    url1 = "https://api.inews.qq.com/newsqa/v1/query/inner/publish/modules/list?modules=statisGradeCityDetail,diseaseh5Shelf"
    url2 = "https://view.inews.qq.com/g2/getOnsInfo?name=disease_other"

    r1 = requests.get(url1).json()['data'] #当日疫情数据
    r2 = requests.get(url2).json()['data'] #历史疫情数据

    today_details = []

    for prov_info in r1['diseaseh5Shelf']['areaTree'][0]['children']:
        province_name = prov_info['name']
        province_total = prov_info['total']
        province_today = prov_info['today']
        update_time = province_total['mtime']
        confirm = province_total['confirm']
        confirm_add = province_today['confirm']
        heal = province_total['heal']
        dead = province_total['dead']
        today_details.append([update_time,province_name,'全省统计', confirm, confirm_add, heal, dead])
        for city_infos in prov_info["children"]:
                city = city_infos["name"]
                update_time = city_infos['total']['mtime']
                confirm = city_infos["total"]["confirm"]
                confirm_add = city_infos["today"]["confirm"]
                heal = city_infos["total"]["heal"]
                dead = city_infos["total"]["dead"]
                today_details.append([update_time,province_name, city, confirm, confirm_add, heal, dead])
    
    history = {}
    for historical_day_record in json.loads(r2)['chinaDayList']:
        date = time.strftime("%Y-%m-%d", time.strptime(historical_day_record['y']+'.'+ historical_day_record['date'], "%Y.%m.%d"))
        confirm  = historical_day_record['confirm']
        dead = historical_day_record['dead']
        heal = historical_day_record['heal']
        history[date] = {"confirm": confirm, "heal": heal, "dead": dead,"confirm_add": -1, "heal_add": -1, "dead_add": -1}

    for historical_dayadd_record in json.loads(r2)['chinaDayAddList']:
        date = time.strftime("%Y-%m-%d", time.strptime(historical_dayadd_record['y']+'.'+ historical_dayadd_record['date'], "%Y.%m.%d"))
        confirm = historical_dayadd_record["confirm"]
        heal = historical_dayadd_record["heal"]
        dead = historical_dayadd_record["dead"]
        if date in history:
            history[date]['confirm_add'] = confirm 
            history[date]['heal_add'] = heal
            history[date]['dead_add'] = dead 
        else:
            history[date] = {"confirm": -1, "heal": -1, "dead": -1,"confirm_add": confirm, "heal_add": heal, "dead_add": dead}

    return history, today_details

def init_database():
    history, details = collect_data()
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind = engine)
    session = Session()

    session.add_all([details_records(update_time=dataline[0],
                 province = dataline[1],
                 city = dataline[2],
                 confirm = dataline[3],
                 confirm_add = dataline[4],
                 heal = dataline[5],
                 dead = dataline[6]) for dataline in details])
    session.commit()

    session.add_all([historical_records(date = key,
                    confirm = history[key]['confirm'],
                    heal = history[key]['heal'],
                    dead = history[key]['dead'],
                    confirm_add = history[key]['confirm_add'],
                    heal_add = history[key]['heal_add'],
                    dead_add = history[key]['dead_add']) for key in history])
    session.commit()
    session.close()
    
def update_database():
    history, details = collect_data()
    Session = sessionmaker(bind = engine)
    session = Session()
    #update details
    for detail in details:
        update_time,province, city, confirm, confirm_add, heal, dead = detail 
        # Iteratively check if each city is the latest update
        # if province and city already in the table, check the update time to decide if update
        # otherwise, insert a new row 
        query_check = session.query(details_records).filter(details_records.province==province, details_records.city == city).all()
        if query_check and query_check[0].update_time < datetime.datetime.strptime(update_time, "%Y-%m-%d %H:%M:%S"):
            query_check[0].update_time, query_check[0].confirm,query_check[0].confirm_add, query_check[0].heal, query_check[0].dead = update_time, confirm, confirm_add, heal, dead
        elif not query_check:
            session.add(details_records(update_time=update_time,
                 province = province,
                 city = city,
                 confirm = confirm,
                 confirm_add = confirm_add,
                 heal = heal,
                 dead = dead))
    
    session.commit()

    #update historical records 
    # query the record of last day
    # check if there's any record in new scraped record in history, insert that record.
    latest_update = session.query(func.max(historical_records.date)).first()[0]
    for key in history:
        if datetime.date.fromisoformat(key) > latest_update:
            session.add(historical_records(
                date = key,
                confirm = history[key]['confirm'],
                heal = history[key]['heal'],
                dead = history[key]['dead'],
                confirm_add = history[key]['confirm_add'],
                heal_add = history[key]['heal_add'],
                dead_add = history[key]['dead_add']
        ))
    
    session.commit()

    session.close()
            


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='select a method to start your detector')

    parser.add_argument('-init',action='store_true',default=False, help='init the datebase, you should run this parameter in the first run')

    parser.add_argument('-update',action='store_true',default=False, help='update the datebase')

    args = parser.parse_args()
    if args.init:
        init_database()
    if args.update:
        update_database()
