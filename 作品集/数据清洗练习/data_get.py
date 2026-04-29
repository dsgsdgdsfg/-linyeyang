import baostock as bs
import pandas as pd
import os #导入系统文件模块
from datetime import datetime #时间比对、日期格式转换

# ===================== 全局格式化：关闭科学计数，保留2位小数 =====================
pd.set_option('display.float_format', '{:.2f}'.format)

# ===================== 可配置参数 =====================
CONFIG = {
    "code": "sh.000001",
    "start_date": "2024-01-01",
    "end_date": "2026-01-10",
    "pct_limit_up": 0.20,
    "pct_limit_down": -0.20,
    "quantile_low": 0.01,
    "quantile_high": 0.99,
    "min_amount": 100000000,   # 最小成交额过滤 1亿
    "csv_path": "stock_clean_data.csv",#干净数据缓存路径
    "dirty_csv_path": "dirty_data.csv"#被剔除的脏数据保存路径
}

# ===================== 分位数异常过滤 =====================
def filter_quantile(series, low_q, high_q):
    lower = series.quantile(low_q)
    upper = series.quantile(high_q)
    return (series >= lower) & (series <= upper)

# ===================== 新增：因子单独函数（解耦，防未来函数） =====================
def add_factors(df_ohlc):
    df = df_ohlc.copy()
    df["pct_change"] = df["close"].pct_change()
    df['ma5'] = df['close'].rolling(5).mean()
    df["ma10"] = df["close"].rolling(10).mean()
    return df

# ===================== 新增：标记一字涨跌停 =====================
def mark_limit_up_down(df):
    df["limit_up"] = (df["open"] == df["high"]) & (df["open"] == df["close"])
    df["limit_down"] = (df["open"] == df["low"]) & (df["open"] == df["close"])
    return df

# ===================== 新增：只保留A股交易日 =====================
def filter_trade_day(df):
    # 生成自然日
    all_day = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
    # 生成A股交易日历
    trade_cal = pd.bdate_range(start=df.index.min(), end=df.index.max(), freq='C')
    return df[df.index.isin(trade_cal)]

# ===================== 核心获取+清洗函数 =====================
def get_stock_data(code, start_date, end_date, csv_path, dirty_csv_path):
    # ========== 新增：智能缓存判断 ==========
    refresh = False #这里语法细节还不是无法理解
    if os.path.exists(csv_path):
        df_tmp = pd.read_csv(csv_path, index_col="date", parse_dates=["date"])#把 date 列设为行索引 这里语法细节还不是无法理解
        local_last = df_tmp.index.max()
        target_end = pd.to_datetime(end_date)
        if local_last < target_end:  #工业级逻辑：节省接口请求、提速、保护数据源
            print("本地数据日期不足，自动重新爬取更新...")
            refresh = True
        else:
            print("检测到本地缓存日期充足，直接读取CSV...")
            return df_tmp
        
    if refresh:    
        # 无缓存/需要更新 再联网拉取
        try:#无论中间代码报错、崩溃、中途退出，finally 里代码必执行
            lg = bs.login()
            if lg.error_code != '0':
                print("baostock 登录失败：", lg.error_msg)
                return pd.DataFrame()

            rs = bs.query_history_k_data_plus(
                code=code,
                fields="date,open,high,low,close,volume",
                start_date=start_date,
                end_date=end_date,
            )

            df_raw = rs.get_data()# baostock 查询结果转成原始 DataFrame
            df = df_raw.copy()#深拷贝原始数据
            raw_count = len(df)#统计原始行数，后面做清洗前后数据对账

            # 1. 先数值转浮点
            num_cols = ["open", "high", "low", "close", "volume"]
            for col in num_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce") #errors="coerce"：转不了数字的脏字符，强制变成 NaN 空值

            # 2. 时间处理、索引、排序
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
            df = df.sort_index() #强制按时间从小到大排序防止接口乱序，均线、时序计算必须时间有序 ,无法理解时间大小从小到大，所以接口都是从小到大吗？

            # 3. 去重交易日
            df = df[~df.index.duplicated(keep="first")]#什么是接口？

            # 保存一份待清洗副本，用于提取脏数据
            df_all = df.copy()

            # 4. 基础缺失值、有效成交量
            df = df.dropna()#dropna()：删除含 NaN 空值的行
            df = df[df["volume"] > 0]#volume>0：剔除成交量为 0 的无效停牌行

            # 5. 剔除全天停牌无波动K线
            suspend_mask = ~((df["open"] == df["high"]) &
                            (df["high"] == df["low"]) &
                            (df["low"] == df["close"])) #开盘 = 最高 = 最低 = 收盘，全天一字横盘停牌，直接剔除 语法细节不理解
            df = df[suspend_mask]

            # 6. K线高低收逻辑合法性校验
            kline_mask = (df['high'] >= df['low']) & \
                        (df['high'] >= df["close"]) & \
                        (df["low"] <= df["close"])
            df = df[kline_mask]

            # ========== 新增：过滤仅保留A股交易日 ==========
            df = filter_trade_day(df)

            # ========== 新增：计算成交额 + 低流动性过滤 ==========
            df["amount"] = df["close"] * df["volume"] #成交额 = 收盘价 × 成交量 为何不自己调用，要自己算
            df = df[df["amount"] >= CONFIG["min_amount"]] #过滤成交额过低的冷门股，实盘无流动性无法交易

            # 先保存干净OHLCV，彻底解耦因子
            df_ohlc = df.copy()
            # 定义 OHLC 干净底仓保存路径（和你的缓存文件放一起）
            ohlc_csv_path = csv_path.replace(".csv", "_ohlc_raw.csv")
            # 保存最纯净的K线（无分位数、无策略过滤、只洗过脏数据）
            df_ohlc.to_csv(ohlc_csv_path, encoding="utf-8-sig")
            print(f"已保存干净OHLC底仓：{ohlc_csv_path}")
            # =====================================================
            # ========== 先衍生因子 ==========
            df = add_factors(df)

            # 7. 过滤单日异常涨跌幅
            df = df[(df["pct_change"] >= CONFIG["pct_limit_down"]) &
                (df["pct_change"] <= CONFIG["pct_limit_up"])]

            # 8. 分位数清洗价格、成交量极端值
            valid_price = filter_quantile(df["close"], CONFIG["quantile_low"], CONFIG["quantile_high"])
            valid_vol = filter_quantile(df["volume"], CONFIG["quantile_low"], CONFIG["quantile_high"])
            df = df[valid_price & valid_vol]

            # ========== 新增：标记一字涨跌停 ==========
            df = mark_limit_up_down(df) #标记而已

            # 9. 时间缺失交易日检测
            full_date_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq="D")
            missing_days = full_date_range[~full_date_range.isin(df.index)]
            print("===== 时间缺失检测 =====")
            print("缺失交易日数量：", len(missing_days))
            if len(missing_days) > 0:
                print("缺失交易日明细：\n", missing_days)

            # 10. 只删除真正必要的NaN
            df = df.dropna(subset=["pct_change", "ma5", "ma10"])

            # 11. 固定标准列顺序（新增amount、limit_up、limit_down）
            cols_order = ["open", "high", "low", "close", "volume", "amount",
                        "pct_change", "ma5", "ma10", "limit_up", "limit_down"]
            df = df[cols_order]

            # ========== 新增：抓取并保存脏数据 ==========
            dirty_df = df_all[~df_all.index.isin(df.index)]
            dirty_df.to_csv(dirty_csv_path, encoding="utf-8-sig")
            print(f"\n脏数据已保存至：{dirty_csv_path}")

            # 12. 数据对账
            clean_count = len(df)
            print("\n===== 数据清洗对账 =====")
            print(f"原始数据行数：{raw_count}")
            print(f"清洗后行数：{clean_count}")
            print(f"剔除脏数据行数：{raw_count - clean_count}")

            # 13. 保存本地缓存CSV
            df.to_csv(csv_path, encoding="utf-8-sig")
            print(f"\n已保存本地缓存：{csv_path}")

            # 14. 基础统计巡检
            print("\n===== 清洗后数据统计 =====")
            print(df.describe())

            return df

        finally:
            bs.logout()
            print("\n已安全登出 baostock 会话")

# ===================== 主程序入口 =====================
if __name__ == "__main__":
    df_final = get_stock_data(
        code=CONFIG["code"],
        start_date=CONFIG["start_date"],
        end_date=CONFIG["end_date"],
        csv_path=CONFIG["csv_path"],
        dirty_csv_path=CONFIG["dirty_csv_path"]
    )

    print("\n===== 清洗最终数据 =====")
    print(df_final.head(10))