# CCA 案例：连接两组变量

本案例构造四维输入变量组 X 和三维结果变量组 Y，学习典型变量、典型相关以及训练和测试相关的区别。

## 数据

- 样本：240 个匿名合成观测，固定种子 `6701`。
- 数据：[`course/data/cca_data.csv`](../data/cca_data.csv)。
- 字段：[`course/data/cca_fields.csv`](../data/cca_fields.csv)。
- 数据由两个潜在合成因子生成，不含现实主体信息。

## 方法与运行

脚本先按行切分训练集和测试集，为 X、Y 两个变量块分别拟合训练集 `StandardScaler`，再以 `CCA(scale=False)` 估计两个典型维度：

```bash
python3 course/code/cca.py --output-dir course/results
```

## 验证

查看 `course/results/cca_results.json`：应同时有第一、第二典型相关的训练集和测试集绝对值，`no_row_overlap` 与 `test_correlations_in_unit_interval` 应为 `true`。典型变量正负号可同时翻转，比较时使用绝对相关或明确记录符号约定。

本轮训练集两个绝对典型相关为 `0.9409、0.8522`，测试集为 `0.9395、0.8477`；两个独立标准化器和 `CCA(scale=False)` 的设定记录在结果 JSON 中。

## 解释边界

CCA 描述两组变量的线性关联，不证明某组变量导致另一组变量。典型相关的显著性、冗余度和稳定性需要更完整样本及推断设计；本实验只验证算法流程。
