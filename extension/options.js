const DEFAULTS = { root: "~/dev", editor: "Visual Studio Code" };
const fields = Object.keys(DEFAULTS);

chrome.storage.local.get(DEFAULTS).then(settings => {
	fields.forEach(key => (document.getElementById(key).value = settings[key]));
});

document.getElementById("save").addEventListener("click", async () => {
	const settings = Object.fromEntries(fields.map(key => [key, document.getElementById(key).value.trim()]));
	if (!settings.root) return (document.getElementById("status").textContent = "根目录不能为空");
	await chrome.storage.local.set(settings);
	document.getElementById("status").textContent = "已保存";
});
