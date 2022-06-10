# OldSchool the Messeger
OldSchool is a messeger that has ncurses UI

## Screenshot
![App Screenshot](https://raw.githubusercontent.com/MertcanBilek/OldSchool/master/images/oldschool.png)

## Requirements
* Python3
* If you are using Windows you may run given command for using the program
```bash
pip install windows-curses
```

## Usage
### Server
```
python oldschool server -h
usage: oldschool server [-h] [-P PASSWORD]

optional arguments:
  -h, --help            show this help message and exit
  -P PASSWORD, --password PASSWORD
                        optional password
```
You can specify a password that prevent strangers from your chat
### Client
```
python oldschool client -h
usage: oldschool client [-h] [-p PORT] [-P PASSWORD] ip username

positional arguments:
  ip                    IP address of server you will connect
  username              user name for server

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  optional port
  -P PASSWORD, --password PASSWORD
                        login password
```
You need the IP adress and a user name that you determine before entering a server
If you know that the server running on a different port (default 31415) you can use `-p` option
You may be asked for password if server has it. If you do not want to be prompted, you can specify the password with `-P` option

