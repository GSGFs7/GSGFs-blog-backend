#!/bin/bash
echo "=== [1] 系统基础信息 ==="
uname -a
cat /etc/os-release | grep -E '^(NAME|VERSION)='
id

echo -e "\n=== [2] 命名空间支持 (Namespaces) ==="
# 检查是否支持用户命名空间（Rootless 的基础）
[ -f /proc/self/ns/user ] && echo "User Namespace: 已启用" || echo "User Namespace: 未启用"
sysctl kernel.unprivileged_userns_clone 2> /dev/null || echo "kernel.unprivileged_userns_clone: 不存在 (可能是非 Debian/Arch 系)"

echo -e "\n=== [3] 用户 ID 映射 (SubUID/SubGID) ==="
# 检查当前用户是否有足够的 UID 映射范围
echo "UID 映射 (/etc/subuid):"
grep "$(id -un)" /etc/subuid || echo "未找到当前用户的 subuid 配置"
echo "GID 映射 (/etc/subgid):"
grep "$(id -gn)" /etc/subgid || echo "未找到当前组的 subgid 配置"

echo -e "\n=== [4] 存储驱动支持 ==="
# 检查内核是否加载了 overlay 模块
lsmod | grep overlay || echo "内核模块 'overlay' 未加载"
# 检查 FUSE 设备（如果需要用 fuse-overlayfs）
ls -l /dev/fuse || echo "/dev/fuse 设备不可访问"

echo -e "\n=== [5] 挂载权限测试 (关键) ==="
# 尝试在 /tmp 目录下进行一次非特权 overlay 挂载测试
mkdir -p /tmp/ovl_lower /tmp/ovl_upper /tmp/ovl_work /tmp/ovl_merged
mount -t overlay overlay -o lowerdir=/tmp/ovl_lower,upperdir=/tmp/ovl_upper,workdir=/tmp/ovl_work /tmp/ovl_merged 2>&1 &&
    {
        echo "Native Overlay Mount: 成功"
        umount /tmp/ovl_merged
    } ||
    echo "Native Overlay Mount: 失败 (报错原因如上)"

echo -e "\n=== [6] Buildah 现状 ==="
buildah --version
buildah info --format '{{.store.GraphDriverName}} {{.store.GraphRoot}}'

echo -e "\n=== [7] Cgroups 版本 ==="
stat -fc %T /sys/fs/cgroup/
