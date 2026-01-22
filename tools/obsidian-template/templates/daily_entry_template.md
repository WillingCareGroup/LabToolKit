---
modification date: <% tp.file.last_modified_date()%>
---
```dataview
Table WITHOUT ID
	file.name AS "OngoingProject", Name AS "Name", Project AS "Project"
FROM #OngoingExperiments 
WHERE !contains(file.name, "Experiment template") 
SORT file.name ASC
```


<%*
// Define the tag to search for
const tag = "#OngoingExperiments";
const folder = "LabNote/Experiments"; // Specify your notes folder path
const files = app.vault.getMarkdownFiles().filter(file => file.path.startsWith(folder));
let notesWithTag = [];

// Search for notes with the specified tag within the specified folder
for (const file of files) {
  const content = await app.vault.cachedRead(file);
  if (content.includes(tag)) {
    notesWithTag.push(file.basename);
  }
}

// Sort the list of notes (optional)
notesWithTag.sort();

// Create a list of notes with the specified tag
let notesList = "#DailyEntries\n";
notesWithTag.forEach(note => {
  notesList += `${note}::[${note}] \n`;
});

// Output the list
tR += notesList;
%>


![[Scheduler#TODO]]
