# 0004. A batch checker that runs in the browser

- Status: Proposed (built 2026-11-25)
- Date: 2026-11-25

## Context
The CLI checks one sort code and account number at a time and needs Python installed.
People cleaning a list of bank details (a finance team, a data migration) want to drop
in a spreadsheet and get results back. Bank details are sensitive financial data, so
they must not be sent to a server.

## Decision
- A **static page on GitHub Pages**. The user downloads a CSV template, fills it in, and
  opens it in the page. The file is read inside the browser tab; nothing is uploaded.
- The page runs the **real Python package in the browser with Pyodide**. The batch logic
  lives in the package (`ukbankcheck.batch`), shared with `python -m ukbankcheck check-file`,
  so the web page and the CLI give identical results.
- The deploy workflow **builds the wheel from the same commit** as the page and ships it
  alongside it (changed during the build: the plan was to install from PyPI). The page
  then always runs exactly the code CI tested, and web changes don't need a PyPI release.
- A **Content Security Policy** in the page only allows scripts and network requests to the
  page's own origin and the Pyodide CDN. This makes "your file goes nowhere" enforced by
  the browser, not just promised.
- Python runs on the **main thread, not a Web Worker**. A worker would keep the page
  responsive on huge files, but a page's CSP doesn't cover workers on GitHub Pages (which
  can't set HTTP headers), so the privacy guarantee would be weaker. Files are capped at
  200,000 rows.
- **Two modes:**
  - *Demo:* a few made-up rules and sample rows, clearly labelled, so anyone can try it
    instantly.
  - *Real:* the user downloads `valacdos.txt` and `scsubtab.txt` from Vocalink and drops
    them onto the page (we can't host them; see decision 0002).
- **Output:** the same CSV with `outcome` and `reason` columns added, plus a summary of
  how many rows were valid, invalid, not checked and foreign currency.
- **Excel damage is flagged, not fixed.** Excel drops leading zeros (08-99-99 becomes
  89999). Values that look like this are marked `needs_review` instead of being guessed at.
- **No network requests after the page loads.** The page says so, and anyone can confirm
  it in the browser's network tab.

## Alternatives considered
- **Rewrite the algorithm in JavaScript.** Lighter (no ~10 MB Pyodide download) and
  works offline, but two implementations can drift apart. Only acceptable if the same 34
  spec cases also ran against the JavaScript version in CI.
- **Hosted API (server checks the file).** Simplest page, but bank details would leave the
  user's machine. Ruled out on privacy grounds.
- **A downloadable HTML file opened from disk.** Browsers restrict pages opened from
  `file://` from loading scripts and files, and there'd be no link to share.
- **Accept .xlsx uploads.** Friendlier, but needs a spreadsheet parser in the page, and
  doesn't stop Excel's leading-zero damage. Start with CSV only.

## Consequences
- First load downloads Pyodide (~10 MB) from a CDN, so it needs internet once.
- Real mode asks users to fetch two files from Vocalink themselves: some friction, but it
  keeps the licence position from decision 0002.
