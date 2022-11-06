from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date,func, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from data_collector import *

# collect data of total statistical magnitude
def get_c1_data():
    Session = sessionmaker(bind = engine)
    session = Session()
    res = session.query(func.sum(details_records.confirm),func.sum(details_records.heal),func.sum(details_records.dead)).where(details_records.city=='全省统计').first()
    session.close()
    return res

def get_c2_data():
    Session = sessionmaker(bind = engine)
    session = Session()
    data = session.query(details_records.province, details_records.confirm_add).where(details_records.city=='全省统计').all()
    session.close()
    return data

def get_l1_data():
    Session = sessionmaker(bind = engine)
    session = Session()
    res = session.query(historical_records.date, 
                    historical_records.confirm, 
                    historical_records.heal, 
                    historical_records.dead).where(historical_records.confirm!=-1).all()
    session.close()
    return res
    
def get_l2_data():
    Session = sessionmaker(bind = engine)
    session = Session()
    res = session.query(historical_records.date, 
                    historical_records.confirm_add, 
                    historical_records.heal_add).where(historical_records.confirm_add!=-1, historical_records.confirm_add<100000).all()
    return res

def get_r1_data():
    Session = sessionmaker(bind = engine)
    session = Session()
    data = session.query(details_records.province, details_records.confirm_add).where(details_records.city=='全省统计').order_by(desc(details_records.confirm_add)).limit(5).all()
    session.close()
    return data