# 聚类案例：比较 K-means 与 Ward 分群

本案例把四维合成观测划分为三组，比较基于质心的 K-means 与 Ward 层次聚类。轮廓系数用于描述簇内紧密度和簇间分离度，调整 Rand 指数只用于对照已知的模拟生成标签。

## 数据

- 样本：180 个匿名合成观测，固定种子 `6301`。
- 数据：[`course/data/cluster_data.csv`](../data/cluster_data.csv)。
- 字段：[`course/data/cluster_fields.csv`](../data/cluster_fields.csv)。
- `synthetic_group` 是生成器标签，只为验证算法恢复模拟结构，不是现实主体类别。

## 方法与运行

脚本先标准化四个特征，再运行 `KMeans(n_clusters=3, n_init=20)` 和 `AgglomerativeClustering(linkage='ward')`：

```bash
python3 course/code/cluster.py --output-dir course/results
```

## 验证

查看 `course/results/cluster_results.json`：`three_nonempty_kmeans_clusters` 和 `silhouette_in_valid_range` 应为 `true`。报告中的惯性、轮廓系数和调整 Rand 指数可以比较两个方法，但不应把模拟标签当成真实分类标准。

本轮 K-means 和 Ward 都得到每簇 60 个观测；K-means 轮廓系数为 `0.6669`，相对合成标签的调整 Rand 指数为 `1.0000`。这些数值只说明本次模拟结构易于恢复。

## 解释边界

簇数、距离和尺度选择会影响结果。聚类是探索性分群，形成的簇需要用外部变量、稳定性或领域知识进一步验证。
