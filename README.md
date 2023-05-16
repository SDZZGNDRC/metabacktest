# Metabacktest
This project will generate various test for testing the back-test frameworks, such as `pybacktest` and `cbacktest`.  
**NOTICE: Currently only supports for SPOT.**  
# RUN
> python main.py  
# Process
## Step 1
1. 确定交易涉及到的交易对
2. 确定策略balance中各个交易对的余额(注意, 交易中不涉及到的交易对也可能会有余额)
3. 确定回测的时间区间[start, end], 时间粒度暂定为1 sec
4. 确定在回测期间策略生成的指令(BUY/SELL, 撤单). 注意, 必须考虑到策略可能会生成'不正确'的指令, 比如在余额不足的情况下发出BUY指令; 指令中和价格相关的参数暂时空缺, 后续步骤补上, 包括但不限于: 限价, 交易量
5. 生成策略发出的指令中涉及到的所有交易对的价格序列
6. 根据`2`和`4`补充交易指令中的相关参数, 如限价, 交易量等
7. 由`2`, `4`和`6`计算策略在回测过程中每一时间单元的balance
8. 根据`2`,`4`和`7`生成订单簿
## Step 2
1. 将`Step 1`中生成的各种数据归类, 存储到指定文件中
# 假设/前提
