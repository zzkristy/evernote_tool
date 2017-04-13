import os
import re
import json
import argparse
from evernote.api.client import EvernoteClient
from evernote.edam.notestore import NoteStore
from evernote.edam.type import ttypes as Types
from markdown import markdown as md

config_file = '.evernote'


def markdown(s):
    s = md(s, extensions=['markdown.extensions.fenced_code', 'markdown.extensions.tables'])
    return re.compile('<code[^>]*?>').sub('<code>', s)


def load_config(file_path):
    configs = {}
    if not os.path.exists(file_path):
        return configs
    with open(file_path) as f:
        return json.loads(f.read())


def dump_config(file_path, configs):
    with open(file_path, 'w') as f:
        json.dump(configs, f)


class EvernoteController(object):
    notebook_guid = None

    def __init__(self, token, notebook_name=None, service_host='app.yinxiang.com'):
        self.client = EvernoteClient(token=token, service_host=service_host)
        self.note_store = self.client.get_note_store()
        notebooks = self.get_all_notebooks()
        for book in notebooks:
            if book.name == notebook_name:
                self.notebook_guid = book.guid
                break
        if self.notebook_guid is None:
            print('notebook_name error')
            raise Exception('notebook_name')

    def get_all_notebooks(self):
        return self.note_store.listNotebooks()

    def get_notes_in_notebooks(self, notebook_guid=None):
        f = NoteStore.NoteFilter()
        f.notebookGuid = notebook_guid or self.notebook_guid
        s = NoteStore.NotesMetadataResultSpec()
        s.includeTitle = True
        note_names = {}
        for ns in self.note_store.findNotesMetadata(f, 0, 9999, s).notes:
            note_names[ns.title] = ns.guid
        return note_names

    def create_note(self, title, content, notebook_guid=None):
        note = Types.Note()
        note.title = title
        note.notebookGuid = notebook_guid or self.notebook_guid
        note.content = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
        note.content += '<en-note>'
        note.content += content
        note.content += '</en-note>'
        note = self.note_store.createNote(note)
        return note

    def update_note(self, guid, title, content):
        note = Types.Note()
        note.guid = guid
        note.title = title
        note.content = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
        note.content += '<en-note>'
        note.content += content
        note.content += '</en-note>'
        self.note_store.updateNote(note)


def scan_file(path):
    files_content = {}
    file_path = path + '.evernote'
    files_mtime = load_config(file_path)
    for file_name in os.listdir(path):
        if file_name.endswith('.md'):
            full_name = path + file_name
            statinfo = os.stat(full_name)
            o_mtime = files_mtime.get(file_name, 0)
            c_mtime = int(statinfo.st_mtime)
            if o_mtime < c_mtime:
                title = file_name.split('.')[0]
                with open(full_name) as f:
                    text = f.read().decode('utf-8')
                files_content[title] = text
                files_mtime[file_name] = c_mtime
    dump_config(file_path, files_mtime)
    return files_content


def main(token, path):
    if not token or not path:
        print('token or path error')

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--book", default='2017', help="note book")
    args = parser.parse_args()

    ec = EvernoteController(token, args.book)
    full_path = path + args.book + '/'
    notes = ec.get_notes_in_notebooks()
    files_content = scan_file(full_path)

    for title, content in files_content.items():
        html = markdown(content)
        if title in notes:
            ec.update_note(notes[title], title, html.encode('utf8'))
        else:
            ec.create_note(title, html.encode('utf8'))


if __name__ == '__main__':
    home_path = os.environ['HOME']
    file_path = home_path + '/' + config_file
    configs = load_config(file_path)
    main(**configs)
