# 代码基线契约

开发/Bug提交待验、测试接单/结束及复用证据时读取。协议2基线绑定具体交付，不能只看持续task_id。旧协议由原包解释，不改历史清单。

## 新交接的最小格式

```yaml
schema_version: 1
git_commit: null
scope: []
exclude: []
files: [] # 每项{path,sha256}，按path排序，实际字节摘要
evidence: [] # 相对产出任务output_dir的必要记录
```

scope/files非空，项目相对路径无绝对/..逃逸；目录递归枚举普通文件，exclude仅缓存/产物，不能排除源码。相关链接先解析目标，越界或目标未纳入blocked。删除文件保留在scope但不列files，新增/删除/内容变化均算差异。Git HEAD只作辅助，相关未提交/未跟踪文件必须包含；必要依赖/生成代码无法捕获时说明并阻塞必需验证。

## 比较与绑定

开发/Bug交付的code_baseline是该交付权威清单；根development_baseline={task_id,delivery_id,code_baseline}，测试本次授权source_delivery={task_id,delivery_id}须一致。按任务目录→原task.result_path→指定delivery→artifacts读取，不能只读result最后一条或猜run名。测试接单及结束重新枚举scope/exclude/files，与指定交付及根绑定比较，不仅比较HEAD/聚合摘要。证据路径始终相对原任务output_dir，不复制误解为本测试输出。

HEAD变化须证明无关且依赖未变；相关文件/环境/输入变化重验，无法核实blocked。代码修复仍原开发task、但新delivery和精确基线；测试仍原testing task、但新source_delivery与结论。新交付不能覆盖旧文件/失败证据，部分写入不能提前绑定。测试自验/局部通过不代替完整独立验收。

报告只写实际版本/变化/限制，精确清单留对应交付，不另导出平行清单。旧格式可靠映射可读引用，只有HEAD或未知覆盖范围不够；不能猜摘要或回写历史。
