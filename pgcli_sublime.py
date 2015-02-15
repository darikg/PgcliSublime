import sublime
import sublime_plugin
import logging
import sys
import os
import site
import traceback
import queue

pgclis = {}  # Dict mapping urls to pgcli objects
MONITOR_URL_REQUESTS = False
url_requests = queue.Queue()  # A queue of database urls to asynchronously connect to

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

    global psycopg2
    import psycopg2

    # All database connections are done in a separate thread so sublime doesn't
    # hang waiting for a connection to timeout or whatever
    global MONITOR_URL_REQUESTS
    MONITOR_URL_REQUESTS = True
    sublime.set_timeout_async(monitor_connection_requests, 0)


def plugin_unloaded():
    global MONITOR_URL_REQUESTS
    MONITOR_URL_REQUESTS = False

    global pgclis
    pgclis = {}

    global url_requests
    url_requests = Queue()


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

        panel = get_output_panel(self.view)
        logger.debug('Command: PgcliExecute: %r', sql)
        out = ''

        try:
            results = pgcli.pgexecute.run(sql)
            out = []

            for rows, headers, status in results:
                fmt = format_output(rows, headers, status, pgcli.table_format)
                out.append('\n'.join(fmt))

            out = '\n\n'.join(out)
            logger.debug('Results: %r', out)

        except psycopg2.Error as e:
            out = e.pgerror

        # Write to panel
        panel.run_command('append', {'characters': out, 'pos': 0})

        # Make sure the output panel is visiblle
        sublime.active_window().run_command('pgcli_show_output_panel')


class PgcliShowOutputPanelCommand(sublime_plugin.TextCommand):
    def description(self):
        return 'Show the output panel'

    def run(self, edit):
        logger.debug('PgcliShowOutputPanelCommand')
        sublime.active_window().run_command('show_panel',
                {'panel': 'output.' + output_panel_name(self.view)})


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
        view = self.window.active_view()
        view.set_syntax_file('Packages/SQL/SQL.tmLanguage')
        check_pgcli(view)


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
        view.set_status('pgcli', '')
        return

    url = get(view, 'pgcli_url')
    if not url:
        view.set_status('pgcli', '')
        logger.debug('Empty pgcli url %r', url)
        return

    if url in pgclis:
        pgcli = pgclis[url]
        if pgcli is None:
            view.set_status('pgcli', 'ERROR CONNECTING TO {}'.format(url))
        else:
            view.set_status('pgcli', pgcli_id(pgcli))
            logger.debug('Already connected to %r', url)
        return

    view.set_status('pgcli', 'Connecting: ' + url)
    url_requests.put(url)


def get(view, key):
    # Views may belong to projects which have project specific overrides
    # This method returns view settings, and falls back to base plugin settings
    val = view.settings().get(key)
    return val if val else settings.get(key)


def get_entire_view_text(view):
    return view.substr(sublime.Region(0, view.size()))


def monitor_connection_requests():
    global MONITOR_URL_REQUESTS

    while MONITOR_URL_REQUESTS:

        try:
            url = url_requests.get(block=True, timeout=1)
        except queue.Empty:
            continue

        if url in pgclis:
            # already connected
            continue

        try:
            logger.debug('Connecting to %r', url)
            pgcli = PGCli(never_passwd_prompt=True)
            pgcli.connect_uri(url)
            logger.debug('Connected to %r', url)

            logger.debug('Refreshing completions')
            pgcli.refresh_completions()
            logger.debug('Refreshed completions')

            logger.debug('Smart completions: %r',
                         pgcli.completer.smart_completion)

        except Exception as e:
            logger.error('Error connecting to pgcli')
            logger.error('traceback: %s', traceback.format_exc())
            pgcli = None

        pgclis[url] = pgcli

        # Now that we've connected, update status in all open views
        for view in sublime.active_window().views():
            check_pgcli(view)


def pgcli_id(pgcli):
    pge = pgcli.pgexecute
    user, host = pge.user, pge.host
    return '{}@{}'.format(user, host)


def output_panel_name(view):
    return '__pgcli__' + (view.file_name() or 'untitled')


def get_output_panel(view):
    return view.window().create_output_panel(output_panel_name(view))
