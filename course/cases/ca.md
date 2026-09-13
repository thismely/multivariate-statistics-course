# CA 案例：列联表的 SVD 几何表示

本案例用六个匿名行类别和五个匿名列类别生成列联表。通过行轮廓、列轮廓、质量和惯量，把类别关联表示在二维空间中。

## 数据

- 表格：6×5 的固定种子合成频数表，种子 `6801`。
- 数据：[`course/data/ca_table.csv`](../data/ca_table.csv)。
- 字段：[`course/data/ca_fields.csv`](../data/ca_fields.csv)。
- `region_1` 等名称是合成类别名，不对应真实地区或个人。

## 方法与运行

脚本计算独立性期望，构造质量加权标准化残差矩阵，再调用 `numpy.linalg.svd` 得到奇异值、行坐标、列坐标和惯量：

```bash
python3 course/code/ca.py --output-dir course/results
```

## 验证

查看 `course/results/ca_results.json`：`row_masses_sum_to_one`、`column_masses_sum_to_one`、`inertia_ratio_sum_to_one` 应为 `true`；同时检查二维行、列坐标文件。行列类别接近只表示在该列联表中的关联结构。

本轮 SVD 的前两个奇异值为 `0.6424、0.2807`，前两维惯量比例为 `0.7838、0.1497`；三个质量/惯量和检查均为 `true`。

## 解释边界

CA 的惯量和坐标来自频数与独立性基准。低频类别可能有不稳定坐标，二维图也会丢失高维信息；该几何关联不等同于因果或总体推断。
