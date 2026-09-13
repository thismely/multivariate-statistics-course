import MarkdownIt from 'markdown-it'
import texmath from 'markdown-it-texmath'
import katex from 'katex'

const SAFE_EXTERNAL_PROTOCOL = /^(?:https?:|mailto:|tel:)/i
const UNSAFE_PROTOCOL = /^(?:javascript:|vbscript:|data:|file:|blob:)/i

function decodeSafely(value) {
  try {
    return decodeURIComponent(value)
  } catch {
    return value
  }
}

function stripPathDecorations(value) {
  const withoutHash = String(value ?? '').split('#', 1)[0]
  return withoutHash.split('?', 1)[0]
}

/**
 * Normalise a course-relative path without allowing `..` to escape its root.
 * Returning an empty string lets callers reject malformed or unsafe paths.
 */
export function resolveCoursePath(sourcePath, href) {
  const rawHref = String(href ?? '').trim().replace(/\\/g, '/')
  if (!rawHref || rawHref.startsWith('//')) return ''

  const decodedHref = decodeSafely(stripPathDecorations(rawHref)).replace(/\\/g, '/')
  const absolute = decodedHref.startsWith('/')
  const source = decodeSafely(stripPathDecorations(sourcePath)).replace(/\\/g, '/')
  const sourceParts = source.split('/').filter(Boolean)
  const parts = absolute ? [] : sourceParts.slice(0, -1)
  const rootDepth = absolute || !sourceParts.length ? 0 : 1

  for (const segment of decodedHref.split('/')) {
    if (!segment || segment === '.') continue
    if (segment === '..') {
      if (parts.length <= rootDepth) return ''
      parts.pop()
      continue
    }
    parts.push(segment)
  }

  return parts.join('/')
}

function resourcePath(resource) {
  return resolveCoursePath('', resource?.path ?? '')
}

function resourceByPath(resources, path) {
  const target = resolveCoursePath('', path)
  if (!target) return null
  return (Array.isArray(resources) ? resources : []).find((resource) => resourcePath(resource) === target) ?? null
}

function baseAssetUrl(assetBase, path) {
  const base = String(assetBase || '/').trim() || '/'
  const cleanBase = base.endsWith('/') ? base : `${base}/`
  return `${cleanBase}${path.replace(/^\/+/, '')}`
}

function isExternalHref(value) {
  return SAFE_EXTERNAL_PROTOCOL.test(value) || /^(?:https?:)?\/\//i.test(value)
}

/**
 * Resolve links inside a Markdown resource.
 *
 * Markdown links to registered course files become hash routes so the Vue
 * router can open them. Other relative links become static asset URLs under
 * the Vite base path. Fragment-only links remain fragments and are handled by
 * CourseResource's click delegation, keeping them from changing the SPA route.
 */
export function resolveMarkdownHref(href, {
  sourcePath = '',
  resources = [],
  assetBase = '/',
} = {}) {
  const raw = String(href ?? '').trim()
  if (!raw) return '#'
  if (UNSAFE_PROTOCOL.test(raw)) return '#'
  if (raw.startsWith('#')) return raw
  if (isExternalHref(raw)) return raw

  const path = resolveCoursePath(sourcePath, raw)
  if (!path) return '#'

  const resource = /\.md$/i.test(path) ? resourceByPath(resources, path) : null
  if (resource?.id) return `#/resource/${encodeURIComponent(String(resource.id))}`
  return baseAssetUrl(assetBase, path)
}

function markdownOptions() {
  return {
    // Raw HTML is deliberately escaped because the result is mounted with
    // v-html in the public course site.
    html: false,
    breaks: false,
    linkify: false,
    typographer: false,
  }
}

function createParser() {
  const parser = new MarkdownIt(markdownOptions())
  parser.use(texmath, {
    engine: katex,
    delimiters: ['dollars', 'brackets', 'beg_end'],
    katexOptions: {
      throwOnError: false,
      strict: false,
      output: 'htmlAndMathml',
    },
  })

  const defaultImage = parser.renderer.rules.image ?? ((tokens, index, options, env, self) => self.renderToken(tokens, index, options))
  parser.renderer.rules.link_open = (tokens, index, options, env, self) => {
    const token = tokens[index]
    const href = token.attrGet('href')
    const resolved = resolveMarkdownHref(href, env)
    token.attrSet('href', resolved)
    if (resolved.startsWith('#') && !resolved.startsWith('#/')) token.attrSet('data-markdown-anchor', 'true')
    if (/^https?:/i.test(resolved) || /^(?:https?:)?\/\//i.test(resolved)) {
      token.attrSet('target', '_blank')
      token.attrSet('rel', 'noopener noreferrer')
    }
    return self.renderToken(tokens, index, options)
  }
  parser.renderer.rules.image = (tokens, index, options, env, self) => {
    const token = tokens[index]
    const src = token.attrGet('src')
    token.attrSet('src', resolveMarkdownHref(src, env))
    return defaultImage(tokens, index, options, env, self)
  }
  return parser
}

const parser = createParser()

export function renderMarkdown(source, options = {}) {
  const env = {
    sourcePath: options.sourcePath ?? '',
    resources: options.resources ?? [],
    assetBase: options.assetBase ?? '/',
  }
  return parser.render(String(source ?? ''), env)
}

export { MarkdownIt }
