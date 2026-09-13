# 《多元统计分析》离线 Python 实验

这里收录与三维知识空间配套的九个可离线运行实验。每个实验都有 Python 脚本、无输出身份信息的 Jupyter Notebook、字段说明 CSV 和案例 Markdown。数据由脚本中的固定种子生成，仅用于教学演示，不读取课程资料库、学生作品或任何个人信息。

## 快速运行

在项目根目录执行：

```bash
python3 -m pip install -r requirements.txt
python3 course/code/pca.py --output-dir course/results
python3 course/code/fa.py --output-dir course/results
python3 course/code/cluster.py --output-dir course/results
python3 course/code/discriminant.py --output-dir course/results
python3 course/code/regression.py --output-dir course/results
python3 course/code/logistic.py --output-dir course/results
python3 course/code/cca.py --output-dir course/results
python3 course/code/ca.py --output-dir course/results
python3 course/code/evaluation.py --output-dir course/results
```

脚本会生成带有 `_data.csv`、`_scores.csv` 或 `_predictions.csv` 后缀的教学输出，以及可机器检查的 `_results.json`。运行时可把 `--output-dir` 指向临时目录，避免覆盖已有结果。

实验索引和三维知识节点映射见 [`labs.json`](labs.json)。静态实验预览由 `python3 scripts/build-labs.py` 生成到 [`course/preview/`](preview/)。

## 实验与方法边界

| 实验 | 方法重点 | 防泄漏或解释边界 |
| --- | --- | --- |
| PCA | 标准化、特征分解、贡献率、载荷 | PCA 是总方差的线性降维，不是因果模型 |
| FA | 共同因子、共同度、特殊方差、Varimax | FA 建模共同方差，与 PCA 的目标不同 |
| Cluster | K-means、Ward、轮廓系数 | 合成标签只用于验证生成机制，不代表真实类别 |
| Discriminant | LDA、QDA、混淆矩阵 | 标准化器放在 Pipeline 内，只用训练行拟合 |
| Regression | OLS、测试集 R²、RMSE、MAE | 测试集只用于最后评价，不据此宣称因果 |
| Logistic | 概率、ROC-AUC、优势比 | 分层切分；标准化器只在训练集拟合 |
| CCA | 两个变量块、典型变量、典型相关 | X/Y 各自用训练集拟合标准化器，CCA 不读取测试分布 |
| CA | 列联表、行列质量、SVD、惯量 | CA 解释类别关联的几何结构，不等同于因果关系 |
| Evaluation | 指标方向、熵权、TOPSIS | 正向/逆向方向先声明；权重是方法设定，不是客观真理 |

各案例文件列出学习目标、数据字段、运行命令和验证检查。结果中的数值随依赖版本的浮点实现可能有极小差异，应优先检查结果 JSON 中的结构性断言。
