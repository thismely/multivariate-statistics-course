# FA 案例：从六个观测指标识别公共因子

本案例用六个观测变量模拟两个潜在公共因子。学生需要区分 FA 与 PCA：FA 将观测方差分为公共方差和特殊方差，PCA 则寻找解释总方差的线性组合。

## 数据

- 样本：220 个匿名合成观测，固定种子 `6201`。
- 数据：[`course/data/fa_data.csv`](../data/fa_data.csv)。
- 字段：[`course/data/fa_fields.csv`](../data/fa_fields.csv)。
- 数据来源声明：由 `course/code/fa.py` 生成，不从学生数据复制。

## 方法与运行

脚本先标准化，再用 `sklearn.decomposition.FactorAnalysis` 提取两个因子并做 Varimax 正交旋转，报告载荷、共同度和特殊方差：

```bash
python3 course/code/fa.py --output-dir course/results
```

## 验证

查看 `course/results/fa_results.json`：`scores_finite` 应为 `true`，每个变量同时有公共度和特殊方差。载荷的因子顺序、正负号会因旋转约定改变，解释时应以载荷模式而不是因子编号为准。

本轮实际运行的六个共同度依次约为 `0.827、0.846、0.773、0.837、0.833、0.777`，`communalities_in_unit_interval` 与 `scores_finite` 均为 `true`。

## 解释边界

固定种子只保证本案例可重跑，不证明真实问卷存在两个因子。共同度不是因果贡献，因子数和旋转方式应结合理论、拟合诊断与领域解释。
