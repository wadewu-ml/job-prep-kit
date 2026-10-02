# 本地工具

Python 3.10+，仅标准库。在公开模板项目根目录运行，--workspace 指向初始化后的个人目录。工具不联网提交、不读取邮箱、不创建定时任务。

## 初始化

```powershell
python scripts/init_workspace.py
```

默认 private/；已有目录不覆盖。可用 --dest 指向新的个人目录，但自选位置的云同步/公开仓库保护由使用者确认。不要用个人工作区重新分发模板。

## 台账

```powershell
python scripts/tracker.py validate --workspace private
python scripts/tracker.py render --workspace private
```

只维护 private/applications/data.json。总表、时间轴、日程为生成视图。遇到手工旧文件会拒绝覆盖，先用 --output-dir private/preview 生成新视图，核对迁移后再使用。生成器不会改 data.json，不会自动把扫描候选变成申请。

数据样例见 ../templates/application-example.json，**全部为合成资料，不是实际可投岗位**。顶层 schema_version=1，applications 为数组。

- id：稳定唯一记录编号。company 与 project 一起确定统计分组；role 为岗位，choices 为明确登记的志愿列表。
- status：candidate / ready / draft / submitted / assessment / interview / waiting / offer / rejected / withdrawn / signed。
- sources：以来源id为键。kind=employer/school/personal_notice/community/other；locator 为原URL或私有凭证定位，excerpt 为必要短摘录，checked_at 为核验时间。
- submission：实际提交时间 at、凭证 source、实际附件 resume_version；没有真实凭证不填。流程中状态必须关联提交记录。resume_version 可直接填写实际发送的附件版本或文件名，不要求先登记哈希。历史附件确实缺失时，用 resume_unavailable_reason 说明原因，不同时填写 resume_version；工具会明确提醒待补，不会把真实投递改成未投。
- events：title、at、kind、source、done；可选 notified_at。kind=deadline/scheduled/suggested。官方日期必须关联直接来源。通知到达和截止分开。
- result：offer/signed/rejected 状态需要 result.source 指向正式结果来源，个人感觉不作为结果。
- next_action：当前下一动作。工具优先列出逾期、当天及未来七天的未完成节点，再列下一动作；不自动提醒，不把逾期推断为淘汰。

时间使用带时区 ISO 格式，例如 2030-09-02T18:00:00+08:00。只有日期而没有具体时刻的原文先放 next_action 和来源摘录，核实后再录精确提醒；不要编造23:59。正文、来源与原文件是否真实仍由用户/助手核验，校验器只检查结构和来源关联。

## 简历文件核对（可选）

```powershell
python scripts/resume_manifest.py --workspace private
```

仅在需要比较文件是否变化时使用。versions.json 每个版本记录 id、direction、docx、pdf、docx_sha256、pdf_sha256，路径相对 private/resumes/。哈希可用 Get-FileHash 获取完整 SHA256。未维护此清单也能跟进投递和生成日程。

这个命令只比较文件哈希，不读懂文件，不生成简历，不代替人工/文档工具检查。

## 开发时按需验证

```powershell
python -B -m unittest discover -s tests -v
```

tests/ 是可选的离线脚本用例。普通文档修改无需跑测试；修改工具时验证相关场景即可。真实站点适配用扫描器 --check 查看。

需要分发源码 ZIP 时，提交公开文件后运行 `python scripts/package_source.py`，仅打包已提交源码；输出在 dist/，不会包含 Git 历史或忽略的私人目录。
