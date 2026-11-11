<p align="center"><img src="extension/icons/icon.svg" width="96" alt="logo"></p>

<h1 align="center">一键 Clone 到本地</h1>

<p align="center">在 GitHub / GitLab 仓库页点一下扩展图标 → 本机 git 克隆到预设目录 → 用编辑器打开</p>

## 原理

```
扩展图标点击
  └─ background.js：把页面 URL + 设置发给本地程序（connectNative 长连接）
       └─ host/one_click_clone.py（本机 python）
            ├─ 解析 URL → 仓库地址 + 分支
            ├─ 目录已存在：同一仓库 → 直接打开；不同仓库 → 报错
            ├─ git clone --progress → 进度回传到图标角标
            └─ open -a <编辑器> <目录>
```

- 用本机 git：复用钥匙串 / SSH 凭证，私有库无需另配 Token
- 仅支持 macOS + Google Chrome

## 安装

1. 克隆本仓库，在仓库根目录运行 `./install.sh` 注册本地程序
2. Chrome → `chrome://extensions` → 开启「开发者模式」→「加载已解压的扩展程序」→ 选 `extension` 目录
3. 扩展 ID 固定为 `ghddfnledcmjioejpfdjdfdikaapeejg`（manifest 里的 `key` 决定），与目录位置无关

## 设置（扩展选项页）

| 项 | 默认 | 说明 |
|---|---|---|
| 克隆根目录 | `~/dev` | 克隆到「根目录/仓库名」 |
| 编辑器 App 名称 | `Visual Studio Code` | `/Applications` 下的 App 名；留空只克隆不打开 |

## URL 识别规则

| 页面 | 仓库 | 分支 |
|---|---|---|
| `github.com/owner/repo/...` | 前两段 | `tree/` 或 `blob/` 之后 |
| 其它域名（按 GitLab）`host/group/sub/repo/-/...` | `/-/` 之前全部 | `/-/tree/` 或 `/-/blob/` 之后 |

- 分支名可能含 `/`，与文件路径混在一起：用 `git ls-remote` 取远程实际存在的最长前缀
- 远程没有对应分支 / 标签（如 commit SHA 链接）→ 直接报错

## 常见问题

- 「本地程序异常：Specified native messaging host not found」→ 没跑 `install.sh`，或移动了仓库目录后没重跑
- 「打开编辑器失败：Unable to find application」→ 选项页编辑器名称与 `/Applications` 里的 App 名不一致
- 私有库克隆失败 → 先在终端 `git ls-remote <仓库地址>` 确认本机凭证可用

## 开发

- 测试：`cd host && python3 -m unittest`
- 本地程序由 Chrome 用系统 python（3.9）启动，代码保持 3.9 兼容

## 许可证

[MIT](LICENSE)
