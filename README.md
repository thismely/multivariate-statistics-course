# Multivariate Statistical Analysis

《多元统计分析》开放式数字课程平台。以三维知识空间连接章节、方法、讲义、课件、Python 实验、案例、数据和练习，提供探索式与章节式两种学习入口。

在线课程地址将在 GitHub Pages 首次部署验证后登记。当前版本已完成本地构建与资源验收，尚未上线。仓库预定名称：`multivariate-statistics-course`。

## 课程模块

| 章节 | 内容 | 章节 | 内容 |
|---|---|---|---|
| 01 | 多元统计分析及软件概述 | 07 | 因子分析 |
| 02 | 数据处理 | 08 | 对应分析 |
| 03 | 数据可视化 | 09 | 相关与回归 |
| 04 | 聚类分析 | 10 | 典型相关分析 |
| 05 | 综合评价 | 11 | 扩展线性模型 |
| 06 | 主成分分析 | 12 | 判别分析 |

知识空间包含知识、方法、解释与案例节点，可查看先修关系、生成学习路径、比较方法并进入完整课程资源。无需登录；不采集学习行为或提交成绩。

## Python Labs

PCA、因子分析、聚类、判别、回归、Logistic 回归、CCA、对应分析和综合评价提供独立教学实验。新编实验使用明确标记的模拟数据，不代表原课程案例的历史实证结果。原课程 Notebook 单独保存为阅读参考，输出与个人元数据已移除，其历史依赖和全部数据尚未完成适配。

实验入口：网站的 Python 实验与案例库；运行环境和方法说明见 [course](course/) 和 [requirements.txt](requirements.txt)。

## Course Resources

- [课件](course/slides/)：PPTX 下载与文本预览，完整公式与图片以课件为准。
- [讲义](course/notes/)：12章完整讲义。
- [Notebook](course/notebooks/)：原课程阅读参考及可重跑实验。
- [练习](course/exercises/)：新编形成性练习及评价标准，不包含考试信息。
- 资源目录由 `src/data/course-resources.json` 统一管理，知识图谱来源定位与原课程案例保留独立的证据状态。

## 本地运行

需要 Node.js 20.19+（建议22）和 Python 3.10+。

```bash
npm install
npm run prepare:course
npm run dev
```

```bash
npm test
npm run build
npm run preview
```

`npm run build` 自动生成安全预览和静态资源，检查图谱关系、资源文件和隐私后再构建。Notebook 预览仅转换源码，构建不执行历史课程代码。Python 实验单独按说明运行。

## 维护与发布

Vue 3 / Vite / Three.js / Pinia；JSON 资源映射；hash 路由与相对资源路径兼容 GitHub Pages 项目子目录。`.github/workflows/pages.yml` 负责测试、构建和部署。

- [部署说明](docs/DEPLOYMENT.md)
- [隐私与资源边界](docs/PRIVACY.md)
- [资源审计](docs/course-resource-audit.md)
- [项目建设报告](docs/BUILD_REPORT.md)

课程材料的使用范围由课程提供者确认；第三方作品保留原权利，公开访问不自动授予再分发或商业使用许可。项目未代替权利人对原教材重新授权。详见 [LICENSE](LICENSE)。原始教材、源课件和教学管理材料不因本项目整理而被修改。
