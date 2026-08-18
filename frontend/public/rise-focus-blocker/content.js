window.addEventListener('message', event => {
  if (event.source !== window || event.data?.type !== 'RISE_FOCUS_STATE') return
  browser.runtime.sendMessage({
    type: 'RISE_FOCUS_STATE',
    active: event.data.active === true,
    sites: Array.isArray(event.data.sites) ? event.data.sites : []
  })
})

window.postMessage({ source: 'rise-extension', type: 'RISE_EXTENSION_READY' }, '*')
