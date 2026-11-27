# RustFS 懒猫应用适配器

本仓库为上游 [RustFS](https://github.com/rustfs/rustfs) 维护懒猫官方应用
`white.lazycat.app.rustfs` 的自动更新适配。共享工作流跟踪 RustFS 的稳定三段式
Release 标签，例如 `1.0.7`，将官方 amd64 镜像转存到懒猫官方仓库后生成 LPK 并提交审核。

## 升级兼容

旧版 `white.lazycat.app.rustfs-v1.0.0.lpk` 使用以下运行契约，新版本继续保持：

- 控制台走应用域名的 9001 服务；S3 API 走 TCP 9000；
- `/lzcapp/var/data` 绑定到容器 `/data`；
- `/lzcapp/var/config` 绑定到容器 `/config/rustfs`；
- 服务名保持 `rustfs`，应用子域名保持 `rustfs`。

RustFS 官方镜像使用 UID/GID `10001:10001`。升级第一次启动时，setup script
只在数据目录缺少标记时修复旧数据目录和配置目录的所有权，避免已有对象因旧版 root
写入而无法读取。升级后仍应确认控制台登录、创建 bucket、上传和下载对象。

默认账号密码沿用旧应用的 `rustfsadmin / rustfsadmin`，首次登录后请立即修改。

定时任务每天北京时间 10:17 检查上游，有更新时自动打包并送审。

## 自动流程

推送配置只执行检查。Actions 的手动运行默认勾选 `dry-run`，取消勾选后才会进行镜像转存、
LPK 构建和官方审核提交。组织级 `LZC_API_TOKEN` 需要授权给本仓库，工作流使用
`secrets: inherit`。正式运行成功后会提交状态锁并创建带版本号的 GitHub Release，Release
只上传 `.lpk` 文件。

### 本地检查

```bash
python3 -m unittest discover -s tests -v
lzc-cli project build
lzc-cli lpk lint dist/white.lazycat.app.rustfs-v*.lpk
```

## 来源

- 上游源码：https://github.com/rustfs/rustfs
- RustFS Docker 镜像：https://hub.docker.com/r/rustfs/rustfs
- 懒猫开发者文档：https://developer.lazycat.cloud/
