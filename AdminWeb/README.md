# AdminWeb

AdminWeb is the staff/admin web interface for TOOL-E. It provides authenticated views for inventory management, transaction monitoring, manual fallback transactions, analytics, reports export, and ML tool-identification debugging.

## Tech Stack

- React 19 + TypeScript
- Vite
- React Router
- TanStack React Query
- Zustand (persisted auth store)
- Axios
- Tailwind CSS
- Recharts
- Lucide React

## Prerequisites

- Node.js 20+ (recommended)
- npm 10+ (recommended)
- Running backend API from the Server folder

## Environment Variables

Create an .env file inside AdminWeb with:

VITE_API_BASE_URL=<API_ADDRESS>

Notes:
- Most API calls use VITE_API_BASE_URL through the shared axios instance.

## Run Locally

1. Install dependencies:

   npm install

2. Start dev server:

   npm run dev

3. Open the URL printed by Vite (usually http://localhost:5173).

## Build and Preview

- Production build:

  npm run build

- Preview production build locally:

  npm run preview

- Lint:

  npm run lint

## App Structure

- src/App.tsx
  - Defines routing for login and protected dashboard routes.
- src/components/layout/DashboardLayout.tsx
  - Auth-protected layout with sidebar navigation, sync button, user info, and logout.
- src/lib/axios.ts
  - Shared axios client configured with VITE_API_BASE_URL.
- src/lib/react-query.ts
  - Shared QueryClient configuration (5-minute stale time, retry once).
- src/lib/authStore.ts
  - Zustand auth store persisted to localStorage under auth-storage.

## Routes

- /login
- /dashboard
- /inventory
- /transactions
- /manual-transaction
- /reports
- /debug-ml

Unauthenticated users are redirected to /login.

## Feature Pages

### Login

- File: src/features/auth/LoginPage.tsx
- Purpose: authenticate admin/staff users.
- API:
  - POST /api/auth/login
- Behavior:
  - Saves token and user to persisted auth store.
  - Redirects successful login to /dashboard.

### Dashboard

- File: src/features/dashboard/DashboardPage.tsx
- Purpose: high-level metrics and period analytics.
- API:
  - GET /analytics/dashboard?period=<value>
- Behavior:
  - Shows live stats (total tools, borrowed, overdue).
  - Shows period stats and top borrowed tools chart.
  - Includes term selector and a term settings modal UI.

### Inventory

- File: src/features/inventory/InventoryPage.tsx
- Purpose: manage tool catalog.
- API:
  - GET /tools
  - POST /tools
- Behavior:
  - Search and sort tools.
  - Add new tools via modal with field validation.
  - Displays quantity and training-related metadata.

### Transactions

- File: src/features/transactions/TransactionsPage.tsx
- Purpose: monitor all borrow/return records.
- API:
  - GET /transactions (with pagination/filter/sort query params)
  - DELETE /transactions/:id
- Behavior:
  - Search, filter by status, sort by dates.
  - Displays computed status (Borrowed/Returned/Overdue).
  - Supports delete with confirmation.

### Manual Transaction

- File: src/features/manual-transaction/ManualTransactionPage.tsx
- Purpose: fallback checkout/return workflow.
- API:
  - POST /transactions (checkout)
  - GET /tools
  - GET /transactions?user_id=<id>&limit=50
  - PUT /transactions/:id (return)
- Behavior:
  - Two tabs: Checkout and Return.
  - Validates UCID, required fields, and date constraints.

### Reports

- File: src/features/reports/ReportsPage.tsx
- Purpose: date-range reporting and export.
- API:
  - GET /transactions?limit=1000&start_date=<ISO>&end_date=<ISO>
- Behavior:
  - Filters by date range.
  - Generates CSV export for transactions.

### ML Debug

- File: src/features/debug/MLDebugPage.tsx
- Purpose: test tool-identification model output.
- API:
  - POST /identify_tool (multipart/form-data image upload)
- Behavior:
  - Upload image and inspect prediction/confidence.
  - Shows structured success/error output.

## Auth and Data Notes

- Protected pages are wrapped in DashboardLayout and require a token.
- Auth state is persisted in browser storage.
- Sync Data in the sidebar invalidates all React Query caches and refetches active data.

## Known Assumptions

- Role-based access control is not yet implemented in AdminWeb.
- Dashboard term-management UI currently appears local/mocked and is not yet persisted through a dedicated API.
