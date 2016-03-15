import logging
import sublime
from .pgcli_sublime import format_results
from time import sleep

try:
    from SublimeREPL.repls import Repl
except ImportError:
    Repl = object

logger = logging.getLogger('pgcli_sublime.repl')


class SublimePgcliRepl(Repl):
    TYPE = "pgcli"

    def __init__(self, encoding, pgcli_url=None):
        super(SublimePgcliRepl, self).__init__(encoding,
                                               additional_scopes=['sql'])

        global psycopg2
        from .pgcli_sublime import PGCli, psycopg2
        settings = sublime.load_settings('PgcliSublime.sublime_settings')
        pgclirc = settings.get('pgclirc')

        logger.debug('Pgcli url: %r', pgcli_url)
        self.url = pgcli_url
        self.pgcli = PGCli(pgclirc_file=pgclirc)
        self.pgcli.connect_uri(pgcli_url)
        self.pgcli.refresh_completions()
        self._query = None
        self._brand_new = True

    def name(self):
        return 'pgcli'

    def write(self, sql):
        logger.debug('Write: %r', sql)
        self._query = sql

    def prompt(self):
        return '{}> '.format(self.pgcli.pgexecute.dbname)

    def read(self):

        # Show the initial prompt
        if self._brand_new:
            logger.debug('Brand new prompt')
            self._brand_new = False
            return self.prompt()

        # Block until a command is entered
        while not self._query:
            sleep(.1)

        logger.debug('Query: %r', self._query)

        try:
            results = self.pgcli.pgexecute.run(self._query)
            results = format_results(results, self.pgcli.table_format)
        except psycopg2.Error as e:
            results = e.pgerror
        finally:
            self._query = None

        if results:
            return '\n' + results + '\n\n' + self.prompt()
        else:
            return self.prompt()

    def autocomplete_completions(self, whole_line, pos_in_line, *args, **kwargs):
        comps = self.pgcli.get_completions(whole_line, pos_in_line)
        return [(comp.text, comp.display) for comp in comps]

    def is_alive(self):
        return self.pgcli is not None

    def kill(self):
        self.pgcli = None

    def allow_restarts(self):
        return True

    def autocomplete_available(self):
        return True
