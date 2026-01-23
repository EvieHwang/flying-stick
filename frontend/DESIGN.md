# Design System Documentation

This document describes the design system used in {{PROJECT_NAME}}. It's intended to be portable—you can copy this frontend setup to new projects.

## Design Philosophy

> "The UI should be invisible."

This design system prioritizes **information density** over visual ornamentation. Inspired by well-designed newspapers, financial terminals (Bloomberg), and productivity tools (Linear), the goal is to present maximum useful content with minimum visual noise.

### Core Principles

1. **Content over chrome**: UI elements should serve the content, not draw attention to themselves
2. **Information density**: Tighter spacing, smaller base font, more content visible at once
3. **Functional aesthetics**: Every pixel should earn its place
4. **Equal-quality themes**: Both light and dark modes are first-class citizens
5. **Accessibility first**: High contrast ratios, clear focus states, keyboard navigation

## Typography

### Scale

Our typography scale uses a **14px base** (smaller than the typical 16px) for information density:

| Token | Size | Line Height | Use Case |
|-------|------|-------------|----------|
| `text-xs` | 12px | 1.4 | Labels, captions, metadata |
| `text-sm` | 13px | 1.4 | Secondary text, descriptions |
| `text-base` | 14px | 1.5 | Body text, primary content |
| `text-lg` | 16px | 1.5 | Subheadings, emphasis |
| `text-xl` | 18px | 1.4 | Section headers |
| `text-2xl` | 20px | 1.3 | Page titles |
| `text-3xl` | 24px | 1.3 | Major headings |
| `text-4xl` | 30px | 1.2 | Hero text |

### Font Stack

```css
font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
font-family: "JetBrains Mono", Menlo, Monaco, Consolas, monospace; /* code */
```

### Line Heights

Tighter line heights (1.3-1.5) compared to typical web defaults (1.6-1.8) for:
- More content visible without scrolling
- Print-like reading experience
- Better visual grouping

## Spacing

### Scale

Tighter than Tailwind defaults, optimized for dense layouts:

| Token | Value | Use Case |
|-------|-------|----------|
| `0.5` | 2px | Micro adjustments |
| `1` | 4px | Inline spacing, icon gaps |
| `1.5` | 6px | Tight component padding |
| `2` | 8px | Standard element spacing |
| `3` | 12px | Component internal padding |
| `4` | 16px | Card padding, section gaps |
| `6` | 24px | Section spacing |
| `8` | 32px | Large section gaps |

### Guidelines

- **Cards**: Use `p-4` (16px) for compact padding, not the default `p-6`
- **Form elements**: Prefer `gap-2` (8px) between form fields
- **Sections**: Use `space-y-4` or `space-y-6` for content sections
- **Touch targets**: Maintain minimum 32px for interactive elements

## Color System

Colors are defined as CSS custom properties (variables) for instant theme switching.

### Semantic Tokens

| Token | Light Mode | Dark Mode | Purpose |
|-------|------------|-----------|---------|
| `--background` | White | Near black | Page background |
| `--foreground` | Near black | Off white | Primary text |
| `--muted` | Light gray | Dark gray | Disabled, secondary backgrounds |
| `--muted-foreground` | Medium gray | Light gray | Secondary text |
| `--border` | Light gray | Dark gray | Borders, dividers |
| `--primary` | Near black | Off white | Primary actions |
| `--destructive` | Red | Dark red | Error states, delete actions |

### Usage

Always use semantic tokens, not raw colors:

```tsx
// Good
<div className="bg-background text-foreground border-border" />

// Avoid
<div className="bg-white text-gray-900 border-gray-200" />
```

## Components

### Button

Available variants:
- `default`: Primary action
- `secondary`: Secondary action
- `outline`: Tertiary action
- `ghost`: Minimal, icon buttons
- `link`: Inline links
- `destructive`: Dangerous actions

Sizes:
- `lg`: Large buttons for primary CTAs
- `default`: Standard size
- `sm`: Compact areas
- `compact`: Information-dense tables/lists
- `icon`: Square icon-only buttons

```tsx
import { Button } from "@/components/ui/button"

<Button variant="default" size="compact">Save</Button>
```

### Card

Containers for grouped content. Uses tighter padding than default shadcn.

```tsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

<Card>
  <CardHeader>
    <CardTitle>Section Title</CardTitle>
  </CardHeader>
  <CardContent>
    Content here
  </CardContent>
</Card>
```

### Input & Textarea

Form controls with optional `compact` prop for dense forms.

```tsx
import { Input } from "@/components/ui/input"

<Input compact placeholder="Search..." />
```

## Dark Mode

### Implementation

1. **CSS Variables**: All colors defined as HSL variables in `:root` and `.dark`
2. **Class-based**: Theme applied via `dark` class on `<html>`
3. **No flash**: Inline script in `<head>` applies theme before render
4. **System support**: Respects `prefers-color-scheme` when set to "system"

### Theme Switching

```tsx
import { useTheme } from "@/components/ThemeProvider"

function MyComponent() {
  const { theme, setTheme, resolvedTheme } = useTheme()

  return (
    <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
      Current: {resolvedTheme}
    </button>
  )
}
```

### Guidelines

- Test both themes equally during development
- Use semantic color tokens (they adapt automatically)
- Avoid hardcoded colors that don't respect theme
- Check contrast ratios in both modes

## Accessibility

### Requirements

- **Color contrast**: Minimum 4.5:1 for normal text, 3:1 for large text
- **Focus indicators**: Visible focus rings on all interactive elements
- **Keyboard navigation**: All functionality accessible via keyboard
- **Screen readers**: Proper ARIA labels and semantic HTML

### Implementation

- Focus ring: `focus-visible:ring-2 focus-visible:ring-ring`
- Skip link: Consider adding for complex pages
- Reduced motion: Respect `prefers-reduced-motion`

## Adding New Components

To add more shadcn/ui components:

1. Visit [ui.shadcn.com/docs/components](https://ui.shadcn.com/docs/components)
2. Copy the component code
3. Place in `src/components/ui/`
4. Adjust padding/spacing for information-dense design:
   - `p-6` → `p-4`
   - `gap-4` → `gap-2` or `gap-3`
   - `text-base` → `text-sm` where appropriate

### Example: Adding Alert

```tsx
// src/components/ui/alert.tsx
import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const alertVariants = cva(
  "relative w-full rounded-lg border p-3 [&>svg~*]:pl-7 [&>svg]:absolute [&>svg]:left-3 [&>svg]:top-3",
  {
    variants: {
      variant: {
        default: "bg-background text-foreground",
        destructive: "border-destructive/50 text-destructive",
      },
    },
    defaultVariants: { variant: "default" },
  }
)
// ... rest of component
```

## Technical Reference

### Dependencies

```json
{
  "react": "^18.2.0",
  "tailwindcss": "^3.4.0",
  "class-variance-authority": "^0.7.0",
  "clsx": "^2.1.0",
  "tailwind-merge": "^2.2.0",
  "lucide-react": "^0.312.0"
}
```

### File Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/           # shadcn components
│   │   ├── ThemeProvider.tsx
│   │   └── ThemeToggle.tsx
│   ├── lib/
│   │   └── utils.ts      # cn() helper
│   ├── index.css         # Tailwind + CSS variables
│   └── main.tsx          # App entry with ThemeProvider
├── tailwind.config.ts    # Design tokens
└── index.html            # Theme flash prevention script
```

### Key Files

| File | Purpose |
|------|---------|
| `tailwind.config.ts` | Custom spacing, typography, colors |
| `src/index.css` | CSS variables for light/dark themes |
| `src/lib/utils.ts` | `cn()` class merging utility |
| `index.html` | Theme flash prevention inline script |
| `src/components/ThemeProvider.tsx` | Theme context and persistence |

## Portability Checklist

To copy this design system to a new project:

- [ ] Copy `frontend/` directory
- [ ] Update `package.json` name field
- [ ] Replace `{{PROJECT_NAME}}` placeholders
- [ ] Run `npm install`
- [ ] Verify `npm run dev` works
- [ ] Test light/dark mode toggle
- [ ] Test theme persistence across reload
