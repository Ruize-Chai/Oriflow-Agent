import axios from 'axios'

const BASE = (import.meta.env && import.meta.env.VITE_API_BASE) || 'http://127.0.0.1:8000'
const client = axios.create({ baseURL: BASE, headers: { 'Content-Type': 'application/json' }})

// Types (mirror backend Schema/payload)
export interface WorkflowNode {
  id: number
  type: string
  listen?: number[]
  outputs?: Array<number | null>
  inputs?: number[]
  context?: Record<string, any>
  params?: Record<string, any>
}

export interface WorkflowPayload {
  workflow_id: string
  entry: number
  nodes: WorkflowNode[]
}

export interface NodeState {
  node_id: number
  state: string
}

export interface NodeStateListPayload {
  workflow_id: string
  states: NodeState[]
}

export interface ChatboxOutputPayload {
  node_id: number
  message: string
  meta?: any
}

// API methods
export const getPlugins = async () => {
  return client.get('/plugins/')
}

export const getWorkflowList = async () => {
  return client.get('/workflow/list')
}

export const getWorkflow = async (workflow_id: string) => {
  return client.get(`/workflow/${workflow_id}`)
}

export const createWorkflow = async (payload: Partial<WorkflowPayload>) => {
  return client.post('/workflow/create', payload)
}

export const alterWorkflow = async (payload: Partial<WorkflowPayload>) => {
  return client.post('/workflow/alter', payload)
}

export const deleteWorkflow = async (payload: { workflow_id: string }) => {
  return client.post('/workflow/delete', payload)
}

export const postInterrupt = async () => {
  return client.post('/runtime/interrupt')
}

export const postTextInput = async (workflow_id: string, node_id: number, value: string) => {
  return client.post(`/runtime/${workflow_id}/input/text`, { node_id, value })
}

export const postNumberInput = async (workflow_id: string, node_id: number, value: number) => {
  return client.post(`/runtime/${workflow_id}/input/number`, { node_id, value })
}

export const getCheckboxOptions = async (workflow_id: string, node_id: number) => {
  return client.get(`/runtime/${workflow_id}/checkbox/${node_id}`)
}

export const postCheckboxSelection = async (workflow_id: string, node_id: number, selection: number[]) => {
  return client.post(`/runtime/${workflow_id}/checkbox/${node_id}`, { selection })
}

export const getChatboxOutput = async (workflow_id: string, node_id: number) => {
  return client.get<ChatboxOutputPayload>(`/runtime/${workflow_id}/chatbox/${node_id}`)
}

export const getFilebaseList = async () => {
  return client.get('/filebase/list')
}

// Run workflow: POST /runtime/run returns text/event-stream. Implement fetch+readable stream parser and yield parsed JSON events.
export async function* runWorkflowEvents(workflow_id: string) {
  const res = await fetch(`${BASE}/runtime/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workflow_id }),
  })

  if (!res.body) return

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    let idx = buf.indexOf('\n\n')
    while (idx !== -1) {
      const chunk = buf.slice(0, idx).trim()
      buf = buf.slice(idx + 2)
      // Each chunk may contain lines like: data: {...}
      const lines = chunk.split(/\n/)
      for (const line of lines) {
        const m = line.match(/^data:\s*(.*)$/)
        if (m) {
          try {
            const parsed = JSON.parse(m[1]) as NodeStateListPayload
            yield parsed
          } catch (e) {
            // ignore parse errors
          }
        }
      }
      idx = buf.indexOf('\n\n')
    }
  }
}

export default {
  getPlugins,
  getWorkflowList,
  getWorkflow,
  createWorkflow,
  alterWorkflow,
  deleteWorkflow,
  runWorkflowEvents,
  postTextInput,
  postNumberInput,
  getCheckboxOptions,
  postCheckboxSelection,
  getChatboxOutput,
  postInterrupt,
  getFilebaseList,
}
