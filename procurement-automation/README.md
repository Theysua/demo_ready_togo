# Procurement External Services for Dify HTTP Call

这个项目提供两个可以直接给 Dify `HTTP Call` 节点调用的外部服务：

1. `Vendor API`：根据采购项返回供应商报价
2. `PO Template API`：返回采购订单模板

## 1. 启动方式

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

服务启动后可用地址：

- `GET http://localhost:8000/health`
- `POST http://localhost:8000/api/vendor/quotes`
- `POST http://localhost:8000/api/vendor-quotations-bulk`
- `GET http://localhost:8000/api/po-template`

---

## 2. Vendor API

### 接口说明

- Method: `POST`
- URL: `http://localhost:8000/api/vendor/quotes`
- Content-Type: `application/json`

### 请求体

```json
{
  "request_id": "PR-20260311-001",
  "currency": "RMB",
  "items": [
    {
      "name": "Laptop",
      "quantity": 5,
      "unit": "pcs",
      "target_unit_price": 6000
    },
    {
      "name": "Mouse",
      "quantity": 10,
      "unit": "pcs",
      "target_unit_price": 80
    }
  ]
}
```

### 返回体

```json
{
  "request_id": "PR-20260311-001",
  "currency": "RMB",
  "quote_count": 2,
  "estimated_total": 29260,
  "quotes": [
    {
      "item_name": "Laptop",
      "recommended_vendor": "Goodyear Supplier C",
      "options": [
        {
          "item_name": "Laptop",
          "quantity": 5,
          "unit": "pcs",
          "vendor_name": "Goodyear Supplier A",
          "unit_price": 5880,
          "total_price": 29400,
          "currency": "RMB",
          "lead_time_days": 3
        },
        {
          "item_name": "Laptop",
          "quantity": 5,
          "unit": "pcs",
          "vendor_name": "Goodyear Supplier B",
          "unit_price": 6120,
          "total_price": 30600,
          "currency": "RMB",
          "lead_time_days": 5
        },
        {
          "item_name": "Laptop",
          "quantity": 5,
          "unit": "pcs",
          "vendor_name": "Goodyear Supplier C",
          "unit_price": 5700,
          "total_price": 28500,
          "currency": "RMB",
          "lead_time_days": 7
        }
      ]
    }
  ]
}
```

### Dify HTTP Call 节点配置

- Method: `POST`
- URL: `http://host.docker.internal:8000/api/vendor/quotes`
- Headers:

```json
{
  "Content-Type": "application/json"
}
```

- Body:

```json
{
  "request_id": "{{#start.request_id#}}",
  "currency": "RMB",
  "items": {{#llm.items_json#}}
}
```

### 建议上游 LLM 输出格式

让信息抽取节点输出 `items_json`，格式如下：

```json
[
  {
    "name": "Laptop",
    "quantity": 5,
    "unit": "pcs",
    "target_unit_price": 6000
  }
]
```

### 云端兼容模式

如果上游 `GET ITEMS` 节点只输出两个变量：

- `item_json_string`
- `total_budget_mentioned`

本地服务也支持直接接收这种格式，使用下面这个兼容接口：

- Method: `POST`
- URL: `http://host.docker.internal:8000/api/vendor-quotations-bulk`

请求体示例：

```json
{
  "item_json_string": "[{\"name\":\"Razer BlackWidow V4 Keyboard\",\"quantity\":2,\"unit\":\"pcs\",\"target_unit_price\":1299},{\"name\":\"Razer DeathAdder V3 Mouse\",\"quantity\":2,\"unit\":\"pcs\",\"target_unit_price\":499}]",
  "total_budget_mentioned": 4500
}
```

兼容接口会自动：

- 解析 `item_json_string`
- 兼容外层多余引号
- 生成标准报价结果
- 回传 `total_budget_mentioned` 和 `budget_gap`

---

## 3. PO Template API

### 接口说明

- Method: `GET`
- URL: `http://localhost:8000/api/po-template`

### Query 参数

- `company_code`：公司代码，默认 `GYCN`
- `business_unit`：业务单元，默认 `procurement`
- `language`：语言，默认 `zh-CN`

### 请求示例

```http
GET /api/po-template?company_code=GYCN&business_unit=IT&language=zh-CN
```

### 返回体

```json
{
  "template_id": "po-gycn-zh-cn",
  "template_name": "Standard Purchase Order Template",
  "version": "2026.03",
  "format": "json",
  "fields": [
    "po_number",
    "request_id",
    "requester",
    "department",
    "supplier_name",
    "currency",
    "items",
    "subtotal",
    "tax",
    "total_amount",
    "delivery_address",
    "payment_terms",
    "approval_status"
  ],
  "template": {
    "po_number": "",
    "request_id": "",
    "requester": "",
    "department": "IT",
    "supplier_name": "",
    "currency": "RMB",
    "items": [
      {
        "item_name": "",
        "quantity": 0,
        "unit": "pcs",
        "unit_price": 0,
        "total_price": 0
      }
    ],
    "subtotal": 0,
    "tax": 0,
    "total_amount": 0,
    "delivery_address": "",
    "payment_terms": "Net 30",
    "approval_status": "pending",
    "language": "zh-CN",
    "company_code": "GYCN",
    "generated_at": "2026-03-11T00:00:00"
  }
}
```

### Dify HTTP Call 节点配置

- Method: `GET`
- URL:

```text
http://host.docker.internal:8000/api/po-template?company_code=GYCN&business_unit={{#start.department#}}&language=zh-CN
```

---

## 4. 在 Dify 中的典型编排

### 节点 1：用户输入

用户输入自然语言采购需求，例如：

```text
帮我采购 5 台笔记本电脑和 10 个鼠标，总预算 32000 RMB
```

### 节点 2：LLM 信息抽取

提取结构化字段：

- `items_json`
- `budget`
- `currency`

示例输出：

```json
{
  "items_json": [
    {
      "name": "Laptop",
      "quantity": 5,
      "unit": "pcs",
      "target_unit_price": 6000
    },
    {
      "name": "Mouse",
      "quantity": 10,
      "unit": "pcs",
      "target_unit_price": 80
    }
  ],
  "budget": 32000,
  "currency": "RMB"
}
```

### 节点 3：条件分支

- `budget < 10000` -> Auto-purchase
- `budget >= 10000` -> Approval workflow

### 节点 4：HTTP Call - Vendor API

把抽取后的 `items_json` 发送给报价接口。

### 节点 5：HTTP Call - PO Template API

获取标准采购订单模板。

### 节点 6：LLM / Code 节点生成最终 PO

把以下输入合并：

- 用户原始采购请求
- 抽取后的结构化字段
- Vendor API 返回的推荐供应商和报价
- PO Template API 返回的模板

输出最终采购订单 JSON。

---

## 5. 最终 PO 生成示例

```json
{
  "po_number": "PO-20260311-001",
  "request_id": "PR-20260311-001",
  "requester": "Alice",
  "department": "IT",
  "supplier_name": "Goodyear Supplier C",
  "currency": "RMB",
  "items": [
    {
      "item_name": "Laptop",
      "quantity": 5,
      "unit": "pcs",
      "unit_price": 5700,
      "total_price": 28500
    }
  ],
  "subtotal": 28500,
  "tax": 3705,
  "total_amount": 32205,
  "delivery_address": "Shanghai Office",
  "payment_terms": "Net 30",
  "approval_status": "pending"
}
```

## 6. 说明

- 如果 Dify 跑在 Docker 里，本机服务通常使用 `http://host.docker.internal:8000`
- 如果部署到测试环境，把 `localhost` 替换成实际 API 域名即可
- 这两个接口当前是 mock 服务，后续可以替换为真实供应商系统和模板数据库
