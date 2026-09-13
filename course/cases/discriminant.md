# 判别案例：LDA 与 QDA 的分类边界

本案例使用六个模拟财务比率构造三分类任务，比较线性判别分析（LDA）和二次判别分析（QDA），练习从混淆矩阵和测试集指标判断分类表现。

## 数据

- 样本：240 个匿名合成观测，固定种子 `6401`。
- 数据：[`course/data/discriminant_data.csv`](../data/discriminant_data.csv)。
- 字段：[`course/data/discriminant_fields.csv`](../data/discriminant_fields.csv)。
- `synthetic_class` 是生成器提供的教学标签，不含真实公司或学生身份。

## 方法与运行

脚本按类别分层切分 75% 训练集和 25% 测试集。每个模型都用 `Pipeline(StandardScaler(), model)`，因此标准化器只在训练行拟合：

```bash
python3 course/code/discriminant.py --output-dir course/results
```

## 验证

查看 `course/results/discriminant_results.json`：训练集 180 行、测试集 60 行，`no_row_overlap` 应为 `true`；LDA 和 QDA 各有准确率、平衡准确率与 3×3 混淆矩阵。测试指标只在留出行上计算。

本轮测试集 LDA 准确率为 `0.9833`，QDA 为 `1.0000`；两个模型的混淆矩阵和训练/测试行数均写入结果 JSON。

## 解释边界

LDA 假定类别条件协方差结构相对简单，QDA 允许类别协方差不同。模拟数据上的高准确率不等于真实业务场景可泛化，实际任务还应做交叉验证和先验检查。
