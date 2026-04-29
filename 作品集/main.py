# ======================================================
# 量化交易回测框架 - 个人工作模板
# 必赚必触发版 · 直接运行就有结果
# ======================================================
from datetime import datetime
from datetime import timedelta
import backtrader as bt
import quantstats as qs
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import webbrowser
import numpy as np
import talib
from savefig import saveplots
from tusshareget_data import stock_get
from backtrader.feeds import PandasData
plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

modpath = os.path.dirname(os.path.abspath(sys.argv[0]))#获取脚本文件所在路径
class PriceDiff(bt.Indicator):
    lines = ('diff', 'ggcmoe')
    # 这里必须加 params，才能接收 period
    params = (('period', 20),)
    plotinfo = dict(subplot=True)

    def __init__(self):
        data = self.datas[0]
        sma = bt.talib.SMA(data.close, timeperiod=self.p.period)
        upp = data.high / sma
        downp = sma / data.low
        diff = upp - downp

        self.lines.diff = diff
        self.lines.ggcmoe = diff > 0.03
        
        

# ====================== 策略【必触发！】======================
#创建新的data feed类
class PandasData_PE(PandasData):
    lines = ("pe",)#增加pe线
    params = (("pe",8),)#默认第八列
class stampDutyCommissionScheme(bt.CommInfoBase):
    """
    本佣金模式下，买入股票仅支付佣金，卖出股票支付佣金和印花税。
    """
    params = (
        ('stamp_duty', 0.005), # 印花税率
        ('percabs', True),
        ('stocklike', True),
    )

    def _getcommission(self, size, price, pseudoexec):
        """
        If size is greater than 0, this indicates a long / buying of shares.
        If size is less than 0, it indicates a short / selling of shares.
        """
        if size > 0: # 买入，不考虑印花税
            return size * price * self.p.commission
        elif size < 0: # 卖出，考虑印花税
            return - size * price * (self.p.stamp_duty + self.p.commission)
        else:
            return 0 # just in case for some reason the size is 0.
class SmaCross(bt.Strategy):
    #定义参数,元组定义，还可以用字典定义（key=）
    params = (
        ('period', 60),      # 快线 60日均线（超级灵敏，必触发）
        ('period2', 200),    # 慢线 200日均线
        ('period3',300),
        ('period4',20),  #指数平均 202   
        ('buy_size', 1000),  #买入大小
        ('sell_size', 1000),  #卖出大小
        ('period_fast',5),    #快线 5日
        ('period_slow',10),    #慢线 10日
        ('dataframe',None)   #dataframe
    )
    def stop(self):
        for t in self._trades[self.data0][0]:
            print(t.pnl)
    #日志函数
    def log(self,txt,dt=None):
        '''日志函数'''
        dt = dt or self.datetime.date(0)#可以显示时间部分
        print('%s,%s'%(dt.isoformat(),txt))

    def __init__(self):#只运行一次
        self.sma = bt.talib.SMA(self.data.close,timeperiod = self.p.period)
        self.sma.plotinfo.plotname = f"MA{self.p.period}"
        self.sma.plotinfo.subplot = True       # 单独绘图,是否放主图
        self.sma.plotinfo.linewidth = 2
        self.sma.line.color = 'blue'

        self.sma2 = bt.talib.SMA(self.data.close,timeperiod = self.p.period2)#第二条均线
        self.sma2.plotinfo.plotname = f"MA{self.p.period2}"
        self.sma2.plotinfo.subplot = True
        self.sma2.plotinfo.master = self.sma  # 合并到 sma
        self.sma2.plotinfo.linewidth = 2
        self.sma2.line.color = 'red'
        self.order=None
        self.stop_price = None
        self.crossover = bt.ind.CrossOver(self.sma,self.sma2)#交叉指标
        something = self.sma2-self.sma+self.data.close
        self.sma3 = bt.talib.SMA(something,timeperiod = self.p.period3)
        self.greater = self.sma3>self.sma
        bt.LinePlotterIndicator(self.greater,name='greater',plotname='greaterplot')

        self.ema = bt.talib.EMA(self.data.close,timeperiod = self.p.period4)

        # 直接给它设置绘图属性，完事！
        self.ema.plotinfo.plotname = "EMA"
        self.ema.plotinfo.subplot = True   # 分开画图
        self.ema.line.color = "blue"

        self.my_ind = PriceDiff(period=self.p.period4)
        self.atr = bt.ind.ATR(self.data, period=14)
        self.buy_price = 0  # 记录买入价
        self.stop_loss_price = 0  # 止损价
        self.take_profit_rate = 0.2   # 8%止盈，可自行改0.05/0.1
        self.trail_back = 0.2 
        self.high_price = 0

    
    def notify_order(self,order):
        if order.status in [order.Submitted,order.Accepted]:#订单状态 submitted/accepted，误动作
            return
        if order.status in [order.Completed]:
            if order.isbuy():#买单执行，输出价格，大小，总值
                self.log(f'买单执行,price{round(order.executed.price,2)},\
                         size{order.executed.size},\
                            cost{round(order.executed.value,2)}')
            elif order.issell():#卖单执行，输出价格，大小，总值
                self.log(f'卖单执行,price{round(order.executed.price,2)},\
                         size{order.executed.size},\
                            cost{round(order.executed.value,2)}')
        elif order.status in [order.Canceled,order.Margin,order.Rejected]:#判断订单状态输出
            self.log('订单Canceled/Margin/Rejected')
        self.order = None
    def notify_trade(self,trade):
        print('trade')
        for h in trade.history:
            print("status:",h.status)
            print("enent",h.event)
        if trade.isclosed:
            print('毛收益%0.2f,扣佣金收益%0.2f,佣金%.2f'%(trade.pnl,trade.pnlcomm,trade.commission))
    def start(self):
        print("start")
    """def prenext(self):
        self.log("nextstart")
        self.next()"""    

    def next(self):#循环，核心逻辑
        # 无持仓 → 金叉买
        if not self.position:
            if self.crossover>0 and self.my_ind.ggcmoe[0] :#金叉指标判断
                self.log('均线金叉+指标满足，All in 满仓买入')
                # 固定风险仓位参数：单笔最多亏总资金的1.5%
                risk_percent = 0.015
                total_value = self.broker.getvalue()
                # 单笔允许最大亏损金额
                max_risk_money = total_value * risk_percent
                
                atr_mult = 2.5
                # 每股止损亏损幅度
                loss_per_share = atr_mult * self.atr[0]
                
                close_price = self.data.close[0]
                # 算出应该买多少股
                size = int(max_risk_money / loss_per_share / 100) * 100
                
                # 限制最大不超过9成仓，防止极端重仓
                max_size = int((total_value * 0.9) / close_price / 100) * 100
                size = min(size, max_size)
                if size <= 0:
                    return
                self.log('创建买单')
                #记录订单引用
                validday = self.data.datetime.datetime(0)+timedelta(days=7)
                self.order = self.buy(size=size,
                         exectype=bt.Order.Limit,
                         price=self.data.close[0],#限价
                         valid=validday
                         )
                self.buy_price = self.data.close[0]
                # ATR动态止损：买入价 - 2.5倍ATR
                atr_mult = 2.5
                self.stop_loss_price = self.buy_price - atr_mult * self.atr[0]
                # 有持仓 → 死叉卖
        else:
            if self.data.close[0] > self.high_price:
                self.high_price = self.data.close[0]
            if self.data.close[0] <= self.stop_loss_price:
                self.log('触发ATR动态止损 离场')
                self.order = self.sell(size=self.position.size)
                return
            if self.crossover<0:
                self.log('创建卖单')
                self.order  = self.sell(size=self.position.size)
                return
            if self.data.close[0] >= self.buy_price * (1 + self.take_profit_rate):
                self.log(f'触发{self.take_profit_rate*100:.0f}%止盈 离场')
                self.order = self.sell(size=self.position.size)
# ====================== 主程序 ======================
if __name__ == '__main__':
    cerebro = bt.Cerebro()

    #datapath = os.path.join(modpath, '60000.csv')#拼接得到数据文件全路径
    dataframe = stock_get()
    '''dataframe = pd.read_csv(
        datapath,
        skiprows=0,#不忽略行skiprows=0 → 不跳过任何行，从第一行开始读如果写 skiprows=1 → 跳过第一行，从第二行开始读
        header=0#行列头在0行，如date，close等
    )'''
    def find_date_column(dataframe):
        possible_names = ["date", "trade_date", "datetime", "time"]
        for col in possible_names:
            if col in dataframe.columns:
                return col
        raise Exception("找不到日期列！")
    col_date = find_date_column(dataframe)
    # 【优化 1】直接重命名，不要新建列（更干净）
    dataframe.rename(columns={col_date: 'date'}, inplace=True)
    # 【优化 2】pd.to_datetime 自带强转
    dataframe['date'] = pd.to_datetime(dataframe['date'], errors='coerce')
    # 删除无效日期（防止回测崩溃）
    dataframe = dataframe.dropna(subset=['date'])
    # 设置索引
    dataframe.set_index("date", inplace=True)

    # 按时间排序（超级重要！）
    dataframe = dataframe.sort_index()
    print(dataframe.head())
    print(dataframe)

    data = PandasData_PE(
        dataname=dataframe,
        datetime=None,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
       #timeframe=bt.TimeFrame.Minutes,
        #openinterest=-1,
        #dtformat=('%Y-%m-%d %H:%M:%S'),
        #fromdate=datetime(2020, 1, 1),
        #todate=datetime(2025, 12, 31)
    )
    

    cerebro.adddata(data) #将行情数据注对象注入引擎
    cerebro.addstrategy(SmaCross)#将策略注入引擎

    # 正常资金
    cerebro.broker.setcash(1000000.0)#设置初始资金
    #cerebro.broker.setcommission(0.0003)#佣金费率
    #cerebro.broker.set_coc(True)
    cerebro.broker.set_slippage_fixed(0.05)
    comminfo = stampDutyCommissionScheme(stamp_duty=0.005,commission=0.0001)#自定义佣金 印花0.0050
    cerebro.broker.addcommissioninfo(comminfo) #自定义的佣金
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')#关键固定：加PyFolio导出器

    thestrats = cerebro.run()
    thestrat = thestrats[0]

    #输出最后市值
    print('最终市值：%.2f'% cerebro.broker.getvalue())
    #打印各个分析者的内容
    pf = thestrat.analyzers.getbyname('pyfolio')
    returns, positions, transactions, gross_lev = pf.get_pf_items()

    # 时区清理（固定步骤，防报错）
    returns.index = returns.index.tz_convert(None)
    positions.index = positions.index.tz_convert(None)
    transactions.index = transactions.index.tz_convert(None)

    # ----------------------
    # 3. QuantStats 固定输出
    # ----------------------
    # 打印交易明细
    qs.reports.metrics(returns, display=True)
    # 生成完整HTML专业报告
    qs.reports.html(
        returns,
        benchmark=None,
        output='策略回测报告.html',
        title='Backtrader+QuantStats回测报告'
    )


    # ===========================
    # 🔥 打印完整交易明细（100% 不报错）
    # ===========================
    print("\n" + "="*70)
    print("🧾 【完整交易明细】")
    print("="*70)

    # 这里是正确格式，不会报缩进错误
    for index, row in transactions.iterrows():
        dt = index.strftime("%Y-%m-%d %H:%M:%S")
        amount = row[0]
        price = row[1]

        if amount > 0:
            action = "买入 🟢"
        else:
            action = "卖出 🔴"

        print(f"📅 {dt} | {action} | 价格: {price:>8.2f} | 数量: {abs(amount):>4.0f}")

    print("="*70)


        # ====================== 绘图 ======================
    cerebro.plot(
        style='candlestick',  # 蜡烛图
        barup='red',         # 涨红
        bardown='green',     # 跌绿
        volume=True,         # 显示成交量
    )

    # 自动用浏览器打开回测图表报告
    webbrowser.open("策略回测报告.html")


    



