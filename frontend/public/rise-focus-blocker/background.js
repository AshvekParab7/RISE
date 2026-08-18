const state = { active: false, sites: [] }

const normalize = value => String(value || '').toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0]
const isBlocked = hostname => state.active && state.sites.some(site => {
  const blocked = normalize(site)
  return blocked && (hostname.includes(blocked) || blocked.includes(hostname))
})

browser.storage.local.get(['active', 'sites']).then(saved => {
  state.active = saved.active === true
  state.sites = Array.isArray(saved.sites) ? saved.sites : []
})

browser.runtime.onMessage.addListener(message => {
  if (message?.type !== 'RISE_FOCUS_STATE') return
  state.active = message.active === true
  state.sites = Array.isArray(message.sites) ? message.sites : []
  return browser.storage.local.set({ active: state.active, sites: state.sites })
})

browser.webRequest.onBeforeRequest.addListener(
  details => {
    if (!isBlocked(new URL(details.url).hostname)) return undefined
    return { redirectUrl: `${browser.runtime.getURL('blocked.html')}?site=${encodeURIComponent(new URL(details.url).hostname)}` }
  },
  { urls: ['<all_urls>'], types: ['main_frame'] },
  ['blocking']
)
