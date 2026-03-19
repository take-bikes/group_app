# CUCC Brand Identity — AI Design Cheatsheet

> このファイルをプロンプトの冒頭に貼り付けてください。
> AIがCUCCのブランドガイドラインに従ったUI/コード/コピーを生成します。

---

## Brand Essence

- **Name:** CUCC
- **Tagline:** Structure the Serendipity.
- **What:** 自動グループ分けSaaS（B2C）。人の集まりを最適なグループに瞬時に分ける。
- **Archetype:** The Creator — 混沌を整理し、偶然に意味を与える設計者。
- **Positioning:** Apple/Stripe的プレミアムミニマル × Notion/Slack的モダンテック

---

## Voice Matrix

| Trait | 意味 |
|-------|------|
| Confident, not arrogant | 明確に語るが、押しつけない |
| Warm, not casual | 親しみはあるが、なれなれしくない |
| Smart, not complex | 知的だが、難解にしない |
| Playful, not frivolous | 遊び心はあるが、軽薄でない |

**コピーの原則:** 短い文。能動態。専門用語を避ける。ユーザーを主語にする。

---

## Color System

### Primary（60:30:10 ルール）

| Role | Name | HEX | RGB | Usage |
|------|------|-----|-----|-------|
| Surface 60% | Warm Parchment | `#F2F1ED` | 242, 241, 237 | ページ背景、余白 |
| Primary 30% | Deep Midnight | `#1A1A2E` | 26, 26, 46 | テキスト、ヘッダー、サイドバー |
| Accent 10% | Electric Indigo | `#5B5FEF` | 91, 95, 239 | CTA、リンク、アクティブ状態 |

### Secondary & Neutral

| Name | HEX | Usage |
|------|-----|-------|
| Accent Light | `#8B8EF5` | Hover states, subtle highlights |
| Accent Muted | `#3D4076` | Secondary buttons, tags |
| Ink Black | `#0A0A0A` | Body text, high contrast |
| Dark Gray | `#4A4A45` | Secondary text |
| Mid Gray | `#9B9B93` | Placeholders, disabled states |
| Warm Gray | `#E8E6E1` | Borders, dividers |
| Off White | `#F7F7F5` | Alt backgrounds |
| Pure White | `#FFFFFF` | Cards, modals, inputs |

### カラー使用ルール
- 背景は `#F2F1ED` または `#FFFFFF`。純白より温かみのあるParchmentを優先。
- テキストは `#0A0A0A`（本文）または `#4A4A45`（補足）。
- リンク・CTAボタンは `#5B5FEF`。Hover時は `#8B8EF5`。
- ダークUIが必要な場合は `#1A1A2E` を背景に、テキストは `#FFFFFF`。
- グラデーションを使う場合は `#5B5FEF` → `#1A1A2E` 方向のみ。

---

## Typography

| Level | Font | Size | Weight | Usage |
|-------|------|------|--------|-------|
| H1 | Inter | 48px | Bold (700) | Hero headings |
| H2 | Inter | 32px | Semibold (600) | Section titles |
| H3 | Inter | 24px | Semibold (600) | Subsection titles |
| Body | Inter | 16px | Regular (400) | Paragraph text |
| Caption | Inter | 13px | Regular (400) | Labels, metadata |
| Overline | Inter | 11px | Medium (500), tracking +1.5px | Tags, categories |

### タイポグラフィルール
- フォントファミリー: `Inter` のみ。Fallback: `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
- 行間: 本文 1.6、見出し 1.2
- 段落間スペース: 本文フォントサイズの 1.5 倍
- 見出しは `#1A1A2E`、本文は `#0A0A0A`、補足は `#4A4A45`

---

## Spacing & Layout

- **Grid:** 8px ベース。すべての間隔を 8 の倍数で指定。
- **Border radius:** 12px（カード、ボタン、入力欄）。小要素は 8px。
- **Shadow:** `0 1px 3px rgba(26,26,46,0.06), 0 8px 32px rgba(26,26,46,0.08)`
- **Container max-width:** 1200px。左右パディング 24px（モバイル 16px）。
- **Section間余白:** 80px〜120px。

---

## Components Style Guide

### Buttons
- **Primary:** bg `#5B5FEF`, text `#FFFFFF`, radius `12px`, padding `12px 24px`, font-weight `600`
- **Primary Hover:** bg `#8B8EF5`
- **Secondary:** bg `transparent`, border `1.5px solid #5B5FEF`, text `#5B5FEF`
- **Ghost:** bg `transparent`, text `#4A4A45`, hover bg `#F2F1ED`

### Cards
- bg `#FFFFFF`, border `1px solid #E8E6E1`, radius `12px`, shadow（上記参照）, padding `24px`

### Inputs
- bg `#FFFFFF`, border `1px solid #E8E6E1`, radius `8px`, padding `12px 16px`
- Focus: border `#5B5FEF`, shadow `0 0 0 3px rgba(91,95,239,0.12)`

### Navigation
- サイドバー: bg `#1A1A2E`, text `#9B9B93`, active text `#FFFFFF`, active indicator `#5B5FEF`（左2pxバー）
- ヘッダー: bg `#FFFFFF`, border-bottom `1px solid #E8E6E1`

---

## Imagery Rules

- **写真:** 自然光、ソフトライティング。彩度やや抑えめ。人物は自然体。
- **イラスト:** 幾何学的・抽象的。ブランドカラーパレット内。2pxストローク。
- **UIスクリーンショット:** 12px角丸、shadow付き、Warm Parchment背景上に配置。
- **アイコン:** Lucide Icons推奨。1.5px stroke、24×24px基準。

---

## Do's & Don'ts

**Do:**
- 承認カラーパレットのみ使用
- Inter フォントファミリーで統一
- 8px グリッドに揃える
- 60:30:10 の配色比率を守る
- 余白を十分に取る（ミニマルに）

**Don't:**
- ロゴの色・比率を変更
- 承認外フォントを使用
- ドロップシャドウやグラデーションを過度に使用
- 低解像度画像の使用
- テキストの可読性を犠牲にしたレイアウト

---

## CSS Variables（コピペ用）

```css
:root {
  /* Primary */
  --color-surface: #F2F1ED;
  --color-primary: #1A1A2E;
  --color-accent: #5B5FEF;

  /* Secondary */
  --color-accent-light: #8B8EF5;
  --color-accent-muted: #3D4076;

  /* Neutral */
  --color-ink: #0A0A0A;
  --color-text-secondary: #4A4A45;
  --color-text-muted: #9B9B93;
  --color-border: #E8E6E1;
  --color-bg-alt: #F7F7F5;
  --color-white: #FFFFFF;

  /* Typography */
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-size-h1: 48px;
  --font-size-h2: 32px;
  --font-size-h3: 24px;
  --font-size-body: 16px;
  --font-size-caption: 13px;
  --font-size-overline: 11px;
  --line-height-heading: 1.2;
  --line-height-body: 1.6;

  /* Spacing */
  --radius-lg: 12px;
  --radius-sm: 8px;
  --shadow-card: 0 1px 3px rgba(26,26,46,0.06), 0 8px 32px rgba(26,26,46,0.08);
  --container-max: 1200px;
}
```

---

## Tailwind Config（コピペ用）

```js
// tailwind.config.js に追加
{
  theme: {
    extend: {
      colors: {
        surface: '#F2F1ED',
        primary: '#1A1A2E',
        accent: { DEFAULT: '#5B5FEF', light: '#8B8EF5', muted: '#3D4076' },
        ink: '#0A0A0A',
        'gray-dark': '#4A4A45',
        'gray-mid': '#9B9B93',
        'gray-warm': '#E8E6E1',
        'off-white': '#F7F7F5',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
      borderRadius: {
        card: '12px',
      },
      boxShadow: {
        card: '0 1px 3px rgba(26,26,46,0.06), 0 8px 32px rgba(26,26,46,0.08)',
      },
    },
  },
}
```
