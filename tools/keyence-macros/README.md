# Keyence Imaging Macros

Keyence macro files (`.mrf`) used to automate HTS imaging workflows when
autofocus is unreliable. These macros encode stage positions, plate layouts,
and capture routines for common formats.

## Contents

- 24well macro.mrf
- 48well 4X macro.mrf
- 48well 10X macro.mrf
- 48well macro.mrf
- 96well 4X macro.mrf
- 96well 10X macro.mrf
- 96 Stich unfinished.mrf
- empty xy setup.mrf
- iBidi 96Square HSCmds1.mrf
- iBidi 96Square HSCmds1 2per.mrf
- iBidi 96Square HSCmds1 no move.mrf
- iBidi 96Square HSCmds1 xy.mrf
- iBidi 96Square HSCmds1 xy capture.mrf
- iBidi 96Square HSCmds1 xy setup.mrf

## Usage

1) Open the Keyence imaging software on the acquisition workstation.
2) Import or load the `.mrf` file that matches your plate and objective.
3) Adjust stage origin and any plate-specific offsets.
4) Run the macro and monitor the first few wells to confirm focus and framing.

## Notes

- These files are hardware- and setup-specific. Validate on a test plate first.
- If your system uses different plate definitions or objectives, duplicate and
  edit the macro in the Keyence macro editor.
