#!/usr/bin/env python
# coding: utf-8

import re
import json
import threading
import subprocess

from .base import Base


class Source(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)
        self.name = 'flow'
        self.mark = '[flow]'
        self.filetypes = ['javascript']
        self.min_pattern_length = 2
        self.rank = 800
        self.input_pattern = '((?:\.|(?:,|:|->)\s+)\w*|\()'

    def on_init(self, context):
        self._stop_working = False
        self._flow_command = context['vars']['deoplete#sources#flow#flowbin']

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
            line = context['position'][1]
            col = context['complete_position'] + 1

            # Cache variables of neovim
            self._current_buffer = self.vim.current.buffer[:]
            args = (line, col,)
            startThread = threading.Thread(
                target=self.completation, name='Request Completion', args=args)
            startThread.start()
            startThread.join()

        # This ensure that async request will work
        return []

    def completation(self, line, column):
        command = [self._flow_command, 'autocomplete', '--no-auto-start',
                   '--json', str(line), str(column)]

        buf = '\n'.join(self._current_buffer)

        try:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
            command_results = process.communicate(input=str.encode(buf))[0]

            if process.returncode != 0:
                self.candidates = []
            else:
                results = json.loads(command_results.decode('utf-8'))
                # self.debug(results)

                self.candidates = [{
                    'dup': 0,
                    'word': x['name'],
                    'abbr': x['name'],
                    'info': x['type'],
                    'kind': x['type']} for x in results['result']]
        except FileNotFoundError:
            self.candidates = []
            self._stop_working = True
