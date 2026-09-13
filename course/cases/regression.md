# 回归案例：解释系数并检验测试集预测

本案例模拟五个连续预测变量和一个连续响应，其中前两个预测变量相关。学生练习 OLS 系数、测试集 R²、RMSE 和 MAE，并观察训练与测试的差异。

## 数据

- 样本：210 个匿名合成观测，固定种子 `6501`。
- 数据：[`course/data/regression_data.csv`](../data/regression_data.csv)。
- 字段：[`course/data/regression_fields.csv`](../data/regression_fields.csv)。
- 数据来源声明：响应由固定系数和随机噪声生成，不含现实个体记录。

## 方法与运行

脚本随机留出 25% 测试行，先只用训练行拟合 `StandardScaler`，再拟合 `LinearRegression`：

```bash
python3 course/code/regression.py --output-dir course/results
```

## 验证

查看 `course/results/regression_results.json`：`no_row_overlap` 和 `predictions_finite` 应为 `true`；同时检查 `train_metrics` 与 `test_metrics` 的 R²、RMSE、MAE。标准化系数是“预测变量增加一个训练集标准差”对应的模型变化。

本轮训练集 R² 为 `0.9471`，测试集 R² 为 `0.9420`；测试集 RMSE 为 `0.6816`、MAE 为 `0.5425`。这些是固定种子下的描述性运行结果。

## 解释边界

合成响应的生成式关系仅用于演示估计和预测流程。相关变量可能使系数不稳定；真实分析还需残差、异常值、共线性和模型设定诊断，不能把回归系数直接解释为因果效应。
