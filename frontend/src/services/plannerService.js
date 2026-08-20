const STORAGE_KEY = 'rise_ui_planner_events'

const read = () => {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') } catch { return [] }
}

const write = events => localStorage.setItem(STORAGE_KEY, JSON.stringify(events))

export const plannerService = {
  list: async () => read(),
  create: async payload => {
    const event = { ...payload, id: `planner-${Date.now()}-${Math.random().toString(36).slice(2)}` }
    write([...read(), event])
    return event
  },
  update: async (id, payload) => {
    const event = { ...payload, id }
    write(read().map(item => item.id === id ? event : item))
    return event
  },
  remove: async id => { write(read().filter(item => item.id !== id)); return null },
}
