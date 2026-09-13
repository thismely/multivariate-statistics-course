# 实验运行说明

实验假定 Python 3.10 或更高版本。依赖只有 NumPy、Pandas、SciPy 和 scikit-learn，所有实验均在本地生成数据，不需要网络、账号或外部服务。

从 `multivariate-statistics-course/` 项目根目录运行：

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -p 'test_labs.py' -v
python3 scripts/build-labs.py
```

单个实验的统一形式为：

```bash
python3 course/code/<lab_id>.py --output-dir course/results
```

`<lab_id>` 取 `pca`、`fa`、`cluster`、`discriminant`、`regression`、`logistic`、`cca`、`ca` 或 `evaluation`。每次运行会生成本实验的合成数据、模型派生表和 `_results.json`。结果 JSON 保存固定种子、预处理、模型指标和可验证断言；案例页中的“验证”命令使用这些结果文件。

需要在不改变项目结果的情况下试跑时，使用临时输出目录：

```bash
python3 course/code/logistic.py --output-dir /tmp/mvs-logistic-lab
```

Jupyter Notebook 只包含教学说明和可重跑代码单元，输出数组保持为空。Notebook 中不写入学生标识、邮箱、路径或其他身份信息。
