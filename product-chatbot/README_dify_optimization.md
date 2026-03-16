# 固特异知识库：Dify 段落原地优化与元数据注入 (In-Place Segment Optimization)

## 背景问题
Dify 知识库在处理复杂的《固特异产品手册》（包含大量表格、尺寸规格表、性能参数表）时，基于 Token 长度的分段往往会将长表格或长文本从中间截断。这导致向量检索时缺乏上下文（如：某个轮胎尺寸所在的表格切片，完全不包含轮胎名称），大模型回答“某个尺寸可用与否”、“性能如何”时严重受限。

## 解决方案
本方案不再依赖 Dify 的“清洗分段”，而是采用**AI 增强的原地段落优化（In-Place Segment Optimization）**策略。
我们通过 `dify_segment_optimizer.py` 脚本，将 Dify 中已分好段的知识切片逐个拉取下来，使用 OpenAI API 对其进行信息提取与扩展，最后拼装成“高保真+强检索”的内容后再写回。

### 优化的分段结构
脚本处理后的知识库 Chunk，将在保留原始数据（不破坏任何文字和长表格）的基础上，在开头插入强有力的 `<metadata>`：

```xml
<metadata>
keywords: 固特异鹰驰 F1, 245/45R18, 高性能, 湿地制动, 降噪
faq:
- Q: 固特异 Eagle F1 的核心卖点是什么？ A: 提供卓越的湿地操控性能。
- Q: 它支持18寸的规格吗？ A: 是的，该段落包含了18英寸的规格表。
</metadata>

<original_content>
【原汁原味的 Dify 原始片段，哪怕被截断的表格也在，因为前面补充了这段代表了什么！】
</original_content>
```

这种结构利用了 GPT 在生成 Embeddings 或执行召回重排（Rerank）时对首尾信息敏感的特性，通过 `FAQ` 和 `keywords` 极大地提高了特定尺寸和特性的命中率。

## 使用指引

### 1. 环境准备
确保您的 `.env` 文件已配置完全（目前项目中已经在使用该配置）：
```ini
DIFY_DATABASE_KEY=dataset-xxx...
API_ENDPOINT=http://localhost/v1
OPENAI_API_KEY=sk-proj-...
```

相关依赖库已经可以直接运行：
```bash
pip install requests python-dotenv openai
```

### 2. 运行优化脚本
原先旧的两份测试性质的 Python 脚本已被删除。请直接运行本目录下提供的新版增强脚本：

```bash
python dify_segment_optimizer.py
```

**脚本执行流程：**
1. 读取 `.env` 加载配置与密钥。
2. 连接本地 Dify 实例，抓取指定数据集中的全部现有切片（Segments）。
3. 循环遍历：调用 OpenAI (`gpt-4o-mini`) 读取原段落，提取关键字并生成 3-5 个假设性 FAQ。
4. 将 `<metadata>`（即关键词和FAQ）注回段落开头。
5. 通过 API 写回 Dify 知识库。
*(注：脚本设计为幂等操作，如果段落已经包含 `<metadata>` 则会自动跳过，方便重复跑中断的任务)*

### 3. Dify 后台推荐配置 (配合此工具使用)
运行完毕上述脚本后，建议再次去 Dify 后台 -> 该数据集 -> **检索设置** 中进行确认调整以达到最好效果：
- **检索模式**：强烈推荐选 **混合检索 (Hybrid Search)** (针对轮胎尺寸的查询，建议设置权重: 语义搜索 0.3 / 关键词搜索 0.7 更加精准命中数字与型号)。
- **Top-K 召回量**：调高到 **6** 或者 **8**。
- **Score 阈值 / Rerank 模型**：如果有条件，建议开启重排 (Reranker) 以便达到极致的查全率。

如此设置配合元数据注入，即便面对长篇幅的产品规格大表也能做到准确检索，不再“前言不搭后语”。
