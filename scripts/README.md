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

数据样例见 ../templates/application-example.json，**全部为合成资料，不是实际可投岗位**。顶层 schema_version=1，applications 为数组。以下顶层字段可选，省略时保留默认行为：

- `scope_note`：非空字符串，说明当前台账的数据范围，例如“合成演示：仅包含已收到通知的部分记录，并非全量”。看板顶部及三份 Markdown 均原样转义显示，保留空白和换行，不解析其中的 HTML 或 Markdown。
- `workspace_links`：导航标签到文件路径或网页地址的字符串映射，标签和值都须非空。提供时整体替换顶部默认导航，空对象表示不显示导航；省略时仍使用目标与偏好、简历底稿、经历库。相对路径以工作区为基准，也支持工作区外已有文件的绝对路径；复用安全链接规则，仅允许 HTTP(S) 网页或已有本地文件，危险协议不生成链接，缺失文件提示待补。只关联已有材料，不创建模板或迁移文件。
- `focus`：用户当前目标，与企业状态分开保存。`mode` 为 `active`（默认求职进行中）、`closing`（只办收尾）、`paused` 或 `complete`。可选 `application_ids` 限定跟进岗位 ID，省略时 active 跟进未结束岗位，空数组表示不跟进任何岗位；closing 必须明确列出至少一个现有 ID。可选 `note` 简述当前范围。paused/complete 不产生当前任务，其他状态和凭证保留。收尾可继续跟进 signed 岗位；rejected/withdrawn 不恢复为当前记录。

例如，只为某条**合成记录**办理收尾，在顶层加入：

```json
"focus": {"mode": "closing", "application_ids": ["synthetic-001"], "note": "只核对该记录的收尾材料"}
```

同时按最新授权更新该岗位的 next_action / needs_user，并将收尾事件标为 `category: "closing"`。其余事件默认 `recruitment`，不会在 closing 模式恢复为待面试。这里不改变企业状态，不代替签约或撤回操作。手工用户在自己的主表标明当前范围即可。

每条 applications 记录：

- id：稳定唯一记录编号。company 与 project 一起确定统计分组；role 为岗位，choices 为明确登记的志愿列表。
- status：candidate / ready / draft / submitted / assessment / interview / waiting / offer / rejected / withdrawn / signed。
- sources：以来源id为键。kind=employer/school/personal_notice/community/other；locator 为原URL或私有凭证定位，excerpt 为必要短摘录，checked_at 为核验时间。
- submission：实际提交时间 at、凭证 source、实际附件 resume_version；没有真实凭证不填。submitted 必须关联提交记录；其他流程中状态的历史提交缺失场景见 stage_evidence。resume_version 可直接填写实际发送的附件版本或文件名，不要求先登记哈希。历史附件确实缺失时，用 resume_unavailable_reason 说明原因，不同时填写 resume_version；工具会明确提醒待补，不会把真实投递改成未投。
- stage_evidence（可选）：严格为 `{"source":"notice", "submission_unavailable_reason":"合成历史缺口：原始申请时间及岗位关联未知"}`，仅允许这两个非空字符串字段。source 必须关联 sources 中 kind=employer/personal_notice 的正式阶段通知，学校或第三方线索不能代替。assessment/interview/waiting/offer/signed 没有 submission 时，允许凭此确认当前阶段，不要求编造原始投递时间或推断岗位关联；缺口必须如实说明。它不能绕过 submitted 的 submission 要求，也不能替代 offer/signed/rejected 的 result.source。视图展示阶段凭证及提交历史缺口，不将缺失凭证解释为“尚未提交”，不把通知记录计作新增已投。已投企业/项目、记录及志愿数字仅统计有 submission 的记录，另列无 submission 的通知确认阶段条数；数字只反映登记凭证，不代表全部实际申请。
- events：title、at、kind、source、done；可选 notified_at。kind=deadline/scheduled/suggested。可选 category=recruitment/closing，省略为 recruitment；收尾模式只显示 closing 事件。官方日期必须关联直接来源。通知到达和截止分开。title 写清这一步的事项，详细说明可放可选的 note 字符串。按通知相对期限推算的时间用 `time_precision: "estimated"`，页面会明确标为“约”和“推算时间”；默认 exact 仅用于已核实的具体时刻。可选 `done_source` 关联完成依据，须同时有 done=true；它与 source 所指的日程时间依据分别保留。
- result：offer/signed/rejected 状态需要 result.source 指向正式结果来源，个人感觉不作为结果。
- materials（可选）：关联文件或官方网页，如 `{"jd":"applications/role-001/jd.md","resume":"resumes/archive/general-v1.pdf","interview":"interviews/role-001.md"}`。文件路径相对个人工作区，也接受现有文件的绝对路径；已有材料无需迁移。看板可点击打开本地文件，未找到时提示待补。resume 指向实际发出的留存件，不是不断变化的当前稿。
- needs_user（可选）：确实需要本人处理的事项，用一句话说明；解决后删除或清空，不必给每个岗位填。
- location（可选）：已知工作地；不清楚时省略，不推断。
- brief（可选）：助手处理该岗位时留下的短摘要，可按需填 `work`（实际工作）、`reason`（推进理由）、`question`（影响选择的待核条件）、`preparation`（准备重点）、`basis`（哪条经验如何影响本次建议，含适用边界或待验证之处）。内容依据已有 JD、经历和复盘，原文仍由 materials 和 sources 关联；不是新一套必填表，也不生成匹配分数。
- next_action：岗位当前的下一动作；每条日程以自己的 title 展示，避免多个节点套用同一句下一动作。工具不自动提醒，不把逾期推断为淘汰。

看板顶部优先展示未来七天的正式安排，然后是近七天时间已过待核实的事项、建议时间和其他明确下一步。最多突出三项，其余可展开。本人待办单独完整列出，不受三项上限影响，也不因同一岗位已有日程而隐藏；当前不跟进的记录不列待办。无日期事项按台账顺序展示，不代表计算出的机会排名。正常求职时 submitted/waiting 的普通 next_action 留在岗位列表；确有跟进安排时再登记事件或 needs_user，不因等待时间长而自动催办。历史与不跟进的记录默认收起，可筛选查看。

看板按近期安排、岗位概况、跟进任务和相关材料组织。日程卡只显示时间、事项和跟进入口；岗位说明独立展示，材料按用途集中列出，不重复放进每张日程卡。正文为 18px，辅助信息至少 14px，窄窗口改为单列；只有一条记录且仍在当前范围时隐藏筛选栏。brief.preparation 和 brief.basis 可以用换行分隔，页面按条目显示；来源和历史记录按需展开。

`materials` 可增加 `experience` 关联相关经历、`offer` 关联录用条件文件、`review` 关联事件复盘、`lessons` 关联本次采用的经验。后两项归在“复盘与经验”中，同一文件不用重复关联。经验怎么形成和复用见 [对应流程](../workflows/06-复盘与经验复用.md)。看板将样式和交互内嵌进一个 HTML，分发或本地打开不需要旁边再放 CSS/JS 文件。相对“今天/明天”按生成时间计算，跨日后重新生成；来源核验时间和页面生成时间分别展示。

近期待办只列当前范围内近七天待核实、今天和未来七天的未完成事件。更早的未确认事项折叠保留，不自动标记完成，也不将其旧准备动作重新生成无日期任务；更远的安排保留在时间轴。历史凭证和资料缺口单列说明，不自动成为当前任务。

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

需要分发源码 ZIP 时，提交公开文件后运行 `python scripts/package_source.py`，仅打包已提交源码；默认输出 `dist/job-prep-kit-source-<commit>.zip`，不会覆盖旧包，也不会包含 Git 历史或忽略的私人目录。按提交编号区分新旧包，不把旧的同名 ZIP 当作当前源码。可用 --output 指定新的输出文件名。
