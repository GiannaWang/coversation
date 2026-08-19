# 文本转换工具 macOS 版

## 在 Mac 上打包

需要 macOS 和 Python 3.9 或更高版本。在终端进入项目目录后运行：

```bash
chmod +x build_mac.sh
./build_mac.sh
```

生成文件位于 `release/TextConverter-macOS.zip`。

## 通过 GitHub Actions 打包

将本次修改推送到 GitHub 后，打开仓库的 **Actions** 页面，选择
**Build macOS app**，点击 **Run workflow**。完成后下载名为
`TextConverter-macOS` 的构建产物。

## 使用和数据位置

解压后把 `TextConverter.app` 拖入“应用程序”文件夹即可。第一次打开未签名应用时，
可能需要在 Finder 中按住 Control 点击应用，选择“打开”。

可编辑字典会在首次启动时复制到：

`~/Library/Application Support/TextConverter/functions`

因此应用放在“应用程序”目录后仍能保存字典修改。
