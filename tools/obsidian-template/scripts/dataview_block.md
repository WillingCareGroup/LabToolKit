```dataview
 TABLE WITHOUT ID 
  Name AS "Experiment Name"
 FROM #ArchivedExperiments
 WHERE contains(file.name, "<% await tp.file.title%>")
```

```dataview
 TABLE WITHOUT ID 
  file.cday AS "Time", <% await tp.file.title%> AS "Note"
 FROM #DailyEntries
 WHERE <% await tp.file.title%>
 SORT file.ctime ASC
```