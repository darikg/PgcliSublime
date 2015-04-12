# Change log

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