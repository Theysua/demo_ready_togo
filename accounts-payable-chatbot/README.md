# Goodyear Accounts Payable (AP) Chatbot Demo

This is a demonstration project for the Goodyear AP Chatbot, showcasing an enterprise-grade AI architecture powered by **Dify**. 

The demo highlights three core capabilities:
1. **SSO & Role-Based Access Control (RBAC):** Differentiating permissions between Internal Employees and External Vendors.
2. **Intent Routing:** Using Dify to strictly route inquiries (e.g., separating casual chat, policy queries, and system actions).
3. **Agent Function Calling & Data Isolation:** Intelligently interacting with a mocked ERP API backend to query and approve invoices, while ensuring row-level data security.

---

## 📂 Project Structure

- `mock_sso/`: A FastAPI backend and frontend representing the main Chatbot UI. It handles mock single sign-on (SSO) and passes user identity (email & role) safely to Dify via proxy.
- `mock_api.py`: A simulated external backend (e.g., SAP/Snowflake) exposing OpenAPI endpoints for Dify to call (List Invoices, Approve Invoice, Create GR, Send Notification).
- `mock_api_openapi.json`: The OpenAPI schema for `mock_api.py`, which should be imported into Dify's "Custom Tools" feature.
- `goodyear_ap_knowledge_base.md`: A mock policy document meant to be uploaded to Dify's Knowledge Base.
- `accounts_payable_chatbot.yml`: The exported DSL for the Dify application workflow (can be imported into Dify).
- `start_services.sh` / `stop_services.sh`: Helper scripts to launch the local mock services.
- `test_cases_en.md` / `test_cases.md`: Structured test scenarios to validate the bot's behavior.

---

## 🚀 Quick Start Guide

### 1. Configure the Environment
You must provide a valid Dify API key and endpoint. 
Create or edit the `.env` file in the root directory:
```env
# URL for your Dify API
API_ENDPOINT=http://localhost/v1

# The API key generated from Dify App -> API Access
CHATFLOW_ACCOUNT_PAYABLE_API=app-xxxxxxxxxxxxxxxxxxxx
```

### 2. Start the Local Mock Services
Ensure you have Python 3 installed. Start the SSO proxy and Mock APIs:
```bash
# This will install requirements and start both services in the background.
./start_services.sh

# The APIs run on:
# - AP Backend Tools (mock_api): http://localhost:8003
# - Front-end Chat UI (mock_sso): http://localhost:8002
```

### 3. Configure Dify 
You must set up the application inside Dify before using the chat UI.
1. **Import the Workflow:** Use the `accounts_payable_chatbot.yml` file to import the exact workflow DSL into Dify.
2. **Add Custom Tools:** Upload `mock_api_openapi.json` to your Dify workspace as a Custom Tool.
   - Set the Auth mechanism to "API Key" -> "Header".
   - It will expect variables `x-user-email` and `x-user-role`.
   - Update the Server URL to point to your local machine (e.g., `http://host.docker.internal:8003` if Dify is running in Docker).
3. **Configure Global Variables:** In the imported App within Dify, ensure `user_email` and `user_role` are listed as required "Start Variables".
4. **Publish:** Publish your app and generate a new API key. Update your `.env` file with this key.

> **Note to Mac/Docker users:** If Dify is deployed locally via Docker-compose, make sure to bypass Dify's SSRF proxy to allow it to reach `host.docker.internal`.

### 4. Experience the Demo
Open your browser and visit:
👉 **http://localhost:8002**

You will see the mock SSO login page. Demo credentials are documented locally in `ENVIRONMENT_CREDENTIALS.md`.

Try the dual pathways:
- **Login as Internal:** You have full access. Ask the bot to *"approve INV-2001"* or *"check status of INV-1002"*.
- **Login as Vendor:** You represent an external vendor. The architecture physically strips your rights to approve an invoice or query other vendors' data. Ask the bot to *"approve INV-1001"* and watch it politely decline the request due to RBAC policies.

Use the `test_cases_en.md` document for exhaustive test prompts!

---

## 🛑 Stop the Services
When finished, stop the background Python processes:
```bash
./stop_services.sh
```
