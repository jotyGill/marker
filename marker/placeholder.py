r''' Interactive {{placeholder}} filling.
    {{name}}          -> hint placeholder, removed from the line(as before)
    {{a|b|c}}         -> choice placeholder, opens an arrow-key picker
    {{-avar|}}        -> optional placeholder, pick <exclude> to drop it
                         (one adjacent space is consumed, no double space left)
    {{ps aux \| x}}   -> escaped pipes are literal values, filled as-is
'''
import re
import shutil
import sys
from . import ansi, keys, readchar

PLACEHOLDER_PATTERN = re.compile(r'\{\{.+?\}\}')
HINT = '   (up/down - enter - esc)'
EXCLUDE_LABEL = '<exclude>'

def parse_placeholder(line):
    ''' return (offset, match_length, options, has_escape) for the first placeholder, or None '''
    match = PLACEHOLDER_PATTERN.search(line)
    if not match:
        return None
    inner = match.group(0)[2:-2]
    has_escape = '\\' in inner
    if inner.startswith('[') and inner.endswith(']'):
        # {{[b|k|m|g]}} style alternation
        inner = inner[1:-1]
    options = [o.replace('\\|', '|') for o in re.split(r'(?<!\\)\|', inner)]
    return match.start(), len(match.group(0)), options, has_escape

def _visible_length(text):
    return len(re.sub(r'\x1b[^m]*m', '', text))

def _render(options, selected):
    cols = shutil.get_terminal_size().columns
    sep = '   '
    # the empty option is displayed as <exclude>(it stays '' when chosen)
    labels = [o if o != '' else EXCLUDE_LABEL for o in options]
    # per-option budget keeps the menu on a single terminal row
    # (the hint is dropped and options shrink on narrow terminals)
    budget = cols - 1 - len(sep) * (len(options) - 1)
    if budget - _visible_length(HINT) >= len(options) * 4:
        budget -= _visible_length(HINT)
        hint = ansi.grey_text(HINT)
    else:
        hint = ''
    per_option = max(1, budget // len(options))
    rendered = [
        ansi.select_text(l[:per_option]) if i == selected else l[:per_option]
        for i, l in enumerate(labels)]
    return sep.join(rendered) + hint

def _erase_menu():
    ansi.move_cursor_line_beggining()
    ansi.erase_from_cursor_to_end()

def choose(options):
    ''' draw a one-line picker, return the chosen option or None on abort '''
    selected = 0
    while True:
        _erase_menu()
        sys.stdout.write(_render(options, selected))
        ansi.flush()
        c = readchar.get_symbol()
        if c == keys.UP:
            selected = (selected - 1) % len(options)
        elif c == keys.DOWN or c == keys.TAB:
            selected = (selected + 1) % len(options)
        elif c == keys.ENTER:
            _erase_menu()
            return options[selected]
        elif c == keys.ESC or c == keys.CTRL_C:
            _erase_menu()
            return None

def run(line_file, out_file):
    ''' find the next placeholder in the line file;
        on success write "offset\nmatch_length\nchoice\n" to the out file,
        write nothing when there is no placeholder or the choice was aborted
    '''
    try:
        _run(line_file, out_file)
    except Exception as e:
        # never dump a traceback mid-keystroke: an empty out file makes the
        # shell widget a no-op, which is the graceful way to fail here
        sys.stderr.write('marker placeholder: %s\n' % e)

def _run(line_file, out_file):
    with open(line_file, 'r', encoding='utf-8') as f:
        line = f.read().rstrip('\n')
    parsed = parse_placeholder(line)
    if not parsed:
        return
    offset, length, options, has_escape = parsed
    if len(options) > 1:
        choice = choose(options)
        if choice is None:
            return
        if choice == '':
            # <exclude> chosen: drop the placeholder together with one
            # adjacent space, so no double space is left in the line
            if offset > 0 and line[offset - 1] == ' ':
                offset -= 1
                length += 1
            elif offset + length < len(line) and line[offset + length] == ' ':
                length += 1
    elif has_escape:
        choice = options[0]
    else:
        choice = ''
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write('%d\n%d\n%s\n' % (offset, length, choice))
