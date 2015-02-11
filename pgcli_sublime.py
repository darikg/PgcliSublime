import sublime
import sublime_plugin
import logging
import sys
import os
import site
from queue import Queue

pgclis = {}  # Dict mapping urls to pgcli objects
url_requests = Queue()  # A queue of database urls to asynchronously connect to

logger = logging.getLogger('pgcli_sublime')


def plugin_loaded():
    global settings
    settings = sublime.load_settings('PgcliSublime.sublime_settings')

    init_logging()
    logger.debug('Plugin loaded')

    # Before we can import pgcli, we need to know its path. We can't know that
    # until we load settings, and we can't load settings until plugin_loaded is
    # called, which is why we need to import to a global variable here

    sys.path = settings.get('pgcli_dirs') + sys.path
    for sdir in settings.get('pgcli_site_dirs'):
        site.addsitedir(sdir)

    logger.debug('System path: %r', sys.path)

    global PGCli
    from pgcli.main import PGCli

    global format_output
    from pgcli.main import format_output

    # All database connections are done in a separate thread so sublime doesn't
    # hang waiting for a connection to timeout or whatever
    sublime.set_timeout_async(monitor_connection_requests, 0)


def plugin_unloaded():
    global pgclis
    pgclis = {}


class PgcliPlugin(sublime_plugin.EventListener):
    def on_post_save(self, view):
        check_pgcli(view)

    def on_activated(self, view):
        check_pgcli(view)

    def on_query_completions(self, view, prefix, locations):

        if not get(view, 'pgcli_autocomplete'):
            return []

        logger.debug('Searching for completions')

        pgcli = get_pgcli(view)
        if not pgcli:
            return

        text = get_entire_view_text(view)
        cursor_pos = view.sel()[0].begin()
        logger.debug('Position: %d Text: %r', cursor_pos, text)

        comps = pgcli.get_completions(text, cursor_pos)
        if not comps:
            logger.debug('No completions found')
            return []

        comps = [(comp.text, comp.display) for comp in comps]
        logger.debug('Found completions: %r', comps)

        return comps, (sublime.INHIBIT_WORD_COMPLETIONS
                        | sublime.INHIBIT_EXPLICIT_COMPLETIONS)


class PgcliRunAllCommand(sublime_plugin.TextCommand):
    def description(self):
        return 'Run the entire contents of the view as a query'

    def run(self, edit):
        logger.debug('PgcliRunAllCommand')

        sql = get_entire_view_text(self.view)
        pgcli = get_pgcli(self.view)

        if not pgcli:
            return

        logger.debug('Command: PgcliExecute: %r', sql)
        results = pgcli.pgexecute.run(sql)
        for rows, headers, status in results:
            out = format_output(rows, headers, status, pgcli.table_format)
            print('\n'.join(out))

        # Make sure the console is visiblle
        sublime.active_window().run_command('show_panel', {'panel': 'console'})


class PgcliOpenCliCommand(sublime_plugin.TextCommand):
    def description(self):
        return 'Open a pgcli command line prompt'

    def run(self, edit):
        logger.debug('PgcliOpenCliCommand')

        url = get(self.view, 'pgcli_url')
        if not url:
            logger.debug('No url for current view')
            return

        logger.debug('Opening a command prompt for url: %r', url)
        cmd = get(self.view, 'pgcli_system_cmd')
        cmd = cmd.format(url=url)
        os.system(cmd)


class PgcliNewSqlFileCommand(sublime_plugin.WindowCommand):
    def description(self):
        return 'Open a new SQL file'

    def run(self):
        """Open a new file with syntax defaulted to SQL"""
        logger.debug('PgcliNewSqlFile')
        self.window.run_command('new_file')
        self.window.active_view().set_syntax_file(
            'Packages/SQL/SQL.tmLanguage')


def init_logging():

    for h in logger.handlers:
        logger.removeHandler(h)

    logger.setLevel(settings.get('pgcli_log_level', 'WARNING'))

    h = logging.StreamHandler(sys.stdout)
    h.setLevel(settings.get('pgcli_console_log_level', 'WARNING'))
    fmt = logging.Formatter('%(name)s: %(levelname)s: %(message)s')
    h.setFormatter(fmt)
    logger.addHandler(h)

    pgcli_logger = logging.getLogger('pgcli')
    pgcli_logger.addHandler(h)


def is_sql(view):
    syntax_file = view.settings().get('syntax')
    return 'sql' in syntax_file.lower()


def get_pgcli(view):
    if not is_sql(view):
        logger.debug('get_pgcli: View is not sql')
        return

    url = get(view, 'pgcli_url')
    if not url:
        logger.debug('get_pgcli: View URL is empty')
        return

    return pgclis.get(url)


def check_pgcli(view):
    """Check if a pgcli connection for the view exists, or request one"""

    if not is_sql(view):
        return

    url = get(view, 'pgcli_url')
    if not url:
        logger.debug('Empty pgcli url %r', url)
        return

    if url in pgclis:
        logger.debug('Already connected to %r', url)
        return

    url_requests.put(url)


def get(view, key):
    # Views may belong to projects which have project specific overrides
    # This method returns view settings, and falls back to base plugin settings
    val = view.settings().get(key)
    return val if val else settings.get(key)


def get_entire_view_text(view):
    return view.substr(sublime.Region(0, view.size()))


def monitor_connection_requests():

    while True:
        url = url_requests.get(block=True)
        if url in pgclis:
            # already connected
            continue

        logger.debug('Connecting to %r', url)
        pgcli = PGCli(never_passwd_prompt=True)
        pgcli.connect_uri(url)
        logger.debug('Connected to %r', url)

        logger.debug('Refreshing completions')
        pgcli.refresh_completions()
        logger.debug('Refreshed completions')

        logger.debug('Smart completions: %r', pgcli.completer.smart_completion)

        pgclis[url] = pgcli