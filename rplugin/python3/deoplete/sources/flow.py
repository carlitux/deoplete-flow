#!/usr/bin/env python
# coding: utf-8

import re
import json
import platform
import threading
import subprocess

from .base import Base

is_window = platform.system() == "Windows"
flow_token = 'AUTO332'


class Source(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)
        self.name = 'flow'
        self.mark = '[flow]'
        self.filetypes = ['javascript']
        self.min_pattern_length = 2
        self.rank = 800
        self.input_pattern = r'\.\w*$|^\s*@\w*$'

    def on_init(self, context):
        self._stop_working = False
        self._flow_command = context['vars']['deoplete#sources#flow#flowbin']
        self._vim_current_cwd = self.vim.eval('getcwd()')

    def get_complete_position(self, context):
        m = re.search(r'\w*$', context['input'])
        return m.start() if m else -1

    def gather_candidates(self, context):
        if self._stop_working:
            return []
        self.debug(context['input'])
        if context['is_async']:
            if self.candidates is not None:
                context['is_async'] = False
                return self.candidates
        else:
            self.candidates = None
            context['is_async'] = True
            line = context['position'][1] - 1
            col = context['position'][2] - 1
            current_file = context['bufname']

            # Cache variables of neovim
            self._current_buffer = self.vim.current.buffer[:]
            args = (line, col, current_file)
            startThread = threading.Thread(
                target=self.completation, name='Request Completion', args=args)
            startThread.start()
            startThread.join()

        # This ensure that async request will work
        return []

    def completation(self, line, column, current_file):
        command = [self._flow_command, 'autocomplete',
                   '--no-auto-start', '--json', current_file]

        current_line = self._current_buffer[line]
        self._current_buffer[line] = current_line[:column] + \
            flow_token + current_line[column:]
        buf = '\n'.join(self._current_buffer)

        try:
            process = subprocess.Popen(
                command,
                cwd=self._vim_current_cwd,
                shell=is_window,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            command_results = process.communicate(input=str.encode(buf))[0]

            if process.returncode != 0:
                self.candidates = []
            else:
                results = json.loads(command_results.decode('utf-8'))
                self.candidates = []

                for t in results['result']:
                    self.candidates.append({
                        'dup': 0,
                        'kind': self.get_kind(t),
                        'word': t['name'],
                        'info': t['type'],
                        'abbr': '{}{}'.format(t['name'], self.get_signature(t)) 
                        })

        except FileNotFoundError:
            self.candidates = []
            self._stop_working = True

    def get_kind(self, rec):
        kind = rec.get('type')

        if kind.startswith('class'):
            return 'class'
        elif rec.get('func_details'):
            return 'function'

        return kind

    def get_signature(self, rec):
        if rec.get('func_details'):
            return rec.get('type')

        return ''

