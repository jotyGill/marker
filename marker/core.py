# App logic
from __future__ import print_function
import os
import re
from . import keys
from . import readchar
from . import command
from . import renderer
from .filter import filter_commands

from sys import version_info, platform

if version_info[0] == 2:
    keyboard_input = raw_input
else:
    keyboard_input = input

def get_os():
    if platform.lower() == 'darwin':
        return 'osx'
    elif platform.lower().startswith('linux'):
        return 'linux'
    else:
        # throw is better
        return 'unknown'

def get_user_marks_path():
    return os.path.join(os.getenv('MARKER_DATA_HOME'), 'user_commands.txt')
def get_tldr_os_marks_path():
    return os.path.join(os.getenv('MARKER_HOME'), 'tldr', get_os()+'.txt')
def get_tldr_common_marks_path():
    return os.path.join(os.getenv('MARKER_HOME'), 'tldr', 'common.txt')
def get_tldr_security_marks_path():
    return os.path.join(os.getenv('MARKER_HOME'), 'tldr', 'security.txt')

COLLECTION_NAME_PATTERN = re.compile(r'^[a-z0-9_-]+$')

def get_collections_dir():
    return os.path.join(os.getenv('MARKER_DATA_HOME'), 'collections')
def get_collection_path(name):
    return os.path.join(get_collections_dir(), name + '.txt')
def get_collections():
    ''' names of the existing collections '''
    try:
        return sorted(f[:-4] for f in os.listdir(get_collections_dir()) if f.endswith('.txt'))
    except OSError:
        return []
def load_collection(name):
    return command.load(get_collection_path(name))

def parse_search(search):
    ''' split a search string into (collection, tags, query):
        "@web #win #idea nmap" -> ("web", ["win", "idea"], "nmap")
    '''
    collection, tags, words = None, [], []
    for w in (search or '').split():
        if collection is None and w.startswith('@') and len(w) > 1:
            collection = w[1:].lower()
        elif w.startswith('#') and len(w) > 1:
            tags.append(w[1:].lower())
        else:
            words.append(w)
    return collection, tags, ' '.join(words)

def mark_command(cmd_string, alias, collection=None, tags=None):
    ''' Adding a new Mark, optionnally into a collection and/or with tags '''
    # validate arguments before prompting, so bad input fails fast
    if collection and not COLLECTION_NAME_PATTERN.match(collection):
        print ("collection name can only contain a-z 0-9 _ -")
        return
    clean_tags = []
    for t in (tags or []):
        t = t.strip()
        if not t:
            continue
        if not COLLECTION_NAME_PATTERN.match(t):
            print ("tag can only contain a-z 0-9 _ - : %s" % t)
            return
        if t not in clean_tags:
            clean_tags.append(t)
    if cmd_string:
        cmd_string = cmd_string.strip()
    if not cmd_string:
        cmd_string = keyboard_input("Command:")
    else:
        print("command: %s" % cmd_string)
    if not cmd_string:
        print ("command field is required")
        return
    if not alias:
        alias = keyboard_input("Alias?:")
    else:
        print("alias: %s" % alias)
    if '##' in cmd_string or '##' in alias:
        # ## isn't allowed since it's used as seperator
        print ("command can't contain ##(it's used as command alias seperator)")
        return
    if collection:
        if not os.path.isdir(get_collections_dir()):
            os.makedirs(get_collections_dir())
        marks_path = get_collection_path(collection)
    else:
        marks_path = get_user_marks_path()
    commands = command.load(marks_path)
    command.add(commands, command.Command(cmd_string, alias, clean_tags))
    command.save(commands, marks_path)

def get_selected_command_or_input(search):
    ''' Display an interactive UI interface where the user can type and select commands
        this function returns the selected command if there is matches or the written characters in the prompt line if no matches are present
        the search can scope with "@collection" and filter with "#tag" sigils
    '''
    unfiled = command.load(get_user_marks_path())
    collections = {name: load_collection(name) for name in get_collections()}
    commands = unfiled + command.load(get_tldr_os_marks_path()) \
        + command.load(get_tldr_common_marks_path()) + command.load(get_tldr_security_marks_path())
    for cmds in collections.values():
        commands += cmds
    state = State(commands, search, collections=collections, unfiled=unfiled)
    # draw the screen (prompt + matchd marks)
    renderer.refresh(state)
    # wait for user input(returns selected mark)
    output = read_line(state)
    # clear the screen
    renderer.erase()
    if not output:
        return parse_search(state.input)[2]
    return output.cmd


def remove_command(search):
    ''' Remove a command interactively, from whichever file it belongs to '''
    unfiled = command.load(get_user_marks_path())
    collections = {name: load_collection(name) for name in get_collections()}
    commands = unfiled + [m for cmds in collections.values() for m in cmds]
    state = State(commands, search, collections=collections, unfiled=unfiled)
    renderer.refresh(state)
    selected_mark = read_line(state)
    if selected_mark:
        files = [(unfiled, get_user_marks_path())]
        files += [(collections[name], get_collection_path(name)) for name in sorted(collections)]
        for marks, path in files:
            before = len(marks)
            command.remove(marks, selected_mark)
            if len(marks) != before:
                command.save(marks, path)
    # clear the screen
    renderer.erase()
    return selected_mark

def read_line(state):
    ''' parse user input '''
    output = None
    while True:
        c = readchar.get_symbol()
        if c == keys.ENTER:
            if state.get_matches():
                output = state.get_selected_match()
            break
        elif c == keys.CTRL_C or c == keys.ESC:
            state.reset_input()
            break
        elif c == keys.CTRL_U:
            state.clear_input()
        elif c == keys.BACKSPACE:
            state.set_input(state.input[0:-1])
        elif c == keys.UP:
            state.select_previous()
        elif c == keys.DOWN or c == keys.TAB:
            state.select_next()
        elif c <= 126 and c >= 32:
            state.set_input(state.input + chr(c))
        renderer.refresh(state)
    return output

class State(object):
    ''' The app State, including user written characters, matched commands, and selected one '''

    def __init__(self, bookmarks, default_input, collections=None, unfiled=None):
        self.bookmarks = bookmarks
        self._selected_command_index = 0
        self.matches = []
        self.default_input = default_input
        self._collections = collections or {}
        self._unfiled = unfiled if unfiled is not None else bookmarks
        self.set_input(default_input)

    def get_matches(self):
        return self.matches

    def reset_input(self):
        self.input = self.default_input

    def set_input(self, input):
        self.input = input if input else ""
        self._update()

    def clear_input(self):
        self.set_input("")

    def clear_selection(self):
        self._selected_command_index = 0

    def select_next(self):
        self._selected_command_index = (self._selected_command_index + 1) % len(self.matches) if len(self.matches) else 0

    def select_previous(self):
        self._selected_command_index = (self._selected_command_index - 1) % len(self.matches) if len(self.matches) else 0

    def _update(self):
        # "@collection" scopes to one collection, "#tag" filters custom commands
        collection, tags, query = parse_search(self.input)
        pool = self.bookmarks
        if collection or tags:
            if collection:
                # case-insensitive lookup(hand-named files may differ in case)
                pool = next((cmds for name, cmds in self._collections.items()
                             if name.lower() == collection), [])
            else:
                pool = self._unfiled + [m for cmds in self._collections.values() for m in cmds]
            if tags:
                pool = [m for m in pool if all(t in m.tags for t in tags)]
        self.matches = filter_commands(pool, query)
        self._selected_command_index = 0

    def get_selected_match(self):
        if len(self.matches):
            return self.matches[self._selected_command_index]
        else:
            raise 'No matches found'
