export const focusFullscreenSupported = () =>
  typeof document !== "undefined" && Boolean(document.documentElement?.requestFullscreen);

export const requestFocusFullscreen = () => {
  if (!focusFullscreenSupported() || document.fullscreenElement) return Promise.resolve(false);
  try {
    return Promise.resolve(document.documentElement.requestFullscreen()).then(() => true).catch(() => false);
  } catch {
    return Promise.resolve(false);
  }
};

export const exitFocusFullscreen = () => {
  if (typeof document === "undefined" || !document.fullscreenElement) return Promise.resolve(false);
  try {
    return Promise.resolve(document.exitFullscreen()).then(() => true).catch(() => false);
  } catch {
    return Promise.resolve(false);
  }
};
