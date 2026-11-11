const HOST = "com.cheapcoder.one_click_clone";
const DEFAULTS = { root: "~/dev", editor: "Visual Studio Code" };

function notify(message) {
	chrome.notifications.create({ type: "basic", iconUrl: "icons/icon128.png", title: "一键 Clone", message });
}

function setBadge(text, color) {
	chrome.action.setBadgeText({ text });
	chrome.action.setBadgeBackgroundColor({ color });
}

function finish(message, ok) {
	notify(message);
	setBadge(ok ? "OK" : "ERR", ok ? "#1a7f37" : "#b3261e");
	setTimeout(() => chrome.action.setBadgeText({ text: "" }), 5000);
}

// 用长连接调用本地程序：连接存续期间 service worker 不会被回收，克隆再久也能收到结果
chrome.action.onClicked.addListener(async tab => {
	const settings = await chrome.storage.local.get(DEFAULTS);
	setBadge("...", "#666666");
	const port = chrome.runtime.connectNative(HOST);
	let finished = false;
	port.onMessage.addListener(msg => {
		if (msg.type === "progress") return setBadge(`${msg.percent}%`, "#666666");
		finished = true;
		if (msg.type === "done") finish(msg.existed ? `已存在，直接打开：${msg.dir}` : `克隆完成：${msg.dir}`, true);
		else finish(`失败：${msg.error}`, false);
	});
	// 本地程序发完结果就退出，断开时必须读一次 lastError，否则 Chrome 会记一条 Unchecked runtime.lastError
	port.onDisconnect.addListener(() => {
		const error = chrome.runtime.lastError?.message;
		if (!finished) finish(`本地程序异常：${error}（未安装请运行 install.sh）`, false);
	});
	port.postMessage({ pageUrl: tab.url, ...settings });
});
