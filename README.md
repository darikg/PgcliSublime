# PgcliSublime
A plugin for [Sublime Text 3](http://www.sublimetext.com/3) supporting
database-aware smart autocompletion via [pgcli](http://pgcli.com)

## Requirements
pgcli running in Python 3.3. (This is the version of python shipped with
Sublime Text 3). I recommend installing pgcli in a virtual environment.

## Installation
Clone or download this repo into a subdirectory in your ST3 /Packages directory.

## Configuration

### Settings
Open the default settings file: 
```Preferences | Package Settings | PgcliSublime | Settings - Default```
and the user settings file:
```Preferences | Package Settings | PgcliSublime | Settings - User```.
Copy and paste the contents of the defaults file into the user file. You 
*could* edit the default settings file directly, but your changes would be
overwritten every time you update PgcliSublime.

The most important configuration is setting up the path correctly, so the
Sublime Text 3 python interpreter can import pgcli. If you run python 3.3 as 
your system-wide interpreter, and pgcli is installed in your global 
site-packages, you don't need to do anything. If on the other hand you have
pgcli installed in a virtual environment, the easiest thing to do is add that
virtual environment's site-packages directory to the ```pgcli_site_dirs``` 
setting. Note that path strings need to be "double-quoted" and backslashes need 
to be escaped. See below for an example configuration. NOTE: You will have to
restart Sublime Text for changes to the pgcli paths to take effect.

Next, specify your default database url in the ```pgcli_url``` setting. You can 
leave this as ```postgresql://``` to default to your PGHOSTNAME, PGDATABASE, 
and PGUSER values.

Finally, if you wish to enable a shortcut to open a pgcli command prompt, 
fill in the "pgcli_system_cmd". This will be OS-specific.
 
### Example configuration
Here is the configuration I use in windows. I have one pgcli python 3.3 virtual
environment called pgcli3. Because there's currently issues with 
python-prompt-toolkit in windows with python 3, I have a second pgcli python
2.7 virtual environment called pgcli2 that I use to run the command prompt.
 
 ```
{
   // Use pgcli to for autocomplete? If false, standard sublime autocompletion is used
   "pgcli_autocomplete": 			true,
   
   // List of python directories to add to python path so pgcli can be imported
   "pgcli_dirs": 					[],
   
   // List of python site directories to add to python path so pgcli can be imported
   "pgcli_site_dirs": 				["C:\\Users\\dg\\Anaconda3\\envs\\pgcli3\\Lib\\site-packages"],
   
   // The path to the postgresql database. This may also be overridden in project-specific settings
   "pgcli_url": 					"postgresql://postgres@localhost/test",

   // The command to send to os.system to open a pgcli command prompt
   // {url} is automatically formatted with the appropriate database url
   "pgcli_system_cmd":             "start cmd.exe /k \"activate pgcli2 && pgcli {url}\"",
}
```

### Keyboard shortcuts
You can view the default keyboard shortcuts with 
```Preferences | Package Settings | PgcliSublime | Key Bindings - Default```
and the user override file:
```Preferences | Package Settings | PgcliSublime | Key Bindings - User```.
Again, you can copy and paste the contents of the defaults file into the user 
file.

## Usage 

### Auto-complete
PgcliSublime auto-complete runs in files with a SQL syntax. Create a new file
and manually set the syntax via the menu ```View | Syntax | SQL```, or save
a file with a .sql extension, or use the PgcliSublime shortcut 
```<ctrl-alt-shift-N>``` to open a new file and automatically set the syntax to 
SQL. While typing a query in an SQL file, either ```<tab>``` or 
```<ctrl-space>``` should trigger an autocomplete menu.

### Run query
Run the contents of the current view as a pgcli query with either the shortcut 
```<alt-enter>``` or via the menu  ```Tools | PgcliSublime | Run query```.
Output from the query will be printed to the sublime text console -- Hit 
```ctrl-~``` to toggle it, or the menu ```View - Show console```. 

### Open pgcli command prompt
If you've configured the ```pgcli_system_cmd``` setting, you can open a pgcli
REPL with the shortcut ```<ctrl-F12>```, or via the menu 
```Tools | PgcliSublime | Open command prompt```


## Trouble-shooting
I've only tested this in Windows so bug reports are appreciated. Check the 
sublime console (```<ctrl-~>```) for any error messages. 
