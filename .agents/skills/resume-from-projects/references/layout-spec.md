# Resume layout spec

`scripts/build_resume.py` implements this spec. Read it when you change the script, when the user asks for a layout change, or when the render looks wrong.

## Page

| Property | Value |
|---|---|
| Pages | Exactly one. Never two. |
| Paper | US Letter (8.5 x 11 in) for users in the US, Canada, Mexico, Philippines. A4 (8.27 x 11.69 in) for everyone else. Ask during intake. If the user skips, infer from the location they gave, otherwise from the system locale, otherwise A4. |
| Margins | 0.7 in all sides at the default level. Allowed range 0.6 to 0.75 in. |
| Orientation | Portrait |
| Columns | One. No text boxes, no tables for layout, no frames. |
| Header and footer | Empty. Put nothing in them. |

## Type

| Element | Font | Size | Weight and colour |
|---|---|---|---|
| Name | Calibri | 21 pt | Bold, accent colour |
| Contact line | Calibri | 10 pt | Regular, body colour, links in accent colour |
| Section heading | Calibri | 11 pt | Bold, ALL CAPS, accent colour, 0.5 pt bottom rule in accent colour |
| Project or job title line | Calibri | 10.5 pt | Bold, body colour |
| Body, bullets, skills | Calibri | 10.5 pt default, 10 pt at compact levels | Regular |
| Descriptions and stack line | Calibri | same as body | Italic for the one-line description, regular for the stack line |

- One font family for the whole document. Calibri by default. Arial if the user asks. In the PDF, LibreOffice substitutes Carlito for Calibri (metric-compatible, so line breaks match) and Liberation Sans for Arial. `scripts/check_env.py` warns if neither the real font nor its substitute is installed, because line breaks then differ between machines.
- Body text never goes below 9.5 pt. Name stays between 20 and 22 pt.
- Colours: body text `222222`. Accent `1F2A44` (dark navy) for the name, section headings, rules and links. Nothing else.
- No images, no icons, no logos, no photo, no shading, no text effects.

## Header

1. Name, left aligned, Word style `Title`.
2. One contact line, left aligned, items separated by ` | ` (a space, a vertical bar, a space). Order: email, phone, location, GitHub, LinkedIn, portfolio.
3. Only provided items appear. The separator appears between items only: no leading, trailing or doubled separators, no labels like "Email:" and no empty slots.
4. Email is a `mailto:` link. GitHub, LinkedIn and portfolio are `https://` links. Display text drops the scheme and any trailing slash (`github.com/name`). Phone and location are plain text.
5. If the user gave a target role or title, it may appear as a plain line under the name only if the user asked for it. Do not invent a title.

If the user gave no name, the header has no name line, only the contact line, and if they gave nothing at all, there is no header.

## Sections and order

1. **Summary**, only if the user supplied one or one is clearly justified by their input (target role plus skills). One or two sentences, plain prose, no bullets. Heading: `SUMMARY`.
2. **Projects**, always. Heading: `PROJECTS`.
3. **Experience**, only if supplied. Heading: `EXPERIENCE`.
4. **Skills**, always. Heading: `SKILLS`.
5. **Education**, only if supplied. Heading: `EDUCATION`.

A section with no content is omitted with its heading. If the user supplied work experience and it is substantial, they may ask to put Experience above Projects. Follow the request, otherwise keep this order.

## Entry formats

**Project entry** (3 to 6 lines):

```
Project Name                                              github.com/user/repo   <- bold name, right aligned link only if the repo is public and the user supplied it
One-line description in italic, plain words
Stack: Python, FastAPI, PostgreSQL, Docker
• Bullet (what was built, how, concrete result)
• Bullet
• Bullet (optional third)
```

- The right-aligned link uses a right tab stop at the right margin. It is optional. Omit it if there is no public URL.
- Line 2 (description) and line 3 (stack) may merge into one line, `Description. Stack: ...`, when space is tight and the merged line fits on one line.
- 2 to 3 bullets per project. With 7 or more projects use 2 bullets.

**Experience entry** (supplied by the user only):

```
Job Title, Company                                        Mon YYYY - Mon YYYY   <- bold title and company, right aligned dates
• Bullet
• Bullet
```

Use the user's exact titles, employers and dates. Add nothing. If the user gave only a title and employer with no dates, omit the dates.

**Skills** (compact, 2 to 4 lines): one line per group, label then items, in plain text.

```
Languages: Python, TypeScript, SQL
Frameworks: FastAPI, React, Express
Tools: Docker, GitHub Actions, PostgreSQL, Redis
```

- Only technologies actually seen in the selected projects, plus skills the user asked to emphasise. Order each line by how much of the evidence uses it.
- Drop a group that has fewer than two items by merging it into another group. No proficiency bars, ratings or years per skill.

**Education** (supplied only): `Degree, Institution` bold, right aligned year if given, plus one line of detail only if the user gave it.

## Spacing (default level 0)

| Item | Value |
|---|---|
| Line spacing | single, exactly 1.0 |
| After name | 2 pt |
| After contact line | 6 pt |
| Section heading, space before | 8 pt |
| Section heading, space after | 3 pt |
| Between project or job entries | 4 pt |
| Between bullets | 0 pt, with 1 pt after the last bullet in an entry |
| Bullet indent | bullet at 0.15 in, text at 0.30 in (hanging indent) |

Left aligned everywhere. Never justify.

## Fitting to one page

Work in this order and stop at the first level that fits on one page:

1. Build at level 0.
2. If it overflows, **tighten the wording**: shorten the longest bullets, merge description and stack lines, remove the weakest bullet from the lowest-ranked project, trim skills. Rebuild at level 0.
3. If it still overflows, allow `--level 1` through `--level 3`:

| Level | Body | Margins | Section space before | Entry gap |
|---|---|---|---|---|
| 0 | 10.5 pt | 0.70 in | 8 pt | 4 pt |
| 1 | 10.5 pt | 0.65 in | 6 pt | 3 pt |
| 2 | 10 pt | 0.65 in | 6 pt | 3 pt |
| 3 | 10 pt | 0.60 in | 5 pt | 2 pt |

4. If level 3 overflows, remove the lowest-ranked project (and tell the user) or cut bullets. Do not go below 10 pt in the script. 9.5 pt is the hard floor reserved for manual adjustments the user approves.

Never let content reach a second page, and never solve it by shrinking margins below 0.6 in.

## Word document requirements

- Real styles: `Title` for the name, `Heading 1` for section headings, `Normal` for body, `List Bullet` for bullets, `Hyperlink` character style for links. Override the look of those styles, not each run.
- Bullets come from the real list style (Word numbering), never typed `•` characters or tab-aligned symbols.
- Plain text order in the file matches visual order (important for ATS parsers). No text in tables, text boxes, headers or footers.
- Document properties: title `<Name> Resume`, author the user's name if given. Remove the default author string from the template.
- Language set to English (US or UK to match paper) so spell-check does not flag everything.

## Verification checklist (after converting to PDF)

1. `scripts/verify_pdf.py` reports exactly 1 page.
2. It reports the smallest font size in the PDF is at least the floor for the chosen level.
3. It reports the expected number of link annotations (one per link) and each target matches `resume.json`.
4. The agent looks at the PNG render: no clipped text at the margins, no orphaned single word on a line by itself in a bullet, no uneven gaps between entries, no overlapping tab-aligned links, no stray separator in the header, bottom margin at least 0.4 in of whitespace.
5. The extracted text order reads top to bottom: name, contact, sections in order.
