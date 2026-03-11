<%*
const noteName = tp.date.now("MMM YYYY");
const folderPath = "LabNote/MileStones/";

await tp.file.rename(noteName);
await tp.file.move(folderPath + noteName);
tR = "";
%>

<% await tp.file.include(tp.file.find_tfile("MileStone template")) %>


