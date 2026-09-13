# 综合评价案例：指标方向、熵权与 TOPSIS

本案例对 12 个匿名合成单位的六项指标进行综合评价，重点练习先声明指标方向，再标准化、赋权和排序。

## 数据

- 样本：12 个匿名合成单位，固定种子 `6901`。
- 数据：[`course/data/evaluation_data.csv`](../data/evaluation_data.csv)。
- 字段：[`course/data/evaluation_fields.csv`](../data/evaluation_fields.csv)。
- 方向：`income`、`employment`、`innovation`、`service` 为正向；`pollution`、`debt` 为逆向。

## 方法与运行

脚本先按方向做极差标准化，随后按列计算熵和差异系数，得到熵权；再计算每个单位到正、负理想解的距离和 TOPSIS 贴近度：

```bash
python3 course/code/evaluation.py --output-dir course/results
```

## 验证

查看 `course/results/evaluation_results.json`：`weight_sum_one`、`scores_in_unit_interval` 和 `all_ranks_present` 应为 `true`。同时核对 `directions` 与 `weights`，不要在逆向指标未转换时直接排序。

本轮熵权约为 `income 0.1716`、`employment 0.1689`、`innovation 0.1458`、`pollution 0.2193`、`debt 0.0851`、`service 0.2092`；TOPSIS 前三名为 `region_05`、`region_03`、`region_12`，三个结构性检查均为 `true`。

## 解释边界

熵权依赖样本离散程度，TOPSIS 排名依赖方向、标准化和权重。权重不是自然真理，应结合等权、主观权重或敏感性分析报告稳健性；排名也不代表因果效果。
