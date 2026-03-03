使用 podman 和 Quadlet 部署的相关配置

使用的镜像是 `Dockerfile`

- 需要预先创建一个容器网络

```bash
podman network create app-network
```

- 如果是 Rootless 需要设置会话驻留

```bash
sudo loginctl enable-linger $USER
```

验证是否启用成功:

```bash
loginctl show-user $USER | grep Linger
```
