---
Code: <% tp.file.title %>
Name:
Project:
creation date: <% tp.file.creation_date() %>
modification date: <% tp.file.last_modified_date()%>
Cells:
Status: ongoing
tags:
  - OnGoingExperiments
---
### Goal & AnticipatedResults

### Result

### FutureDirections

```dataview
TABLE WITHOUT ID
  file.cday AS "Time", Code AS "Note"
FROM #DailyEntries
WHERE contains(file.outlinks, this.file.link)
SORT file.ctime ASC
```
