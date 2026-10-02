# 十分钟走一遍求职工作区

全部案例为合成数据，2030 年的日期不是实际招聘安排，example.invalid 不是真实企业入口。不要在真实投递记录中保留本案例。

1. **经历与简历**：在 records/facts.md 练习登记“合成课程项目：整理公开数据并制作图表”，把本人环节、结果与出处分开写；据此填写 resumes/source/master.md。真实使用时由文档工具导出 DOCX/PDF 并检查内容与页面，哈希登记按需使用。本演示不附真实简历，台账会显示“历史附件待补”。
2. **筛选岗位**：在 company-info.md 练习登记示例岗位的职责、学历要求、企业官网/学校就业网原文定位及核验日期。未披露的薪资、班制写“待核”，不代替本人决定。
3. **查看已投记录**：applications/data.json 已放入一条合成提交凭证。运行工具项目中的 tracker.py render --workspace 指向本目录，打开生成的总表、时间轴和日程。不要手改三张表。
4. **处理通知**：假设收到合成面试通知，向 sources 增加 personal_notice 来源（locator、excerpt、checked_at），把 status 改为 interview；向 events 添加 title、带时区的 at、kind=scheduled、source 和 done=false。通知原文没有具体时刻就先写 next_action，不补造 23:59。再次 validate/render。
5. **复盘**：复制 interviews/TEMPLATE.md 为本场记录，填写“问题：为什么选这个岗位；回答缺口：未结合实际职责；下次改动：准备一个经历与职责对应的例子”。完成的事件改为 done=true，next_action 写下一步。
6. **比较 offer**：在 applications/Offer比较.md 中用合成条件练习比较职责、地点、薪酬结构、班制和未确认事项。只有正式书面结果才在 sources 登记证据，并填写 result.source、更新 status=offer；是否接受由本人决定。

真实投递时，submission.resume_version 写实际发送的附件版本或文件名。历史附件确实缺失时，改用 resume_unavailable_reason 说明原因；二者不能同时填，不通过伪造附件消除提醒。

理解后回到工具项目，用 `python scripts/init_workspace.py --dest private/my-search` 初始化另一个全新的空白工作区；演示目录与真实资料分开。
