#!/usr/bin/env python
# coding: utf-8

import os
import sys
from pathlib import Path
import argparse
import logging
from logging.handlers import RotatingFileHandler
import yaml
import pandas as pd
import datetime
from pandas.api.types import is_datetime64_ns_dtype
from influxdb import DataFrameClient
import logging
from logging.handlers import RotatingFileHandler
from pytz import timezone

#app_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.getcwd()
tmp_dir = app_dir + "/tmp"
log_dir = app_dir + "/logs"
conf_dir = app_dir + "/conf"
lib_dir = app_dir + "/lib"
target_dir = [tmp_dir, log_dir, conf_dir, lib_dir]

def createDirectory(directory):
    try:
        for path in directory:
             if not os.path.exists(path):
                os.makedirs(path)
    except OSError:
         print("Error: Failed to create the directory.")

createDirectory(target_dir)

log_file = log_dir + "/SystemChecker.log"
logger = logging.getLogger()
logger.setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=20240000, backupCount=3)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
sys.path.append(lib_dir)
import SmsClient
from influxdb_conn import influxDB_C
with open(conf_dir + '/default.yml') as config_file:
    configs = yaml.safe_load(config_file)
    

def select_influxdb(query):
    dbHost = configs['INFLUXDB']['host']
    dbPort = configs['INFLUXDB']['port']
    dbUser = configs['INFLUXDB']['user']
    dbPwd = configs['INFLUXDB']['password']
    dbName = configs['INFLUXDB']['db']
    try:
        conn = influxDB_C(dbHost, dbPort, dbUser, dbPwd, dbName)
    except:
        logger.error("Can not collect INFLUXDB")
        
    try:
        result = conn.dbSelect(query)
        return (result)
    except:
        return (pd.DataFrame())
        logger.error("Can not %s" %query)

inventory_file = conf_dir + '/inventory'
def inventory_to_dataframe(target_file):
    try:
        os.path.exists(target_file)
        df = pd.read_csv(target_file, comment = '#')
    except:
        return ("invetnory file is not exist!")
    
    return (df[['hostname']])


def check_server():
    subject = 'check_server'
    if configs['CHECK_SERVER']['use_yn'] == 'use':
        # inventory ????????? ?????? ??? ?????? ????????? df??? ?????????.
        inventory_df = inventory_to_dataframe(inventory_file)
        # CHECK_SERVER ??????????????? ????????? ???????????? ????????? ?????? ????????? ????????????.
        response_df = select_influxdb(configs['CHECK_SERVER']['query'])
        try:
            if 'disk_status' in response_df:
                # DB ?????? ???????????? index ??????
                response_df = response_df['disk_status']
                response_df = response_df.rename_axis('time').reset_index()
                # ?????? host ????????? ????????? host ????????? left join
                result_df = pd.merge(inventory_df, response_df, left_on='hostname', right_on='host', how='left')
                # join ??? time ??? ?????? ????????? ?????? ???????????? ??????
                last_time = result_df[result_df['time'].notnull()].max()
                result_df.replace({'time': {None: last_time['time']}}, inplace=True)
                # disk status ??? ???????????? ?????? host??? ??????
                result_df = result_df[result_df['host'].isnull()]
                result_df = result_df[['hostname','time']]
                # subject column ??????
                result_df.insert(0, 'subject', subject)
                # hostname ?????? ????????? host ??? ??????
                result_df.rename(columns = {'hostname':'host'}, inplace=True)
                return (result_df)
        except:
            logger.error("Can not collect INFLUXDB")


def check_disk():
    subject = 'disk'
    # ?????? ?????? ??????
    if configs['CHECK_DISK']['use_yn'] == 'use':
        response_df = select_influxdb(configs['CHECK_DISK']['query'])
        try:
            if 'disk_status' in response_df:
                # DB ?????? ???????????? index ??????
                response_df = response_df['disk_status']
                result_df = response_df
                # subject column ??????
                result_df.insert(0, 'subject', subject)
                # time ???????????? ???????????? ??????
                result_df=result_df.rename_axis('time').reset_index()
                result_df=result_df.groupby(['subject','host','ITEM_VALUE','ITEM_TAG'])['time'].max().reset_index()
                return (result_df)
        except:
            logger.error("Can not collect INFLUXDB")


def check_fs_usage():
    subject = 'fs_usage'
    # ?????? ?????? ??????
    if configs['CHECK_FS_USAGE']['use_yn'] == 'use':
        response_df = select_influxdb(configs['CHECK_FS_USAGE']['query'])
        try:
            if 'fs_usage' in response_df:
                response_df = response_df['fs_usage']
                result_df = response_df
                # subject column ??????
                result_df.insert(0, 'subject', subject)
                # time ???????????? ???????????? ??????
                result_df=result_df.rename_axis('time').reset_index()
                result_df=result_df.groupby(['subject','host','ITEM_VALUE','ITEM_TAG'])['time'].max().reset_index()
                # ????????? float -> percent
                result_df.loc[:,'ITEM_VALUE'] = result_df['ITEM_VALUE'].map('{:.1%}'.format)
                return (result_df)
        except:
            logger.error("Can not collect INFLUXDB")
        

def check_inode_usage():
    subject = 'inode_usage'
    # ?????? ?????? ??????
    if configs['CHECK_INODE_USAGE']['use_yn'] == 'use':
        response_df = select_influxdb(configs['CHECK_INODE_USAGE']['query'])
        try:
            if 'inode_usage' in response_df:
                # DB ?????? ???????????? index ??????
                response_df = response_df['inode_usage']
                result_df = response_df
                # subject column ??????
                result_df.insert(0, 'subject', subject)
                # time ???????????? ???????????? ??????
                result_df=result_df.rename_axis('time').reset_index()
                result_df=result_df.groupby(['subject','host','ITEM_VALUE','ITEM_TAG'])['time'].max().reset_index()
                # ????????? float -> percent
                result_df.loc[:,'ITEM_VALUE'] = result_df['ITEM_VALUE'].map('{:.1%}'.format)
                return (result_df)
        except:
            logger.error("Can not collect INFLUXDB")
        

def check_ce_cnt():
    subject = 'ce_cnt'
    # ?????? ?????? ??????
    if configs['CHECK_CE_COUNT']['use_yn'] == 'use':
        response_df = select_influxdb(configs['CHECK_CE_COUNT']['query'])
        try:
            if 'memory_ce_cnt' in response_df:
                # DB ?????? ???????????? index ??????
                response_df = response_df['memory_ce_cnt']
                result_df = response_df
                # subject column ??????
                result_df.insert(0, 'subject', subject)
                # time ???????????? ???????????? ??????
                result_df=result_df.rename_axis('time').reset_index()
                result_df=result_df.groupby(['subject','host','ITEM_VALUE'])['time'].max().reset_index()
                return (result_df)
        except:
            logger.error("Can not collect INFLUXDB")
        

def check_zombie_cnt():
    subject = 'zombie_cnt'
    # ?????? ?????? ??????
    if configs['CHECK_ZOMBIE_COUNT']['use_yn'] == 'use':
        response_df = select_influxdb(configs['CHECK_ZOMBIE_COUNT']['query'])
        try:
            if 'zombie_cnt' in response_df:
                # DB ?????? ???????????? index ??????
                response_df = response_df['zombie_cnt']
                result_df = response_df
                # subject column ??????
                result_df.insert(0, 'subject', subject)
                # time ???????????? ???????????? ??????
                result_df=result_df.rename_axis('time').reset_index()
                result_df=result_df.groupby(['subject','host','ITEM_VALUE'])['time'].max().reset_index()
                return (result_df)
        except:
            logger.error("Can not collect INFLUXDB")
        

def result_df_summary():
    server_df = check_server()
    disk_df = check_disk()
    fs_df = check_fs_usage()
    inode_df = check_inode_usage()
    ce_df = check_ce_cnt()
    zombie_df = check_zombie_cnt()
    summary_df = pd.concat([server_df, disk_df, fs_df, inode_df, ce_df, zombie_df], ignore_index=True, sort=False)
    return (summary_df)
    
result_df_summary()

### result_df ??? Alert ?????? ?????? ??????
