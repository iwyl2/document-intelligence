# Document Intelligence — Web UI

**Minimalist, precision-engineered Next.js 16 interface for document ingestion, grounded chat, and interactive page citation inspection.**

![Next.js 16](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js)
![React 19](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)

---

## Overview

The frontend client provides a focused, high-density interface for interacting with the Document Intelligence RAG engine. Designed with a clean, dark-mode developer aesthetic, it prioritizes transparency of attribution and clarity of document context.

### Key Capabilities
- **Presentation Showcase (`/`)**: Interactive 5-stage architecture visualizer detailing the processing steps and empirical IR benchmarks (**Recall@5: 100%**, **MRR: 0.83**).
- **Split-Pane Workbench (`/workspace`)**:
  - **Left Rail**: Drag-and-drop PDF ingestion, live document metadata card, real-time in-memory RAM status (`X Chunks in RAM`), atomic vector store purge control, and `top_k` parameter adjustment.
  - **Right Stage**: Clean conversational stream with syntax rendering, verified grounding badges (`Grounded` vs `Fallback`), and interactive `[Page X]` citation pills.
- **Session Gatekeeper (`LoginModal`)**: Protects the in-memory ChromaDB instance and upstream LLM quota using client-side session authentication (`sessionStorage`).
- **Live Health Polling**: Continual background health check against the FastAPI `/health` endpoint with visual status pulse.

---

## Directory Layout

```text
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx                 # Root layout with fonts, metadata & AuthProvider
│   │   ├── page.tsx                   # Presentation landing page & architecture flow
│   │   ├── workspace/
│   │   │   └── page.tsx               # Product workbench (PDF upload + citation chat)
│   │   └── globals.css                # Tailwind CSS v4 directives
│   ├── components/
│   │   ├── Navbar.tsx                 # Header navigation & live backend health badge
│   │   └── LoginModal.tsx             # Workspace access gatekeeper
│   ├── context/
│   │   └── AuthContext.tsx            # Session storage authentication state
│   └── lib/
│       └── api.ts                     # Strongly-typed fetch client for backend endpoints
├── package.json                       # Dependencies & build scripts
└── tsconfig.json                      # TypeScript configuration
```

---

## Environment Configuration

Create a `.env.local` file in `frontend/`:

```env
# URL where your FastAPI backend is running
NEXT_PUBLIC_API_URL=http://localhost:8000

# Private passcode for unlocking the in-memory workspace session
NEXT_PUBLIC_WORKSPACE_PASSCODE=doc-intel-2026
```

---

## Development & Build

### 1. Install Dependencies
```bash
npm install
```

### 2. Run Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the application.

### 3. Production Build
Generate an optimized, static production build with Turbopack:
```bash
npm run build
```

### 4. Code Quality & Linting
Run ESLint across all TypeScript components:
```bash
npm run lint
```

---

## Deployment (Vercel)

The application is fully compatible with Vercel:

1. Push this repository to GitHub.
2. In Vercel, import your repository.
3. Configure the project:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: `frontend`
4. Add Environment Variables:
   - `NEXT_PUBLIC_API_URL`: Your deployed FastAPI backend URL.
   - `NEXT_PUBLIC_WORKSPACE_PASSCODE`: Your private access passcode.
5. Click **Deploy**.
