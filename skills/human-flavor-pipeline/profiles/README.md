# 笔调 Profile

Profile 只装个人或团队偏好,不改变事实规则。默认使用 `default.md`;只有用户明确指定、当前工作区已有约定,或调用方提供外部 profile 路径时才加载其它 Profile。

## 选择顺序

1. 用户在本次请求中明确给出的偏好。
2. 用户明确指定的外部 Profile,例如 `~/.config/human-flavor-pipeline/profile.md`。
3. 仓库内显式命名的 Profile,例如 `profiles/lens.md`。
4. `profiles/default.md`。

不得仅凭安装者身份猜测 Profile。报告必须写明本次启用的 Profile;没有个人 Profile 时写 `default`。

本地真稿、客户资料和未公开锚点放在安装目录外,不要写进公开仓库或生成的安装包。
