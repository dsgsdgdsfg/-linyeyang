# savefig.py
from backtrader import plot
import matplotlib.pyplot as plt
import os

# 自动创建文件夹 + 保存图片（全部封装好了！）
def saveplots(
    cerebro, #回测核心对象（必须传）
    filename="savefig.png", #图片名（默认 savefig.png）
    save_dir="回测图片", #保存文件夹（默认 回测图片）
    numfigs=1, #显示一副图，k线过多时候可以写更多
    iplot=False, #关闭 Jupyter 模式，Windows 必用
    dpi=300,#高清
    **kwargs#接收额外参数（如 volume=False）
):
    # 自动创建文件夹
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # 完整路径
    file_path = os.path.join(save_dir, filename)

    # 绘图
    if cerebro.p.oldsync:
        plotter = plot.Plot_OldSync(**kwargs)
    else:
        plotter = plot.Plot(**kwargs)

    figs = []
    for stratlist in cerebro.runstrats:
        for si, strat in enumerate(stratlist):
            rfig = plotter.plot(
                strat, 
                figid=si*100, 
                numfigs=numfigs, 
                iplot=iplot,
                volume=False,** kwargs
            )
            figs.append(rfig)

    # 保存
    for fig in figs:
        for f in fig:
            f.savefig(file_path, bbox_inches='tight', dpi=dpi)
    
    print(f"✅ 图片已保存到：{file_path}")
    return file_path