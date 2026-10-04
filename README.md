# Markerpen

## Marker Fork
Python3 by default, plus command collections, tags and choice placeholders. Tuned for pentest workflows but works for any command set.

![marker](https://cloud.githubusercontent.com/assets/2557967/14209204/d99db934-f81a-11e5-910c-9d34ac155d18.gif)

Markerpen is a command palette for the terminal. It lets you bookmark commands (or commands templates) and easily retreive them with the help of a real-time fuzzy matcher.

It's also shipped with many commands common usage(Thanks to [tldr](https://github.com/tldr-pages/tldr)).
  
## Features:
- A UI selector that lets you easily select the desired command if more than one command is matched.
- Fuzzy matching (through commands and their descriptions).
- Command template: You can bookmark commands with place-holders and place the cursor at those place-holders using a keyboard shortcut.
- Portability across supported shells: you can use bookmarked commands in both Bash and Zshell.
- New in Fork: Choice placeholders: `{{a|b|c}}` opens an arrow-key picker to pick command variations; add optional arguments using `|` like  `{{--optional|}}`.
- New in Fork: Collections and tags: file commands into `collections/*.txt` and filter them with `@collection`/`#tag` sigils in the search box. e.g `@web` `#idea`

## Usage
- `Ctrl-space`: search for commands that match the current written string in the command-line.
- `Ctrl-k` (or `marker mark`): Bookmark a command.
- `Ctrl+f` (CHANGED BINDING): place the cursor at the next placeholder(shadows forward-char
  - `{{anything}}`: hint placeholder, removed and the cursor parked there(as upstream).
  - `{{requirements.txt|requests}}`: choice placeholder, an arrow-key picker fills the picked option(up/down or tab, Enter, Esc).
  - `{{-it|}}`: optional part, pick `<exclude>` to drop it cleanly(no double space left behind).
  - `{{[b|k|m|g]}}`: bracket alternations become choices too.
  - `{{ps aux \| grep node}}`: escaped pipes are literal values, filled as-is.
- `marker remove`: remove a bookmark(type `@collection`/`#tag` in the remove UI to scope the removal).

### Collections and tags
```
marker mark --command='nikto -h {{url}}' --alias='web scanner' --collection=web --tags=win
marker mark --command='nmap -sV {{target}}' --alias='version scan' --tags=idea
```
- Files live under `collections/*.txt` in the marker data dir(`~/.config/ezsh/marker` by default), one `cmd##alias##tags` per line; lines without tags keep working.
- In the search box: `@web` looks only in that collection, `#win`/`#idea` filter custom commands by tag(any number combinable, e.g. `@web #win nmap`); without a sigil the global search behaves exactly as before.
- Re-marking a command with the same cmd+alias updates its tags.

### Other fork changes
- `marker mark --alias/--collection/--tags` work non-interactively(the `--alias` flag was dead upstream).
- Malformed lines in data files are skipped with a warning instead of silently dropping the whole file.
- The default next-placeholder key now is `Ctr+f`(no conflict with backspace, tmux or screen).

You can customize key binding using environment variables, respectively with ```MARKER_KEY_GET```, ```MARKER_KEY_MARK``` and ```MARKER_KEY_NEXT_PLACEHOLDER```.

## Requirements
- python (3.0+)
- Bash-4.3+ or Zshell.
- Linux Or OSX

## Installation

`git clone --depth=1 https://github.com/jotyGill/marker ~/.marker && ~/.marker/install.py`

## License
[MIT](LICENSE)
