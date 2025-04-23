# UX Polish: Dynamic Table of Contents (TOC) Implementation

**Date:** 2025-04-12

**Author:** Cline

**Status:** ✅ Completed  

## Goal

Implement a dynamic, responsive Table of Contents (TOC) sidebar for the Markdown report views (Recommendation and Policy Comparison tabs) within the `ux-webapp`. The TOC should automatically list headings from the Markdown content and allow users to click links to navigate to the corresponding sections, similar to documentation sites like Quarto.

## Implementation Steps

1.  **Dependencies:**
    *   Installed `rehype-slug` (`npm install --prefix ux-webapp rehype-slug`) to automatically add `id` attributes to HTML headings generated from Markdown.
    *   Installed development dependencies for creating remark plugins (`npm install --save-dev --prefix ux-webapp unified mdast unist-util-visit mdast-util-to-string`).

2.  **Heading Extraction Plugin (`src/lib/remark-extract-headings.ts`):**
    *   Created a custom `remark` plugin using `unist-util-visit` and `mdast-util-to-string`.
    *   This plugin traverses the Markdown AST, identifies `heading` nodes, extracts their text content and depth, generates a basic slug, and stores this `HeadingData` ({ text, depth, slug }).
    *   The plugin accepts an `onHeadingsExtracted` callback function via its options.

3.  **TOC Component (`src/components/TableOfContents.tsx`):**
    *   Created a new React functional component.
    *   Accepts an array of `HeadingData` as a prop.
    *   Renders a styled vertical list (using MUI `List`, `ListItem`, `ListItemButton`, `ListItemText`).
    *   Each list item is an anchor (`<a>`) tag with an `href` pointing to the corresponding heading slug (`#heading-slug`).
    *   Applies indentation based on heading depth (`sx={{ pl: (heading.depth - 1) * 2 }}`).
    *   Includes an optional `onLinkClick` callback prop (used to close the mobile drawer).

4.  **Markdown Renderer Modification (`src/components/MarkdownRenderer.tsx`):**
    *   Updated to import and use `rehype-slug` in the `rehypePlugins` prop of `<ReactMarkdown>`.
    *   Updated to import and use the custom `remarkExtractHeadings` plugin in the `remarkPlugins` prop.
    *   Added an `onHeadingsExtracted` prop to receive the callback function from the parent.
    *   **Initial Issue Fix:** Implemented `useRef` to store headings extracted by the plugin during render and a `useEffect` hook (dependent on `content`, `loading`) to call the `onHeadingsExtracted` prop *after* the render cycle, preventing the "Maximum update depth exceeded" error.
    *   **TypeScript Workaround:** Cast the remark plugin tuple `[remarkExtractHeadings, { ... }]` to `any` to bypass persistent type errors related to `PluggableList`.

5.  **Parent Component Integration (`src/components/TabbedReportView.tsx`):**
    *   Added state variables: `headings` (to store `HeadingData[]`) and `mobileTocOpen` (boolean for drawer visibility).
    *   Implemented `handleHeadingsExtracted` callback function (using `useCallback`) to receive headings from `MarkdownRenderer` and update the `headings` state. Added a check to only update state if headings actually changed.
    *   Modified `handleTabChange` to clear the `headings` state when navigating away from Markdown tabs (0 and 1).
    *   Added functions `toggleMobileToc` and `closeMobileToc` to manage the `mobileTocOpen` state.
    *   Implemented responsive layout:
        *   Used `useMediaQuery` to detect mobile screens (`isMobile`).
        *   **Desktop:** Conditionally renders the `<TableOfContents>` component within a `Box` positioned to the right of the main content area when `!isMobile`, `showTocArea` is true, and `headings.length > 0`. Applied sticky positioning and vertical scrolling.
        *   **Mobile:** Conditionally renders an `IconButton` with a `MenuIcon` in the `AppBar` when `isMobile`, `showTocArea` is true, and `headings.length > 0`. This button toggles the `mobileTocOpen` state.
        *   Added an MUI `Drawer` component that is conditionally rendered based on `mobileTocOpen`. It displays the `<TableOfContents>` component and passes the `closeMobileToc` function to its `onLinkClick` prop.
    *   **Layout Attempt:** Initially used MUI `Grid` for layout, but encountered persistent TypeScript errors regarding `item`, `xs`, and `md` props. Replaced the `Grid` structure with `Box` components using Flexbox properties (`display: 'flex'`, `flexGrow: 1`, `maxWidth`, `width`) to achieve the two-column layout.

## Challenges Encountered & Solutions Applied

1.  **App Freeze (Infinite Render Loop):**
    *   **Symptom:** App became unresponsive, especially when switching tabs. Console showed "Maximum update depth exceeded" errors.
    *   **Cause:** The `remarkExtractHeadings` plugin called the `onHeadingsExtracted` callback during the `ReactMarkdown` render cycle. This callback updated state in the parent (`TabbedReportView`), triggering a re-render, which ran the plugin again, creating an infinite loop.
    *   **Solution:** Modified `MarkdownRenderer` to use `useRef` to store headings during render and a `useEffect` hook to call the `onHeadingsExtracted` prop (updating parent state) only *after* the render completes.

2.  **MUI Grid TypeScript Errors:**
    *   **Symptom:** Persistent TypeScript errors complaining that `item`, `xs`, and `md` props did not exist on the `Grid` component, despite attempting standard MUI v5 syntax.
    *   **Cause:** Unclear, potentially a version conflict, incorrect type definitions, or subtle syntax issue.
    *   **Attempted Solutions:** Tried various combinations of adding/removing `item`, `xs`, `md` props based on error messages and documentation.
    *   **Final Solution (Workaround):** Replaced the `Grid` layout for the content/TOC columns with `Box` components using Flexbox styling. This resolved the type errors but required manual width/flex calculations.

3.  **`react-markdown` Plugin Type Errors:**
    *   **Symptom:** TypeScript errors when defining the `remarkPlugins` array containing the custom plugin with options, complaining about type mismatches with `Pluggable[]` or `PluggableList`.
    *   **Cause:** Complex generic types used by `react-markdown` and `unified` sometimes lead to inference issues.
    *   **Attempted Solutions:** Tried explicit typing with `PluggableList` (import path was incorrect).
    *   **Final Solution (Workaround):** Cast the plugin tuple `[remarkExtractHeadings, { ... }]` to `any` within the `remarkPluginsWithOptions` array definition in `MarkdownRenderer.tsx`.

## Current Challenge

*   **TOC Not Visible:** Despite the implementation and fixes, the TOC sidebar (on desktop) and the mobile toggle button are not appearing in the UI, as confirmed by user screenshots. *(Note: This was resolved by fixing the data flow and debouncing state updates)*

## Proposed Next Steps (Debugging)

1.  **Add Console Logging:** Insert `console.log` statements in `TabbedReportView.tsx`:
    *   Inside `handleHeadingsExtracted` to verify if headings data is being received from `MarkdownRenderer`.
    *   Just before the main `return` statement to log the values of `isMobile`, `showTocArea`, and `headings.length` to check the conditions controlling the TOC's visibility.
2.  **Analyze Logs:** Run the application, navigate to the relevant tabs, and inspect the browser's developer console to see the logged values.
3.  **Adjust Logic/Layout:** Based on the log output, adjust the conditional rendering logic or the Flexbox layout properties in `TabbedReportView.tsx` to ensure the TOC components are rendered correctly. For example, if `headings.length` is always 0, the issue lies in the data flow from the renderer; if the conditions are met but it's still not visible, the layout styles need adjustment. *(Note: This debugging led to fixes involving debouncing and ensuring correct state updates)*

## Deployment Errors & Troubleshooting (Related to TOC Implementation)

While the TOC feature was implemented locally, deploying the `ux-webapp` to Netlify consistently failed due to TypeScript build errors, specifically related to resolving the custom `remark-extract-headings.ts` module.

**Key Issue:**

*   The build command (`npm run build`, which includes `tsc -b`) failed with errors like `TS2307: Cannot find module '../lib/remark-extract-headings'` (or variations like `./../lib/...` or `lib/...`) originating from the components importing the module (`MarkdownRenderer.tsx`, `TabbedReportView.tsx`, `TableOfContents.tsx`).
*   This occurred despite confirming the file exists at `ux-webapp/src/lib/remark-extract-headings.ts` and the importing components are in `ux-webapp/src/components/`.

**Troubleshooting Steps Attempted (Unsuccessful):**

1.  **Explicit File Extension:** Added `.ts` to the import paths (`../lib/remark-extract-headings.ts`). Build still failed.
2.  **Path Aliases:**
    *   Configured `@/` alias in `tsconfig.app.json` (`baseUrl`, `paths`).
    *   Updated imports to use `@/lib/remark-extract-headings.ts`.
    *   Configured the same alias in `vite.config.ts`.
    *   Result: Build still failed, initially with the `tsc -b` error, and later with Vite itself failing to resolve the alias path (`[vite:load-fallback] Could not load ...`).
3.  **Reverted Aliases & Corrected Relative Path:**
    *   Removed alias configurations from `tsconfig.app.json` and `vite.config.ts`.
    *   Corrected import paths to the accurate relative path: `../lib/remark-extract-headings` (since `lib` is inside `src`, one level up from `components`).
    *   Build still failed with the `TS2307` error.
4.  **Adjusted `tsconfig.app.json`:**
    *   Tried explicitly adding `"lib"` to the `"include"` array and setting `"rootDir": "."`. Build still failed.
    *   Tried simplifying back to just `"include": ["src"]` and removing `"rootDir"`. Build still failed.

**Potential Next Steps / Ideas:**

*   **Move the Module:** Relocate `remark-extract-headings.ts` from `src/lib/` directly into `src/components/` and update imports to use `./remark-extract-headings`. This avoids the `../` directory traversal which might be problematic for `tsc -b` in the build environment.
*   **Simplify `tsconfig.json`:** Remove the project references (`references` array) in the root `ux-webapp/tsconfig.json` and consolidate necessary compiler options into a single config file to see if project references are interfering with path resolution during the `tsc -b` step.
*   **Investigate `tsc -b` Behavior:** Research potential issues or known limitations with `tsc -b` (TypeScript's project reference build) regarding relative path resolution, especially in containerized build environments like Netlify's.
*   **Move the Module:** Relocate `remark-extract-headings.ts` from `src/lib/` directly into `src/components/` and update imports to use `./remark-extract-headings`. This avoids the `../` directory traversal which might be problematic for `tsc -b` in the build environment. **(Implemented & Fixed the Netlify build)**
*   **Simplify `tsconfig.json`:** Remove the project references (`references` array) in the root `ux-webapp/tsconfig.json` and consolidate necessary compiler options into a single config file to see if project references are interfering with path resolution during the `tsc -b` step.
*   **Investigate `tsc -b` Behavior:** Research potential issues or known limitations with `tsc -b` (TypeScript's project reference build) regarding relative path resolution, especially in containerized build environments like Netlify's.
*   **Alternative Build Command:** Experiment with different build commands in `package.json`, perhaps using only `vite build` if Vite's type checking is sufficient, or exploring other TypeScript compilation options.

## Status: COMPLETE (2025-04-23)

The dynamic TOC feature is implemented, and the Netlify build errors related to the `remark-extract-headings` plugin have been resolved by moving the plugin file to the `components` directory and updating import paths.
