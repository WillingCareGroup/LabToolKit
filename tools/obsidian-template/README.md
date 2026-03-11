# Obsidian Lab Notebook Template

An Obsidian lab notebook system built around three note types:

- Daily entries
- Experiment records
- Monthly milestones

It uses the Obsidian `Templater` and `Dataview` plugins to create notes, keep experiment codes consistent, and surface linked work inside your daily log and experiment history.

## What is included

### Templates

- `templates/daily_entry_template.md`
- `templates/experiment_template.md`
- `templates/milestone_template.md`

### Templater scripts

- `scripts/daily_entry_script.md`
- `scripts/experiment_script.md`
- `scripts/milestone_script.md`
- `scripts/dataview_block.md`

## Requirements

- Obsidian
- Templater plugin
- Dataview plugin

## Expected vault layout

The scripts assume this folder structure:

```text
LabNote/
  Daily Entries/
  Experiments/
  MileStones/
```

If your vault uses different folder names, update the paths inside the Templater scripts before using the template.

## Installation

1. Copy the files in `templates/` into your Obsidian Templates folder.
2. Copy the files in `scripts/` into your Templater scripts folder, or another folder you call from Templater.
3. Confirm that your vault contains the `LabNote/Daily Entries`, `LabNote/Experiments`, and `LabNote/MileStones` folders.
4. In Obsidian, enable both `Templater` and `Dataview`.
5. Configure your commands or hotkeys to run the three scripts.

## Workflow

### Daily entry script

`scripts/daily_entry_script.md` does the following:

1. Opens today's note if it already exists.
2. Otherwise renames and moves the current scratch note into `LabNote/Daily Entries/YYYY-MM-DD`.
3. Lists all ongoing experiments in a Dataview table.
4. Appends a block for each ongoing experiment so you can write per-experiment updates directly in the daily note.

### Experiment script

`scripts/experiment_script.md` does the following:

1. Generates the next daily experiment code in the format `EYYMMDDA`, `EYYMMDDB`, and so on.
2. Prompts you for an optional longer title while preserving the generated code as the first token.
3. Creates a new experiment note under `LabNote/Experiments`.
4. Writes the short code into frontmatter as `Code`.

New experiment notes include:

- `Code`
- `Name`
- `Project`
- `Cells`
- `Status`
- `tags`

### Milestone script

`scripts/milestone_script.md` renames the current note to the current month, moves it to `LabNote/MileStones/`, and injects the milestone template content.

## Note linking model

- Daily notes use the `DailyEntries` tag.
- New experiment notes use the `OnGoingExperiments` tag.
- Experiment history is resolved from links in daily notes, not from title text matching.
- The daily note templates and scripts also search for the legacy `#OngoingExperiments` tag for backward compatibility with older notes.

This keeps older experiment notes visible without requiring an immediate vault-wide migration.

## Files

### `templates/experiment_template.md`

The experiment template stores metadata in frontmatter and includes a Dataview block showing daily notes that link back to the current experiment.

### `templates/daily_entry_template.md`

The daily template shows ongoing experiments and creates inline sections for logging work against each experiment code.

### `templates/milestone_template.md`

The milestone template stores a simple monthly checkpoint note with the previous milestone reference and current goal.

### `scripts/dataview_block.md`

This helper block can be embedded in an experiment note to show archived experiments and linked daily-note history.

## Tag compatibility

Tags are case sensitive in Obsidian and Dataview.

This template currently uses:

- `#OnGoingExperiments` for new experiment notes
- `#DailyEntries` for daily notes

For backward compatibility, the daily note views and scripts also recognize:

- `#OngoingExperiments`

## Customization

You will likely want to customize:

- Folder names
- Frontmatter fields such as `Project`, `Cells`, or `Status`
- The experiment code format
- The Dataview columns shown in daily notes
- The `Scheduler#TODO` embed target

## Known assumptions

- The scripts are written for a single Obsidian vault and fixed folder names.
- The experiment code generator uses the count of existing notes for the same day to derive the next suffix letter.
- The current implementation assumes no more than 26 new experiment prefixes are needed on the same day before you customize the naming scheme.
