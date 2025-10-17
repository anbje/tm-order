# TM-Order Add-ons: Detailed Development Plan

## 🗂️ Feature Development Phases

### Phase 1: Order Listing & Delivery Core

**1.1. List Undelivered Orders ✅ COMPLETED**
- Telegram: `/undelivered` command lists all undelivered orders with deadlines.
- Web UI: Add filter/view for undelivered orders, sorted by deadline.
- **Implementation**: Added `/api/orders/undelivered` endpoint and `/undelivered` bot command.

**1.2. List Undelivered Orders by Client**
- Telegram: `/undelivered_client <client>` command lists undelivered orders for a specific client.
- Web UI: Add client filter to undelivered orders view.
- **Implementation**: Added `/api/orders/undelivered/{client_name}` endpoint and `/undelivered_client <name>` bot command.

**1.3. List Delivered Orders ✅ COMPLETED**
- Telegram: `/delivered` command lists delivered orders (client, description, deadline, delivery_time).
- Web UI: Add delivered orders view with relevant columns.
- **Implementation**: Added `/api/orders/delivered` endpoint and `/delivered` bot command.

**1.4. List Delivered Orders by Client**
- Telegram: `/delivered_client <client>` lists delivered orders for a specific client.
- Web UI: Add client filter to delivered orders view.
- **Implementation**: Added `/api/orders/delivered/{client_name}` endpoint and `/delivered_client <name>` bot command.

**1.5. Deliver Order ✅ COMPLETED**
- Telegram: `/deliver <order_id>` command marks specific order as delivered.
- Web UI: Add "Mark as Delivered" action in undelivered orders view.
- **Implementation**: Added `PUT /api/orders/{order_id}/deliver` endpoint and `/deliver <order_id>` bot command.

---

### Phase 2: Order Update & Edit

**2.1. Update Order Data**
- Telegram: `/update_order <order_id>` triggers interactive update (order nr, deadline, etc.), with validation.
- Web UI: Add "Edit" action for both delivered and undelivered orders.

---

### Phase 3: Settings Customization

**3.1. Settings Command**
- Telegram: `/settings` shows current settings (deadline alarm, command labels), allows safe update.
- Web UI: Add settings panel for deadline alarm, labels, etc.

**3.2. Config Storage**
- Store settings in `config/settings.yaml` (reuse canonical config pattern).
- Ensure all changes are logged and require confirmation.

---

### Phase 4: Security, Logging, and Usability

**4.1. Confirmation for Destructive Actions**
- Require confirmation for marking delivered, updating orders, changing settings.

**4.2. Audit Trail**
- Log all changes (who, what, when) in DB or log file.

**4.3. Admin Controls**
- Restrict settings changes to authorized Telegram IDs.

---

## 📝 Evaluation Against Workspace & Project Log

### Consistency Checks
- Project Log: All changes must be deployed via git pull + Docker rebuild on VM. Never commit secrets/tokens.
- Workspace: Use existing paths (`config/*.yaml`, `api/`, `bot/`, `web/`). No new directories.
- Security: No undisclosed network calls; all settings changes must be safe and auditable.
- Style: Minimal increments, explicit docstrings, edge case handling, pure/idempotent functions.

### Potential Risks
- Token/Env Drift: Changing settings or order status via bot must not expose secrets or allow unauthorized access.
- Data Integrity: Editing delivered orders must log changes for provenance.
- Deployment: Any schema changes (e.g., new fields for audit trail) require DB migration and careful rollout.
- User Error: Confirmation dialogs and undo/rollback for destructive actions are essential.

### Mitigation
- Use confirmation flows and logging for all critical actions.
- Document all changes in `tm_order/PROJECT_LOG.md` before deployment.
- Test each feature locally before pushing to production.
- Use `.env` and `config/*.yaml` for all runtime settings.

---

## Next Steps
- Start with `/undelivered` and `/deliver` commands in Telegram and Web UI.
- Add client filtering and delivered order views.
- Implement update and settings features with audit logging.
- Review and document each phase in `tm_order/PROJECT_LOG.md` before production deployment.
