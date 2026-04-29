import tushare as ts
import pandas as pd

def stock_get(ts_code='600000.SH',start_date='20000101',end_date='20200710'):
    ts.set_token("e54c02d0e4287b554d16615e8cd8980849fffae17a80e8617208eafe")

    # 初始化接口
    pro = ts.pro_api()

    # ======================
    # 获取股票数据（正确写法）
    # ======================
    df = pro.bar(
        ts_code=ts_code,
        start_date=start_date,
        end_date=end_date,
        adj='qfq',
        freq='5min'
    )

    # 按日期正序排列（旧→新）
    df = df.sort_values("trade_date", ascending=True)

    # 打印最新10条
    print("📊 股票数据：")
    print(df.tail(10))

    # 保存CSV
    df.to_csv("600000_tushare真实数据.csv", encoding="utf-8-sig", index=False)
    print("\n💾 保存成功！")
    return df