from lib import network, display, _thread
from argparse import ArgumentParser
from lib.consts import networkOpts
from lib import sebcrypter as seb

def _receiver(client:network.Client,stdscr:display.Display):
    while True:
        code , msg = client.getMessage()
        if code == networkOpts.message:
            stdscr.messageBar.addMessage(*msg)
        elif code == networkOpts.users:
            msg.insert(0,stdscr.user)
            stdscr.userBar.updateUser(msg)

def client(userName:str,password:str,ip:str,port:int=networkOpts.defaultPort):
    key = seb.keygen()
    if not port:
        port = networkOpts.defaultPort
    client = network.Client(userName,key,ip,port)
    if client.isPasswordRequired():
        for i in range(3):
            if not password:
                password = input("Password : ")
            result = client.login(password)
            if result == networkOpts.correctPassword:
                break
            elif result == networkOpts.incorrectPassword:
                password = None
    if not client.isLoggedIn():
        print("Login Failed")
        quit()
    stdscr = display.Display(userName)
    _thread(_receiver,client,stdscr)
    try:
        while True:
            msg = stdscr.inputBar.getInput()
            if msg:
                client.addToIndex(msg)
    except KeyboardInterrupt:
        pass
    except:
        stdscr.logger.error("An Error Accurated",exc_info=True)
    finally:
        stdscr.exit()
        client.terminateConnection()
        quit()

def server(password):
    server = network.Server(password)

argparser = ArgumentParser(add_help=True,exit_on_error=True)
argparser.set_defaults(id=0)
subparsers = argparser.add_subparsers()
clientParser = subparsers.add_parser("client",help="Client")
clientParser.add_argument("ip",help="IP address of server you will connect")
clientParser.add_argument("username",help="user name for server")
clientParser.add_argument("-p","--port",help="optional port")
clientParser.add_argument("-P","--password",help="login password")
clientParser.set_defaults(id=1)
serverParser = subparsers.add_parser("server",help="Server")
serverParser.add_argument("-P","--password",help="optional password")
serverParser.set_defaults(id=2)
args = argparser.parse_args()

if args.id == 1:
    ip = args.ip
    userName = args.username
    port = args.port
    password = args.password
    client(userName,password,ip,port)
elif args.id == 2:
    password = args.password
    server(password)
else:
    argparser.print_help()
