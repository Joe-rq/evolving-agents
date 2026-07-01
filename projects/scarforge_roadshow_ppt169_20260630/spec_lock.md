## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## mode
- mode: narrative

## visual_style
- visual_style: soft-rounded

## colors
- bg: #F4F9FF
- secondary_bg: #EAF3FF
- panel: #FFFFFF
- primary: #1D70D6
- accent: #31B67A
- green: #15956B
- green_dark: #0B5A43
- green_tint: #F4FFF9
- secondary_accent: #E47B2C
- purple: #7F5AF0
- purple_tint: #F4F0FF
- red: #D94B4B
- red_tint: #FFF7F6
- warm_tint: #FFF8F4
- text: #122033
- text_secondary: #52657D
- text_tertiary: #7B8DA3
- border: #C9D9EA

## typography
- font_family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif
- title_family: SimHei, "Microsoft YaHei", sans-serif
- emphasis_family: SimHei, "Microsoft YaHei", sans-serif
- code_family: Consolas, "Courier New", monospace
- body: 32
- title: 56
- subtitle: 44
- subheading: 40
- cover_title: 98
- cover_hero: 176
- card_desc: 19
- annotation: 24
- code: 20
- footnote: 16

## icons
- library: tabler-outline
- stroke_width: 2
- inventory: bug, database, adjustments, focus-2, search, schema, git-branch, sparkles, route, file-search, stack-2, code, robot, school, telescope, circle-check, alert-triangle, arrow-right, arrow-loop-right, puzzle

## page_rhythm
- P01: anchor
- P02: breathing
- P03: dense
- P04: dense
- P05: dense
- P06: dense
- P07: dense
- P08: dense
- P09: dense
- P10: breathing

## page_charts
- P04: vertical_list
- P05: butterfly_chart
- P07: layered_architecture
- P08: icon_grid
- P09: pros_cons_chart

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
- HTML named entities in text (`&nbsp;`, `&mdash;`, `&copy;`, `&ndash;`, `&reg;`, `&hellip;`, `&bull;` …) — write as raw Unicode (`—`, `©`, `→`, NBSP, etc.); XML reserved chars `& < > " '` must be escaped as `&amp; &lt; &gt; &quot; &apos;`
