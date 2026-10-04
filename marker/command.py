from . import ansi

def load(filePath):
    lines = []
    try:
        with open(filePath, 'r') as f:
            lines = [Command.deserialize(l.strip('\n').strip('\r')) for l in f.readlines() if l]
    except:
        pass
    return lines

def save(commands, filePath):
    with open(filePath, 'w') as f:
        f.write('\n'.join([m.serialize() for m in commands]))

def add(commands, command):
    remove(commands, command)
    commands.append(command)

def remove(commands, command):
    try:
        match = next(m for m in commands if command.equals(m))
        commands.remove(match)
    except StopIteration:
        pass

class Command(object):
    '''A Command is composed of the shell command string, an optionnal alias and optionnal tags'''
    def __init__(self, cmd, alias, tags=None):
        if not cmd:
            raise ValueError("empty command argument")
        self.cmd = cmd
        self.alias = alias
        if not self.alias:
            self.alias = ""
        self.tags = [t for t in (tags or []) if t]

    def __repr__(self):
        out = self.cmd
        if self.alias and self.alias != self.cmd:
            out += " " + ansi.grey_text(self.alias)
        if self.tags:
            out += " " + ansi.light_gray_text(" ".join("#" + t for t in self.tags))
        return out

    @staticmethod
    def deserialize(str):
        parts = str.split('##')
        cmd = parts[0]
        alias = parts[1] if len(parts) > 1 else ""
        tags = []
        if len(parts) > 2:
            # lowercase so hand-edited "Win,IDE" still matches "#win" searches
            tags = [t.strip().lower() for t in '##'.join(parts[2:]).split(',') if t.strip()]
        return Command(cmd, alias, tags)

    def serialize(self):
        if self.tags:
            return self.cmd + "##" + self.alias + "##" + ",".join(self.tags)
        if self.alias:
            return self.cmd + "##" + self.alias
        return self.cmd

    def equals(self, mark):
        # tags are not part of identity: re-marking a command updates its tags
        return self.cmd == mark.cmd and self.alias == mark.alias

