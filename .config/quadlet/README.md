使用 podman 和 Quadlet 部署的相关配置

如果是 Rootless 需要设置会话驻留

```bash
sudo loginctl enable-linger $USER
```

验证是否启用成功:

```bash
loginctl show-user $USER | grep Linger
```
