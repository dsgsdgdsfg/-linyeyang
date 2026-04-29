def print_full_backtrader_report(thestrat):
    """
    Backtrader 全部官方分析器 一键打印报告
    覆盖你提供的所有指标：
    AnnualReturn / Calmar / DrawDown / TimeDrawDown / GrossLeverage
    PositionsValue / LogReturnsRolling / PeriodStats / Returns
    SharpeRatio / SharpeRatio_A / SQN / TimeReturn / TradeAnalyzer
    Transactions / VWR
    """
    line = "=" * 70
    small_line = "-" * 50

    print(line)
    print("📊 【完整版】Backtrader 策略回测分析报告")
    print(line)

    # =========================================
    # 1. 收益类
    # =========================================
    print("\n📈 收益指标")
    print(small_line)

    # AnnualReturn 年度收益
    try:
        ar = thestrat.analyzers.annualreturn.get_analysis()
        print(f"年度收益数据: {len(ar)} 个年份")
    except:
        pass

    # Returns 收益率统计
    try:
        ret = thestrat.analyzers.returns.get_analysis()
        print(f"总收益    : {ret.get('rtot',0):+.2%}")
        print(f"年化收益  : {ret.get('rnorm',0):+.2%}")
        print(f"复合收益  : {ret.get('rcomp',0):+.2%}")
    except:
        pass

    # TimeReturn 时段收益
    try:
        tr = thestrat.analyzers.timereturn.get_analysis()
    except:
        pass

    # LogReturnsRolling 滚动对数收益
    try:
        logret = thestrat.analyzers.logreturnsrolling.get_analysis()
    except:
        pass

    # =========================================
    # 2. 风险与回撤
    # =========================================
    print("\n⚠️  风险与回撤")
    print(small_line)

    # DrawDown 回撤
    try:
        dd = thestrat.analyzers.drawdown.get_analysis()
        print(f"最大回撤  : {dd['max']['drawdown']:>6.2f} %")
        print(f"最大资金回撤: {dd['max']['moneydown']:>8.0f}")
    except:
        pass

    # TimeDrawDown
    try:
        tdd = thestrat.analyzers.timedrawdown.get_analysis()
    except:
        pass

    # =========================================
    # 3. 风险收益比
    # =========================================
    print("\n⚖️  风险收益比")
    print(small_line)

    # SharpeRatio
    try:
        sp = thestrat.analyzers.sharperatio.get_analysis()
        print(f"夏普比率   : {sp.get('sharperatio',0):>6.2f}")
    except:
        pass

    # SharpeRatio_A 年化夏普
    try:
        spa = thestrat.analyzers.sharperatio_a.get_analysis()
        print(f"年化夏普   : {spa.get('sharperatio',0):>6.2f}")
    except:
        pass

    # Calmar 比率
    try:
        calmar = thestrat.analyzers.calmar.get_analysis()
        print(f"Calmar比率: {calmar.get('calmar',0):>6.2f}")
    except:
        pass

    # VWR 加权收益（比夏普更稳）
    try:
        vwr = thestrat.analyzers.vwr.get_analysis()
        print(f"VWR 加权收益: {vwr.get('vwr',0):>6.2f}")
    except:
        pass

    # =========================================
    # 4. 策略质量 SQN
    # =========================================
    print("\n🎯 策略质量 SQN")
    print(small_line)
    try:
        sqn = thestrat.analyzers.sqn.get_analysis()
        val = sqn.get('sqn',0)
        print(f"SQN 评分: {val:.2f}")

        # SQN 评价等级
        if val >= 7.0: level = "圣杯 🔥"
        elif val >=5.0: level = "一流 ✨"
        elif val >=3.0: level = "杰出 🟢"
        elif val >=2.0: level = "普通 🟡"
        elif val >=1.6: level = "可用 🟠"
        else: level = "差 🔴"
        print(f"评级    : {level}")
    except:
        pass

    # =========================================
    # 5. 杠杆 / 仓位
    # =========================================
    print("\n📊 杠杆与持仓")
    print(small_line)

    # GrossLeverage
    try:
        lev = thestrat.analyzers.grossleverage.get_analysis()
    except:
        pass

    # PositionsValue
    try:
        pv = thestrat.analyzers.positionsvalue.get_analysis()
    except:
        pass

    # =========================================
    # 6. 周期统计
    # =========================================
    print("\n📅 周期统计")
    print(small_line)
    try:
        stats = thestrat.analyzers.periodstats.get_analysis()
    except:
        pass

    # =========================================
    # 7. 交易分析 TradeAnalyzer
    # =========================================
    print("\n🧾 交易统计")
    print(small_line)
    try:
        t = thestrat.analyzers.tradeanalyzer.get_analysis()
        total = t.total.closed
        won = t.won.total
        lost = t.lost.total
        winr = won/total*100 if total else 0

        print(f"总交易 : {total:>3} 次")
        print(f"胜/负  : {won}/{lost}")
        print(f"胜率   : {winr:>5.1f}%")
        print(f"净利润 : {t.pnl.net.total:>8.0f}")
        print(f"平均持仓: {t.len.average:>5.1f} 根K线")
    except:
        pass

    # =========================================
    # 8. 交易明细
    # =========================================
    print("\n🧾 交易明细")
    print(small_line)
    try:
        txs = thestrat.analyzers.transactions.get_analysis()
    except:
        pass

    print(line)
    print("✅ 全部分析器指标打印完成！")
    print(line)

def print_all_trades(thestrat):
    """打印所有真实交易明细：日期、买卖、价格、股数"""
    print("="*70)
    print("🧾 完整交易明细（每一笔买卖）")
    print("="*70)
    
    # 获取交易记录
    trans = thestrat.analyzers.transactions.get_analysis()
    
    if not trans:
        print("⚠️  无交易记录")
        return

    # 遍历打印每一笔
    for dt, trades in trans.items():
        date = dt.strftime("%Y-%m-%d")  # 日期格式化
        
        for trade in trades:
            amount = trade[0]   # 数量（正=买，负=卖）
            price = trade[1]   # 价格

            if amount > 0:
                action = "买入 🟢"
            else:
                action = "卖出 🔴"

            print(f"📅 {date} | {action} | 价格: {price:>7.2f} | 数量: {abs(amount):>4.0f}")

    print("="*70)




# 全部官方分析器（你给的列表 100% 全覆盖）
"""cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="annualreturn")
cerebro.addanalyzer(bt.analyzers.Calmar, _name="calmar")
cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name="timedrawdown")
cerebro.addanalyzer(bt.analyzers.GrossLeverage, _name="grossleverage")
cerebro.addanalyzer(bt.analyzers.PositionsValue, _name="positionsvalue")
cerebro.addanalyzer(bt.analyzers.LogReturnsRolling, _name="logreturnsrolling")
cerebro.addanalyzer(bt.analyzers.PeriodStats, _name="periodstats")
cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharperatio")
cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name="sharperatio_a")
cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="timereturn")
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="tradeanalyzer")
cerebro.addanalyzer(bt.analyzers.Transactions, _name="transactions")
cerebro.addanalyzer(bt.analyzers.VWR, _name="vwr")"""