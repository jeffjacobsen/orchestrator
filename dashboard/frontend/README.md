# Orchestrator Dashboard Frontend

React 18 + TypeScript + Vite frontend for the Orchestrator Dashboard.

## Features

- ✅ React 18 with TypeScript
- ✅ Vite for fast development and building
- ✅ TailwindCSS for styling
- ✅ React Query for data fetching
- ✅ Dark/light mode with system preference detection
- ✅ Responsive design
- ✅ Type-safe API client

## Development

### Install Dependencies

```bash
npm install
```

### Start Development Server

```bash
npm run dev
```

Opens at http://localhost:5173 with hot reload.

### Build for Production

```bash
npm run build
```

Output in `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## Environment Variables

Create `.env` in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
VITE_API_KEY=your-api-key-here
VITE_WS_URL=ws://localhost:8000/ws
```

## Project Structure

```
src/
├── components/       # React components
│   ├── AgentCard.tsx
│   └── AgentList.tsx
├── services/         # API client
│   └── api.ts
├── types/           # TypeScript types
│   └── index.ts
├── lib/             # Utilities
│   └── utils.ts
├── App.tsx          # Main app component
├── main.tsx         # Entry point
└── index.css        # Global styles
```

## Adding Components

Components follow the shadcn/ui pattern:

1. Create component in `src/components/`
2. Use TailwindCSS for styling
3. Import types from `src/types/`
4. Use `cn()` utility for class merging

Example:
```tsx
import { cn } from '../lib/utils'

export function MyComponent({ className }: { className?: string }) {
  return (
    <div className={cn('base-classes', className)}>
      Content
    </div>
  )
}
```

## Styling

Uses TailwindCSS with custom design tokens defined in `index.css`:

- Colors: `bg-background`, `text-foreground`, `border`, etc.
- Dark mode: Automatic with `dark:` prefix
- Custom utilities: See `lib/utils.ts`

## Data Fetching

Uses React Query for data fetching:

```tsx
import { useQuery } from '@tanstack/react-query'
import { agentApi } from '../services/api'

function MyComponent() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentApi.list(),
  })

  // Handle loading, error, data...
}
```

## Deployment

### Static Deployment (Vercel, Netlify, etc.)

```bash
npm run build
```

Deploy the `dist/` directory.

### Docker

See `Dockerfile` in this directory.

### Environment Variables in Production

Set these in your hosting platform:
- `VITE_API_URL`
- `VITE_API_KEY`
- `VITE_WS_URL`

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)

## Next Steps

See parent README.md and DASHBOARD_PROPOSAL_V2.md for Phase 2+ features.
