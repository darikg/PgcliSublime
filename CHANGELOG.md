# Change log

## [0.1.8]
  - Add an F1 command to run `\d+` or `\df+` on the table or function next to the cursor (Thanks @koljonen)
  - Make \special commands work in the SublimeREPL (Thanks @debjan)
  - Default shortcuts only override Sublime Text defaults in sql files

## [0.1.7]
  - Fix bug where run_current_command and autosuggestions were broken in views with multiple queries separated by more than a single whitespace character (Thanks @adnanyaqoobvirk)
  - Added MIT license

## [0.1.6]
  - Add pgcli_run_current command to ui and linux and osx keymaps (Thanks @adnanyaqoobvirk)

## [0.1.5]
  - Fix bug with empty syntax_file views (Thanks @adnanyaqoobvirk)
  
## [0.1.4]
  - Fix broken repl

## [0.1.3]
  - Major improvements in the threading model. Sublime text no longer hangs while running queries.

## [0.1.1] - 4/12/2015
  - Show database name in statusbar indentifier
  - Add a command to quickly switch between database connection strings
  - Bugfix: Newest version of pgcli changed result structure a little bit
  - Bugfix: Handle psycopg2 PGErrors without error messages

## [0.1.0] - 2/16/2015
  - Support running the cli directly in Sublime Text with the SublimeREPL plugin
  - Print datetime when showing output in the output pane
  
## [0.0.5] 
  - Minor bugfix
  
## [0.0.4]
  - Fix polling in connection thread so Sublime Text is no longer slow and 
    unresponsive
    
## [0.0.3]
  - Can now restart PgcliSublime plugin without restarting Sublime Text
  - RunAllCommand prints output in dedicated view output pane, not the main
    Sublime Text console
    
## [0.0.2]
  - Show connection alias in status bar

## [0.0.1]
  - Released on Package Control