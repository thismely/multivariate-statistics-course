# Logistic 案例：二分类概率与优势比

本案例在固定种子生成的二分类数据上拟合 Logistic 回归，学习把线性预测转换为概率，使用 ROC-AUC、对数损失和混淆矩阵评价测试集表现。

## 数据

- 样本：260 个匿名合成观测，固定种子 `6601`。
- 数据：[`course/data/logistic_data.csv`](../data/logistic_data.csv)。
- 字段：[`course/data/logistic_fields.csv`](../data/logistic_fields.csv)。
- `synthetic_class` 是生成器标签，不含学生记录、学号或联系方式。

## 方法与运行

脚本按类别分层留出 25% 测试集，并将 `StandardScaler` 和 Logistic 回归放进同一 Pipeline：

```bash
python3 course/code/logistic.py --output-dir course/results
```

## 验证

查看 `course/results/logistic_results.json`：`no_row_overlap` 和 `probability_in_unit_interval` 应为 `true`；测试集包含 accuracy、ROC-AUC、log loss 和 2×2 混淆矩阵。优势比按标准化预测变量解释，不是原始单位的一单位变化。

本轮测试集 accuracy 为 `0.8923`，ROC-AUC 为 `0.9488`，log loss 为 `0.2770`；混淆矩阵为 `[[33, 4], [3, 25]]`。

## 解释边界

分类阈值影响混淆矩阵，类别不平衡时不能只看 accuracy。合成数据上的 ROC-AUC 不表示真实人群风险，真实应用应进行校准、交叉验证和伦理审查。
