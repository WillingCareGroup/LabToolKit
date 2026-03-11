---
modification date: <% tp.file.last_modified_date()%>
tags:
  - DailyEntries
---
```dataview
Table WITHOUT ID
	file.name AS "OnGoingProject", Name AS "Name", Project AS "Project"
FROM #OnGoingExperiments 
WHERE !contains(file.name, "Experiment template") 
SORT file.name ASC
```


<%*
const tag = "#OnGoingExperiments";
const folder = "LabNote/Experiments";
const files = app.vault.getMarkdownFiles().filter(file => file.path.startsWith(folder));
let notesWithTag = [];

for (const file of files) {
  const content = await app.vault.cachedRead(file);
  if (content.includes(tag)) {
    notesWithTag.push(file.basename);
  }
}

notesWithTag.sort();

let notesList = "#DailyEntries\n";
notesWithTag.forEach(note => {
  notesList += `${note}::[${note}] \n`;
});

tR += notesList;
%>


![[Scheduler#TODO]]
