# look_at_pdf Skill

## 工具定义

`look_at_pdf` 用于将本地扫描版 PDF 或图片文件转换为标准 Markdown。核心对象是无内嵌文字层的扫描 PDF；输出按页生成，并用 `## 第X页` 标记分页。检测到表格时，必须输出标准 Markdown 表格语法。

## 统一入参

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| file_path | string | 是 | 待转换文件的本地绝对路径或相对路径 |
| enhance_img | boolean | 否 | 是否开启图像增强、去噪和轻微倾斜矫正 |
| fix_table | boolean | 否 | 是否自动补齐和矫正错位表格排版 |

## 统一返回结构

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| code | integer | `0` 表示成功，非 `0` 为异常码 |
| msg | string | 执行信息或错误原因 |
| md_content | string | 完整 Markdown 文本 |
| stat.page_num | integer | 页数 |
| stat.table_num | integer | 表格数 |
| stat.avg_accuracy | number | OCR 平均置信度百分比，非人工标注准确率 |

## 错误码

| code | 含义 |
| --- | --- |
| 0 | 成功 |
| 1001 | 文件不存在 |
| 1002 | 文件类型不支持 |
| 1003 | PDF 已加密 |
| 1004 | 文件损坏或无法读取 |
| 1005 | 空白 PDF 或未识别到内容 |
| 1006 | OCR 后端不可用 |
| 1007 | MCP 服务端口被占用 |
| 1999 | 未知异常 |

## 本地函数

函数路径：

```python
from look_at_pdf import convert_to_markdown
```

调用示例：

```python
result = convert_to_markdown(
    file_path="samples/sample_scanned.pdf",
    enhance_img=True,
    fix_table=True,
)
print(result["code"], result["stat"])
print(result["md_content"])
```

命令示例：

```bash
python local_demo.py
```

## MCP Skill

启动服务：

```bash
python mcp_server.py --port 8001
```

MCP 地址：

```text
http://127.0.0.1:8001/mcp
```

注册工具名：

```text
look_at_pdf
```

MCP 客户端调用示例：

```python
result = await session.call_tool(
    "look_at_pdf",
    arguments={
        "file_path": "samples/sample_scanned.pdf",
        "enhance_img": True,
        "fix_table": True,
    },
)
```

本项目也提供可直接运行的客户端演示：

```bash
python mcp_client_demo.py --url http://127.0.0.1:8001/mcp
```
