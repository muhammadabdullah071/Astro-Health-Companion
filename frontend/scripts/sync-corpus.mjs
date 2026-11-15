// Copies the RAG corpus built by rag/ingest.py into the frontend so the Groq path works on
// Vercel, where the Python RAG module is not available. Skips silently if the source is missing
// (e.g. when only the frontend folder is uploaded) and the committed copy is used instead.
import { copyFileSync, existsSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const src = resolve(here, '../../rag/index/corpus.json')
const dst = resolve(here, '../src/data/corpus.json')
if (existsSync(src)) {
  copyFileSync(src, dst)
  console.log('[sync-corpus] copied rag/index/corpus.json -> src/data/corpus.json')
} else {
  console.log('[sync-corpus] rag/index/corpus.json not found, using committed copy')
}
