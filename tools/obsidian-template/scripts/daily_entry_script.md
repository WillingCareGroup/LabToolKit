<%*
const DAILY_FOLDER = "LabNote/Daily Entries";
const EXP_FOLDER = "LabNote/Experiments";
const ONGOING_MARKERS = ["#OnGoingExperiments", "#OngoingExperiments"];

const todayName = window.moment().format("YYYY-MM-DD");
const dailyPath = `${DAILY_FOLDER}/${todayName}`;
const existing = app.vault.getAbstractFileByPath(dailyPath);

if (existing) {
  const leaf = app.workspace.getLeaf(true);
  await leaf.openFile(existing);

  const fe = app.workspace.getLeavesOfType("file-explorer")?.[0];
  if (fe?.view?.revealInFolder) fe.view.revealInFolder(existing);

  app.workspace.getMostRecentLeaf()?.detach();
  tR = "";
  return;
}

await tp.file.rename(todayName);
await tp.file.move(dailyPath);

const expFiles = app.vault.getMarkdownFiles().filter(f => f.path.startsWith(EXP_FOLDER));
let items = [];

for (const f of expFiles) {
  const content = await app.vault.cachedRead(f);
  if (!ONGOING_MARKERS.some(tag => content.includes(tag))) continue;

  const cache = app.metadataCache.getFileCache(f);
  const fm = cache?.frontmatter ?? {};
  const basename = f.basename;
  const fallbackCode = basename.split(/\s+/)[0];
  const code = (fm.Code ?? fm.code ?? fallbackCode).toString().trim();
  items.push({ code, basename });
}

items.sort((a, b) => a.code.localeCompare(b.code));

const blocks = items.map(({ code, basename }) =>
`### [[${basename}]]
${code}:: 
`).join("\n");

const now = window.moment().format("YYYY-MM-DD HH:mm");

tR =
`---
modification date: ${now}
tags:
  - DailyEntries
---

\`\`\`dataview
TABLE WITHOUT ID
  file.name AS "OnGoingProject", Name AS "Name", Project AS "Project"
FROM #OnGoingExperiments OR #OngoingExperiments
WHERE file.name != "Daily Entry Script"
  AND file.name != "Experiment template"
SORT file.name ASC
\`\`\`

${blocks}

![[Scheduler#TODO]]

## Daily Log
- 
`;
%>

