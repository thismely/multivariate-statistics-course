# PCA 案例：把相关指标压缩为两个方向

本案例模拟一个包含五个不同量纲指标的观测矩阵。目标是理解标准化如何消除量纲影响，使用 PCA 的特征方向得到二维表示，并读取贡献率和载荷。

## 数据

- 样本：180 个匿名合成观测，固定种子 `6101`。
- 数据：[`course/data/pca_data.csv`](../data/pca_data.csv)。
- 字段：[`course/data/pca_fields.csv`](../data/pca_fields.csv)。
- 数据来源声明：由 `course/code/pca.py` 生成，不含学生、教师或管理信息。

## 方法与运行

脚本先用 `StandardScaler` 标准化五个指标，再拟合 `PCA(n_components=2)`，输出得分、载荷和解释方差。运行：

```bash
python3 course/code/pca.py --output-dir course/results
```

## 验证

查看 `course/results/pca_results.json`：`variance_ratio_positive` 和 `components_orthogonal` 应为 `true`；两个主成分累计贡献率应大于单个主成分贡献率。载荷的整体正负号可以同时翻转，比较时关注相对大小和绝对值。

本轮实际运行记录为 PC1 `0.5350`、PC2 `0.4300`，前两项累计贡献率 `0.9650`；两个结构性检查均为 `true`。

## 解释边界

贡献率是总方差的描述性分解。主成分方向不是因果机制，也不自动代表某个潜在构念；命名需要结合变量含义和课程语境。
