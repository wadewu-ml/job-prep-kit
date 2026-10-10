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

只维护 private/applications/data.json。总表、时间轴、日程和 dashboard.html 都是生成视图。双击 private/applications/dashboard.html 即可查看，无服务器、无网络依赖；更新台账后重新 render 并刷新页面。遇到手工旧文件会拒绝覆盖，先用 --output-dir private/preview 生成新视图，核对迁移后再使用。生成器不会改 data.json，不会自动把扫描候选变成申请。看板含个人记录和文件路径，同样不要上传；它只展示台账，不自动核实来源或改变状态。

数据样例见 ../templates/application-example.json，**全部为合成资料，不是实际可投岗位**。顶层 schema_version=1，applications 为数组。

- id：稳定唯一记录编号。company 与 project 一起确定统计分组；role 为岗位，choices 为明确登记的志愿列表。
- status：candidate / ready / draft / submitted / assessment / interview / waiting / offer / rejected / withdrawn / signed。
- sources：以来源id为键。kind=employer/school/personal_notice/community/other；locator 为原URL或私有凭证定位，excerpt 为必要短摘录，checked_at 为核验时间。
- submission：实际提交时间 at、凭证 source、实际附件 resume_version；没有真实凭证不填。流程中状态必须关联提交记录。resume_version 可直接填写实际发送的附件版本或文件名，不要求先登记哈希。历史附件确实缺失时，用 resume_unavailable_reason 说明原因，不同时填写 resume_version；工具会明确提醒待补，不会把真实投递改成未投。
- events：title、at、kind、source、done；可选 notified_at。kind=deadline/scheduled/suggested。官方日期必须关联直接来源。通知到达和截止分开。
- result：offer/signed/rejected 状态需要 result.source 指向正式结果来源，个人感觉不作为结果。
- materials（可选）：关联文件或官方网页，如 `{"jd":"applications/role-001/jd.md","resume":"resumes/archive/general-v1.pdf","interview":"interviews/role-001.md"}`。文件路径相对个人工作区，也接受现有文件的绝对路径；已有材料无需迁移。看板可点击打开本地文件，未找到时提示待补。resume 指向实际发出的留存件，不是不断变化的当前稿。
- needs_user（可选）：确实需要本人处理的事项，用一句话说明；解决后删除或清空，不必给每个岗位填。
- location（可选）：已知工作地；不清楚时省略，不推断。
- brief（可选）：助手处理该岗位时留下的短摘要，可按需填 `work`（实际工作）、`reason`（推进理由）、`question`（影响选择的待核条件）、`preparation`（准备重点）。内容依据已有 JD、经历和复盘，原文仍由 materials 和 sources 关联；不是新一套必填表，也不生成匹配分数。
- next_action：岗位当前的下一动作；每条日程以自己的 title 展示，避免多个节点套用同一句下一动作。工具不自动提醒，不把逾期推断为淘汰。

看板顶部优先展示未来七天的正式安排，然后是时间已过待核实的事项、建议时间和其他明确下一步。最多突出三项，其余可展开。本人待办单独完整列出，不受三项上限影响，也不因同一岗位已有日程而隐藏；已结束记录的待办不再列出。无日期事项按台账顺序展示，不代表计算出的机会排名。submitted/waiting 的普通 next_action 留在岗位列表；确有跟进安排时再登记事件或 needs_user，不因等待时间长而自动催办。已结束记录默认收起，可筛选查看。

`materials` 可增加 `experience` 关联相关经历、`offer` 关联录用条件文件。看板将样式和交互内嵌进一个 HTML，分发或本地打开不需要旁边再放 CSS/JS 文件。相对“今天/明天”按生成时间计算，跨日后重新生成；来源核验时间和页面生成时间分别展示。

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
