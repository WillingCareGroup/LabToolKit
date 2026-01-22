<%*
// Name file to YYMMDDA-Z
const date = tp.date.now("YYMMDD");
const folder = "LabNote/Experiments"; // Specify your notes folder path
const files = app.vault.getMarkdownFiles().filter(file => file.path.startsWith(folder));
const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
let index = 0;
files.forEach(file => {
  if (file.basename.startsWith("E" + date)) {
    index++;
  }
});
const suffix = letters[index] || letters[letters.length - 1];
const filename = `E${date}${suffix}`;
const notepath = `${folder}/${filename}`;
// create note
await tp.file.create_new(await tp.file.find_tfile("Experiment template"), notepath, false);
tR += "![[" + filename + "]]";
%>