# Exaktiv brand package v1.0

Version 1.0 · 18 November 2026 · Written in ASD-STE100
This folder is the single source for the Exaktiv identity: logo, colour, type, tokens and components.
It replaces the retired Personal Design System. Do not use teal, Inter, Lora, JetBrains Mono or the chevron mark.
Open `guidelines/index.html` in a browser to see every rule and component in use.

## The idea in one line

No value without a source. The brand cites itself: every claim has a cobalt footnote, every colour has one job,
and every page reads like a document that a reviewer can check.

## Folder map

| Path | Content |
|---|---|
| `guidelines/index.html` | The brand guidelines. It loads the package's own fonts, tokens and CSS, so it is also a live test. |
| `logo/svg/` | `exaktiv-mark`, `exaktiv-lockup`, `exaktiv-stacked`, `exaktiv-wordmark`, each with a `-reversed` version. `exaktiv-lockup-on-ink` and `exaktiv-lockup-on-cobalt` include their ground. The wordmark is outlined (no font needed). |
| `logo/png/` | Each SVG as PNG with a transparent ground. Marks at 256, 512 and 1024 px wide. Lockups at 600, 1200 and 2400 px wide. |
| `favicon/` | `favicon.svg`, `favicon.ico` (16, 32, 48), `favicon-16/32/48.png`, `apple-touch-icon.png` (180), `icon-192.png`, `icon-512.png`, `app-icon.svg`, `site.webmanifest`. |
| `social/og-image.png` | Open Graph image, 1200 × 630 (PRD-W §10). |
| `email/` | Email signature banners as PNG at 2x: `exaktiv-email-banner-paper@2x.png` and `-ink@2x.png` (show at 600 × 150), `-strip@2x.png` (show at 600 × 64). `email-signature.html` is a paste-ready signature block. |
| `fonts/` | Self-hosted woff2 files (Latin and Latin Extended), `fonts.css`, and the three SIL Open Font Licence texts. |
| `tokens/tokens.css` | **Source of truth** for all tokens. Raw values, role tokens, dark mode, print, reduced motion. |
| `tokens/tokens.json` | W3C design tokens format. Generated. |
| `tokens/tokens.ts` | `ex` (CSS variable references), `light` and `dark` (resolved values for canvas, charts and PDF). Generated. |
| `tokens/build_tokens.py` | Generates `tokens.json` and `tokens.ts` from `tokens.css`. |
| `tokens/check_brand.py` | Guard checks for CI: WCAG contrast of 30 text pairs, generated files current, no banned patterns. |
| `components/exaktiv.css` | Base styles and all components: buttons, links, the Trace, header, footer, cards, pillars, steps, finding card, tables, forms, notices, hero, print. |
| `icons/arrow-right.svg` | The arrow for buttons and links. The fonts have no "→" glyph, so never type the arrow character. |

## Rules that are not open for design choice

1. **Colour has a job.** Cobalt `--ex-source` = source (footnotes, citations, links, focus). Vermilion `--ex-act` = act (primary button, logo dot). Marker `--ex-evidence` = evidence (a band behind backed words only). Paper and Ink carry everything else.
2. **Role tokens only.** Components use `--ex-*` role tokens. No hex value and no `--ex-raw-*` token in a component. `check_brand.py` fails the build on both.
3. **Three faces, three jobs.** Young Serif (400 only) for the wordmark and headings. Instrument Sans (400 to 600) for body and UI. Gelasio italic for citations and notes. No monospace anywhere, also not for code and file paths.
4. **`font-synthesis: none` on every page.** Young Serif has one weight. The browser must never make a fake bold.
5. **No tabular figures in running text.** In these fonts, tabular figures also widen full stops and commas. Use `.ex-tnum` only in tables and line numbers.
6. **Headings do the work.** No uppercase kickers, tags, section numbers or small labels above a heading. Captions go below the item.
7. **Display line height 0.98 or more.** The evidence band needs the room. At a tighter line height, the band covers the line above.
8. **Square and flat.** Radius 0. Rules 1.5 px. Accent edges 6 px. No shadows, no blur, no gradients except the evidence band.
9. **One vermilion button per screen.** Text on vermilion is always Ink, never Paper.
10. **The Trace gate.** A claim gets a footnote number only when its status in the PRD-W claims register is "Ready".
11. **Logo follows the theme.** On a dark ground, use the `-reversed` file. In plain HTML with a theme button (the website), use two `<img>` elements with `.ex-logo--light` and `.ex-logo--dark`; the CSS shows one by the system setting or by `data-theme`. Without a button, `<picture>` with a `(prefers-color-scheme: dark)` source works too; in React, switch the file on the `data-theme` value.
12. **Mobile first, fluid between breakpoints.** Use the layout tokens (`--ex-gutter`, `--ex-section-y`, `--ex-hero-top`, `--ex-hero-bottom`, `--ex-card-pad`, `--ex-header-h`) for spacing that changes with the screen. Write a media query only at a breakpoint token, as a number: `min-width` = the token, `max-width` = the token minus 1 px. `check_brand.py` fails on any other width.
13. **Touch targets.** Every control is at least `--ex-target-min` (44 px) tall. Primary buttons are `--ex-control-h` (52 px).
14. **No names.** No person, employer or client names in any asset, file name or metadata (PRD-W constraint 1 to 3).

## How to load it

Static page (website, HTML report):

```html
<link rel="stylesheet" href="/brand/fonts/fonts.css">
<link rel="stylesheet" href="/brand/tokens/tokens.css">
<link rel="stylesheet" href="/brand/components/exaktiv.css">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
```

React UI (`ui/`): copy `tokens/tokens.css` and `tokens/tokens.ts` to `ui/src/tokens/`, and the fonts to `ui/public/fonts/`.
Phase EXD2 does this and adds the checks (see `PHASES.md`).

Content-Security-Policy: the button arrow is an inline SVG data URI in `exaktiv.css`.
Use `img-src 'self' data:`. Everything else is `'self'` (PRD-W §8.2).

## Responsive tokens

| Token | Value | Use |
|---|---|---|
| `--ex-bp-sm` | 480px | Large phone. Below it: footer links stack, table cells get less padding. |
| `--ex-bp-md` | 768px | Tablet. Layout grid goes from 4 to 8 columns. |
| `--ex-bp-lg` | 960px | Small laptop. Capability cards go side by side. Layout grid has 12 columns. |
| `--ex-bp-xl` | 1181px | Full navigation. Below it, the Menu button opens the navigation (when `theme.js` runs). |
| `--ex-gutter` | 16 to 24 px | Page side padding. |
| `--ex-section-y` | 48 to 80 px | Space above and below a section. |
| `--ex-hero-top`, `--ex-hero-bottom` | 48 to 96 px, 48 to 80 px | Hero padding. |
| `--ex-card-pad` | 22 to 30 px | Card padding. |
| `--ex-header-h` | 64 to 72 px | Header and Menu button height. |
| `--ex-target-min` | 44px | Smallest tap target. |
| `--ex-cols` | 4 / 8 / 12 | Columns of the `.ex-grid` layout grid. A child spans `--span` columns. |
| `--ex-size-h3`, `--ex-size-lead`, `--ex-size-body` | 22 to 26, 18 to 20, 16 to 17 px | Fluid text sizes, as display, h1 and h2 already are. |

Fluid values use `clamp()` between 320 px and 1440 px wide, so nothing jumps between breakpoints.
In TypeScript, `tokens.ts` exports `breakpoints`, `up("lg")` and `down("xl")` for `matchMedia`.
The site tests (`tests/site/test_browser.py`) check every page at 320, 390, 768, 1024, 1180, 1181 and 1440 px.

## The Trace, in markup

```html
<h1 class="ex-display">AI you can <span class="ex-mark">audit.</span><a class="ex-ref" href="#c1">1</a></h1>
...
<ol class="ex-cites">
  <li id="c1"><span class="ex-cite__n">1</span>Sample analyser output, sent with every assessment proposal.</li>
</ol>
```

## Change the tokens

1. Edit `tokens/tokens.css`.
2. Run `python3 brand/tokens/build_tokens.py`.
3. Run `python3 brand/tokens/check_brand.py`. It must pass.
4. Commit all three token files together.

## Rebuild the logo files

The logo SVGs are outlined from Young Serif, with letter spacing −0.035 em. The square is 5 grid units (40 of 68),
the cut and the leader are ¾ unit, the dot is 2 units. To change the wordmark, regenerate the outlines from
`fonts/young-serif-latin-400-normal.woff2`. Do not retype it in another font, weight or case.

## Fonts and licences

| Font | Use | Licence | Source |
|---|---|---|---|
| Young Serif | Wordmark, headings | SIL OFL 1.1 (`fonts/OFL-young-serif.txt`) | Google Fonts, via Fontsource 5.3.0 |
| Instrument Sans | Body, UI | SIL OFL 1.1 (`fonts/OFL-instrument-sans.txt`) | Google Fonts, via Fontsource 5.3.0 |
| Gelasio italic | Citations, notes | SIL OFL 1.1 (`fonts/OFL-gelasio.txt`) | Google Fonts, via Fontsource 5.3.0 |

The design canvas with the decisions (palette and font options) is a private claude.ai artifact: "Exaktiv brand system".
