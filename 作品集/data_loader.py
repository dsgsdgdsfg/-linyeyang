# -*- coding: utf-8 -*-
"""
Backtrader万能模板 - 数据读取模块
功能：统一读取CSV格式股票数据，处理数据格式，供主程序调用
说明：换数据时，仅需修改CSV文件路径、列对应关系（datetime/close等）
"""
import backtrader as bt
import os

def load_stock_data(data_path, fromdate, todate):
    """
    读取CSV股票数据，返回Backtrader可识别的数据格式
    :param data_path: CSV数据文件路径（必填）
    :param fromdate: 回测开始日期（datetime格式，如：bt.datetime.datetime(2020,1,1)）
    :param todate: 回测结束日期（datetime格式）
    :return: Backtrader数据对象
    """
    # 校验数据文件是否存在
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"数据文件不存在：{data_path}，请检查路径是否正确")
    
    # 读取CSV数据（核心配置，根据自己的CSV文件列调整）
    data = bt.feeds.GenericCSVData(
        dataname=data_path,          # 数据文件路径
        datetime=0,                 # CSV文件中，日期所在的列（从0开始计数）
        open=1,                     # 开盘价所在列（不用则设为-1）
        high=2,                     # 最高价所在列（不用则设为-1）
        low=3,                      # 最低价所在列（不用则设为-1）
        close=4,                    # 收盘价所在列（核心，必须设对）
        volume=5,                   # 成交量所在列（不用则设为-1）
        openinterest=-1,            # 持仓量（A股一般没有，设为-1）
        dtformat='%Y-%m-%d',        # 日期格式（与CSV文件一致，如：2020-01-01）
        fromdate=fromdate,          # 回测开始日期
        todate=todate,              # 回测结束日期
        timeframe=bt.TimeFrame.Days # 数据周期（日线，不用改；分钟线设为bt.TimeFrame.Minutes）
    )
    return data
