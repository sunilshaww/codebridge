// CodeBridge from Bunchhh — background.js

chrome.runtime.onMessage.addListener(async (msg, sender) => {

  // Popup asks content script to inject workspace context
  if (msg.type === 'CB_REQUEST_ATTACH') {
    const tabs = await chrome.tabs.query({active: true, currentWindow: true});
    if (tabs[0]) {
      chrome.tabs.sendMessage(tabs[0].id, {
        type:    'CB_INJECT',
        context: msg.context || '',
      });
    }
  }

  // Content script asks for attach (user clicked badge button)
  if (msg.type === 'CB_REQUEST_ATTACH' && sender.tab) {
    // Forward to popup to fetch files and send back
    // Popup handles the actual file fetch
  }

  return true;
});

chrome.runtime.onInstalled.addListener(() => {
  console.log('⚡ CodeBridge from Bunchhh installed.');
});