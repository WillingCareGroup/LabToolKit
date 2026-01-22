<%*
const template = await tp.file.find_tfile("MileStone template");
const noteName = tp.date.now("MMM YYYY");
const folderPath = "LabNote/MileStones";
await tp.file.create_new(template, noteName, false, folderPath);
%>


