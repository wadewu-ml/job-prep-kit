# 简历工作区

真实简历保存在私人目录。source/ 放可编辑稿，current/ 放正式投递文件，archive/ 保留已发出的历史附件；已有源目录可以直接引用，不必复制一套。

按 ../workflows/01-简历制作.md 核对事实、页面和提取文本。更换当前文件后，已投记录仍指向当时实际发送的附件；同名不代表内容相同。

需要机器核对附件时，可选用 versions.json：记录 id、direction、docx、pdf、docx_sha256、pdf_sha256，路径相对 resumes/。在工具项目运行 `python scripts/resume_manifest.py --workspace <私人目录>`，只核文件和哈希，不证明内容或排版正确。普通投递跟进无需先填写此清单。
