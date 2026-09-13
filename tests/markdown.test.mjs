import test from 'node:test'
import assert from 'node:assert/strict'
import { renderMarkdown, resolveCoursePath, resolveMarkdownHref } from '../src/utils/markdown.js'

const resources = [
  { id: 'notes-ch02', path: 'course/notes/ch02.md' },
  { id: 'data-pca', path: 'course/data/pca_data.csv' },
]

test('Markdown reader renders safe course prose, tables, code and math', () => {
  const html = renderMarkdown([
    '# 课程标题',
    '',
    '## 学习目标',
    '',
    '- 理解矩阵结构',
    '- 能够复核公式',
    '',
    '| 方法 | 目标 |',
    '| --- | --- |',
    '| PCA | 降维 |',
    '',
    '行内公式 $x^T x$ 与 \\(y = X\\beta\\)；',
    '',
    '$$',
    '\\hat{\\beta}=(X^TX)^{-1}X^Ty',
    '$$',
    '',
    '```python',
    'print("PCA")',
    '```',
  ].join('\n'))

  assert.match(html, /<h1>课程标题<\/h1>/)
  assert.match(html, /<ul>[\s\S]*<li>理解矩阵结构<\/li>/)
  assert.match(html, /<table>[\s\S]*<th>方法<\/th>[\s\S]*<td>PCA<\/td>/)
  assert.match(html, /class="katex"/)
  assert.match(html, /class="katex-display"/)
  assert.match(html, /<pre><code class="language-python">print\(&quot;PCA&quot;\)\n<\/code><\/pre>/)
})

test('raw HTML is escaped and unsafe links are neutralised', () => {
  const html = renderMarkdown('<script>alert(1)</script>\n\n[不安全](javascript:alert(1))')
  assert.match(html, /&lt;script&gt;alert\(1\)&lt;\/script&gt;/)
  assert.doesNotMatch(html, /<script>/i)
  assert.doesNotMatch(html, /<a\b/i)
})

test('registered Markdown files become course routes and local assets use the base path', () => {
  assert.equal(resolveCoursePath('course/cases/pca.md', '../data/pca_data.csv'), 'course/data/pca_data.csv')
  assert.equal(resolveMarkdownHref('../notes/ch02.md', { sourcePath: 'course/notes/ch01.md', resources }), '#/resource/notes-ch02')
  assert.equal(resolveMarkdownHref('../data/pca_data.csv', { sourcePath: 'course/cases/pca.md', resources, assetBase: '/multivariate-statistics-course/' }), '/multivariate-statistics-course/course/data/pca_data.csv')
  assert.equal(resolveMarkdownHref('#learning-objective', { sourcePath: 'course/notes/ch01.md', resources }), '#learning-objective')
  assert.equal(resolveMarkdownHref('javascript:alert(1)', { sourcePath: 'course/notes/ch01.md', resources }), '#')
})

test('external links open safely and fragment links carry an SPA-safe marker', () => {
  const html = renderMarkdown('[文档](https://example.com/docs)\n\n[本页](#section)')
  assert.match(html, /href="https:\/\/example\.com\/docs" target="_blank" rel="noopener noreferrer"/)
  assert.match(html, /href="#section" data-markdown-anchor="true"/)
})
