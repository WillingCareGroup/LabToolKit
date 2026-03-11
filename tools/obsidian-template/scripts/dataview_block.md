```dataview
 TABLE WITHOUT ID 
  Name AS "Experiment Name"
 FROM #ArchivedExperiments
 WHERE contains(file.name, "<% await tp.file.title%>")
```

```dataview
TABLE WITHOUT ID
  file.cday AS "Time", Code AS "Note"
 FROM #DailyEntries
 WHERE contains(file.outlinks, this.file.link)
 SORT file.ctime ASC
```
