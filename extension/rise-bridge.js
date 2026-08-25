function sendToken() {
  const token = localStorage.getItem("rise_access_token");
  if (!token) return;
  chrome.runtime.sendMessage({
    type: "RISE_TOKEN",
    token,
    origin: window.location.origin,
  }).catch(() => undefined);
}

sendToken();
window.setInterval(sendToken, 5000);
window.addEventListener("storage", (event) => {
  if (event.key === "rise_access_token") sendToken();
});