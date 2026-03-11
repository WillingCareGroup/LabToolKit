<%*
const date = tp.date.now("YYMMDD");
const folder = "LabNote/Experiments";
const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

const files = app.vault.getMarkdownFiles().filter(f => f.path.startsWith(folder + "/"));
let index = 0;
for (const f of files) {
  if (f.basename.startsWith("E" + date)) index++;
}
const suffix = letters[index] || letters[letters.length - 1];
const autoCode = `E${date}${suffix}`;

let requestedName = await tp.system.prompt(
  "Experiment file name (append digits and/or add name after a space):",
  autoCode
);
if (!requestedName) requestedName = autoCode;
requestedName = requestedName.trim();

if (!requestedName.startsWith(autoCode)) {
  requestedName = requestedName.length ? `${autoCode} ${requestedName}` : autoCode;
}

const codeOnly = requestedName.split(/\s+/)[0];
const safeName = requestedName.replace(/[\\\/:\*\?"<>\|]/g, "-").trim();
const notepath = `${folder}/${safeName}`;
const templateFile = await tp.file.find_tfile("Experiment template");
const created = await tp.file.create_new(templateFile, notepath, false);

let content = await app.vault.read(created);
if (/(^---\s*$[\s\S]*?^---\s*$)/m.test(content)) {
  if ((/^Code:\s*/m).test(content)) {
    content = content.replace(/^Code:\s*.*$/m, `Code: ${codeOnly}`);
  } else {
    content = content.replace(
      /^---\s*$([\s\S]*?)^---\s*$/m,
      (m, fm) => `---\n${fm}Code: ${codeOnly}\n---`
    );
  }
} else {
  content = `---\nCode: ${codeOnly}\n---\n\n` + content;
}

await app.vault.modify(created, content);
tR += `![[${created.basename}]]`;
%>
