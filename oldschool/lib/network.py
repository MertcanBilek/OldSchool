import socket
import time

try:
    from .consts import networkOpts, generalOpts
    from .logger import *
    from . import sebcrypter as seb
    from lib import _thread, _Indexer
except ImportError:
    from consts import networkOpts, generalOpts
    from logger import *
    import sebcrypter as seb
    from __init__ import _thread, _Indexer
from hashlib import md5


class _SocketBase(socket.socket):
    def __init__(self, name: str, key: bytes = None) -> None:
        super().__init__()
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.logger = Logger(name)
        self.rawKey = key
        self._dataLength = _Indexer("_dataLength")
        self._hash = _Indexer("_hash")
        self._data = _Indexer("_data")
        self._response = _Indexer("_response")
        if self.rawKey:
            self.key = seb.readkey(key=key)
        else:
            self.key = None
        self.keySent = False

    def _send(self, code: int, data: bytes):
        self.sendCode(code)
        self.sock.send(data)

    def _recv(self, ind: _Indexer, buflen: int):
        msg = self.sock.recv(buflen)
        ind.add(msg)
        self.logger.info("Message added to index : %s %s", msg, ind.name)

    def sendCode(self, code: int):
        if code.bit_length() == networkOpts.constLenght*8:
            code = code.to_bytes(networkOpts.constLenght,
                                 networkOpts.byteorder)
            self.sock.send(code)
            self.logger.info("Code sent : %s", code)
        else:
            self.logger.error("Code length is not approprite : %s", code)

    def recvCode(self) -> int:
        buflen = networkOpts.constLenght
        code = self.sock.recv(buflen)
        self.logger.info("Received code : %s", code)
        code = self.convertBytes(code)
        return code

    def sendEncoded(self, msg: bytes):
        if self.key and self.keySent:
            msg = seb.encrypt(msg, self.key)
        else:
            pass
        packSize = networkOpts.packageSize
        dataSize = len(msg)
        self.logger.debug("Data size : %s", dataSize)
        packCount = (dataSize // networkOpts.packageSize) + 1
        self.logger.debug("Package count : %s", packCount)
        _dataSize = dataSize.to_bytes(
            networkOpts.dataSizeLenght, networkOpts.byteorder)
        self._send(networkOpts.dataLenght, _dataSize)
        self.logger.debug("Data size sent: %s", _dataSize)
        for i in range(packCount):
            data = msg[i*packSize:(i+1)*packSize]
            hsh = md5(data).digest()
            self._send(networkOpts.hash, hsh)
            self.logger.debug("Hash sent : %s", hsh)
            while True:
                self._send(networkOpts.data, data)
                self.logger.debug("Data sent : %s", data)
                resp = self._response.pop()
                self.logger.debug("Received response : %s", resp)
                if resp == b"ok":
                    break
                elif resp == b"no":
                    continue

    def recvDecoded(self) -> bytes:
        sock = self
        key = self.key
        keySent = self.keySent
        dataLen = int.from_bytes(sock._dataLength.pop(), networkOpts.byteorder)
        self.logger.debug("Received data length : %s", dataLen)
        packSize = networkOpts.packageSize
        packCount = (dataLen // packSize) + 1
        self.logger.debug("Package count to receive : %s", packCount)
        msg = b""
        for i in range(packCount):
            hsh = sock._hash.pop()
            self.logger.debug("Hash received : %s", hsh)
            while True:
                data = sock._data.pop()
                self.logger.debug("Data received : %s", data)
                if md5(data).digest() == hsh:
                    sock._send(networkOpts.response, b"ok")
                    self.logger.debug("Response sent : %s", "OK")
                    msg += data
                    break
                else:
                    sock._send(networkOpts.response, b"no")
                    self.logger.debug("Response sent : %s", "NO")
                    continue
        if key and keySent:
            msg = seb.decrypt(msg, key)
            self.logger.info("Decrypted message received : %s", msg)
        else:
            self.logger.info("Unencrypted message received : %s", msg)
        return msg

    def convertBytes(self, _bytes: bytes) -> int:
        return int.from_bytes(_bytes, networkOpts.byteorder)


class _Client(_SocketBase):
    def __init__(self, sock: socket.socket, addr: tuple, key: bytes):
        super().__init__(addr, key)
        self.addr = addr
        self.sock = sock
        self.userName = None
        self.id = None

    def sendMsg(self, msg: bytes):
        self.sendEncoded(msg)

    def setUserName(self, userName: str):
        self.userName = userName
        self.logger.debug("User name set : %s", userName)

    def setKey(self, key: bytes):
        self.rawKey = key
        self.key = seb.readkey(key=key)
        self.logger.debug("Key set : %s", key)

    def setId(self, id):
        self.id = id
        self.logger.debug("ID set : %s", id)

    def __repr__(self) -> str:
        return str(self.addr)


class Server(_SocketBase):
    def __init__(self, password: str = None):
        super().__init__("network.Server")
        self.password = password
        if self.password:
            self.password = self.password.encode()
        self.bind(("0.0.0.0", networkOpts.defaultPort))
        self.listen()
        self.settimeout(networkOpts.timeout)
        self._id = 0
        self.clients = []
        self.clientsLoggedIn = []
        self._messagesToSend = _Indexer()
        _thread(self.sender)
        self.logger.debug("Sender started")
        _thread(self.userNameSender)
        self.logger.debug("User name sender started")
        self.logger.info("Server is ready and running")
        self.waitConnection()

    def sender(self):
        while True:
            c = self._messagesToSend.pop()
            self.message(c)

    def id(self):
        id = self._id
        self._id += 1
        return id

    def waitConnection(self) -> None:
        while True:
            try:
                conn, addr = self.accept()
                self.logger.info("Connectted : %s", addr)
                _thread(self.authentication, conn)
            except socket.timeout:
                continue

    def authentication(self, conn: socket.socket) -> bool:
        fails = 0
        conn = _Client(conn, conn.getpeername(), None)
        self.clients.append(conn)
        _thread(self.makeConnection, conn)
        self.addKey(conn)
        conn.logger.info("Key added")
        if self.password:
            conn.sendCode(networkOpts.passwordRequired)
            conn.logger.debug("Password required code sent")
            while True:
                try:
                    passwd = conn.recvDecoded()
                    conn.logger.info("Received password : %s", passwd)
                    if passwd == self.password:
                        conn.logger.info("Received password is correct")
                        conn.sendCode(networkOpts.correctPassword)
                        conn.logger.debug("Correct password code sent")
                        self.allowConnection(conn)
                        break
                    else:
                        fails += 1
                        conn.logger.warn("Received password is incorrect")
                        time.sleep(3)
                        conn.sendCode(networkOpts.incorrectPassword)
                        conn.logger.debug("Incorrect password code sent")
                        if fails == 3:
                            conn.logger.warn("Failed login :", conn)
                            conn.sendCode(networkOpts.loginFailed)
                            conn.logger.debug("Login failed code sent")
                            self.terminateConnection(
                                conn, "3 failed login attemp")
                            break
                except socket.timeout:
                    conn.logger.warn("Timeout")
                    self.terminateConnection(conn, "Timeout")
                    break
                except BrokenPipeError:
                    conn.logger.warn("BrokenPipe")
                    self.terminateConnection(conn, "BrokenPipe")
                    break
        else:
            conn.sendCode(networkOpts.passwordNotRequired)
            conn.logger.debug("Password not required code sent")
            self.allowConnection(conn)

    def allowConnection(self, conn: _Client):
        self.logger.info("Connecttion allowed : %s", conn)
        conn.sendCode(networkOpts.userName)
        conn.logger.debug("User name code sent")
        rawUserName = conn.recvDecoded()
        conn.logger.info("Received user name : %s", rawUserName)
        userName = self.checkUserName(rawUserName)
        if userName:
            conn.sendCode(networkOpts.appropriateUserName)
            self.logger.debug("User name appropriate code sent")
            conn.sendCode(networkOpts.loginSuccessful)
            self.logger.debug("Login successful code sent")
            conn.setUserName(userName.ljust(generalOpts.maxUserNameLenght))
            conn.setId(self.id())
            self.clientsLoggedIn.append(conn)
            self.logger.info("Client added clientsLoggedIn : %s", conn)
        else:
            conn.sendCode(networkOpts.inappropriateUserName)
            self.logger.debug("Inappropriate user name sent")
            self.terminateConnection(conn, "Inappropriate user name")

    def makeConnection(self, conn: _Client):
        while True:
            try:
                code = conn.recvCode()
                conn.logger.info("Received code : %s", code)
            except ConnectionResetError:
                self.terminateConnection(conn, "Connection Reset by Peer")
            if code == networkOpts.message:
                self._messagesToSend.add(conn)
            elif code == networkOpts.dataLenght:
                conn._recv(conn._dataLength, networkOpts.dataSizeLenght)
            elif code == networkOpts.hash:
                conn._recv(conn._hash, networkOpts.hashLenght)
            elif code == networkOpts.data:
                conn._recv(conn._data, networkOpts.packageSize)
            elif code == networkOpts.response:
                conn._recv(conn._response, 2)
            elif code == 0:
                self.terminateConnection(conn, "Connection Lost")
                break
            else:
                pass

    def message(self, conn: _Client):
        msg = conn.recvDecoded()
        conn.logger.info("Received message : %s", msg)
        formattedMsg = self.formatMessage(msg, conn.userName)
        self.sendToEveryone(networkOpts.message, formattedMsg)

    def addKey(self, conn: _Client) -> list:
        conn.sendCode(networkOpts.key)
        conn.logger.debug("Key code sent")
        key = conn.recvDecoded()
        conn.logger.debug("Received key : %s", key)
        conn.setKey(key)
        conn.keySent = True

    def formatMessage(self, msg: bytes, userName: str) -> bytes:
        message = generalOpts.maxUserNameLenght.to_bytes(
            1, networkOpts.byteorder) + userName.encode().ljust(generalOpts.maxUserNameLenght) + msg
        return message

    def userNameSender(self):
        while True:
            loggedinclients = self.clientsLoggedIn.copy()
            while loggedinclients == self.clientsLoggedIn:
                pass
            self.logger.debug("Sending users : %s", self.clientsLoggedIn)
            for c in self.clientsLoggedIn:
                users = [u.userName for u in self.clientsLoggedIn if u.id != c.id]
                if not users:
                    break
                mul = generalOpts.maxUserNameLenght.to_bytes(
                    1, networkOpts.byteorder)
                message = b""
                message += mul
                for user in users:
                    message += user.encode()
                c.sendCode(networkOpts.users)
                c.logger.debug("Users code sent")
                c.sendEncoded(message)
                c.logger.debug("Users sent")

    def sendToEveryone(self, code, msg):
        self.logger.debug("Sending to everyone : %s %s", code, msg)
        for conn in self.clientsLoggedIn:
            conn.sendCode(code)
            conn.sendEncoded(msg)

    def checkUserName(self, userName: bytes):
        try:
            userName = userName.decode()
        except UnicodeDecodeError:
            return False
        # TODO return int for determition of inappropriate user name
        if "\\" in repr(userName) or len(userName) > generalOpts.maxUserNameLenght:
            return False
        return userName

    def terminateConnection(self, conn: _Client, reason: str):
        try:
            conn.sendCode(networkOpts.terminateConnection)
            conn.sendEncoded(reason.encode())
            conn.close()
            conn.logger.warn("Connection terminated")
        except socket.error as error:
            conn.logger.warn("Error catched : %s", error, exc_info=True)
        try:
            self.clients.remove(conn)
        except ValueError:
            conn.logger.debug("Client not in list : %s", conn)
        try:
            self.clientsLoggedIn.remove(conn)
        except ValueError:
            conn.logger.debug("Client not in clientsLoggedIn : %s", conn)


class Client(_SocketBase):
    def __init__(self, userName: str, key: bytes, ip: str, port: int = networkOpts.defaultPort):
        super().__init__("network.Client", key)
        self.sock = self
        self.userName = userName
        addr = (ip, port)
        self.connect(addr)
        self._loggedin = False
        self.passwordRequired = None
        self.messages = []
        self.receiver = self._getMessage()
        self.result = None
        self.userNameResult = None
        self.messageSendable = True
        self._messagesToSend = _Indexer("_messagesToSend")
        _thread(self._messageSender)
        self.logger.info("Message sender started")
        _thread(self._makeConnection)
        self.logger.info("Client started")

    def _makeConnection(self):
        while True:
            # if self._loggedin:
            #    breakpoint()
            code = self.recvCode()
            self.logger.info("Recevied code : %s", code)
            if code == networkOpts.passwordRequired:
                self.passwordRequired = True
            elif code == networkOpts.passwordNotRequired:
                self.passwordRequired = False
            elif code == networkOpts.correctPassword:
                self.result = networkOpts.correctPassword
            elif code == networkOpts.incorrectPassword:
                self.result = networkOpts.incorrectPassword
            elif code == networkOpts.userName:
                _thread(self._sendUserName)
            elif code == networkOpts.loginSuccessful:
                self._loggedin = True
            elif code == networkOpts.loginFailed:
                self._loggedin = False
            elif code == networkOpts.appropriateUserName:
                self.userNameResult = True
            elif code == networkOpts.inappropriateUserName:
                self.userNameResult = False
            elif code == networkOpts.message:
                _thread(self._recvMsg)
            elif code == networkOpts.key:
                _thread(self._sendKey)
            elif code == networkOpts.users:
                _thread(self._recvUsers)
            elif code == networkOpts.dataLenght:
                self._recv(self._dataLength, networkOpts.dataSizeLenght)
            elif code == networkOpts.hash:
                self._recv(self._hash, networkOpts.hashLenght)
            elif code == networkOpts.data:
                self._recv(self._data, networkOpts.packageSize)
            elif code == networkOpts.response:
                self._recv(self._response, 2)
            elif code == networkOpts.terminateConnection:
                reason = self.recvDecoded()
            elif code == 0:
                self.terminateConnection()
                self.passwordRequired = False
                return
            else:
                pass

    def _sendKey(self):
        self.logger.debug("Sending key")
        self.sendEncoded(self.rawKey)
        self.logger.info("Key sent")
        self.keySent = True

    def _sendUserName(self):
        self.logger.debug("Sending user name")
        self.sendEncoded(self.userName.encode())
        self.logger.debug("User name sent")
        while self.userNameResult == None:
            pass
        if self.userNameResult:
            self.logger.debug("User name is okay")
        else:
            self.logger.warn("User name is not appropriate")
        self.userNameResult = None

    def _messageSender(self):
        while True:
            while not self.messageSendable:
                pass
            msg = self._messagesToSend.pop()
            self.logger.info("Sending message : %s", msg)
            self.sendMsg(msg)
            self.logger.info("Message sent : %s", msg)
            self.messageSendable = False

    def _recvMsg(self):
        msg = self.recvDecoded()
        self.logger.info("Received message : %s", msg)
        msg = self._formatMsg(msg)
        self.messages.append((networkOpts.message, msg))
        if msg[1].strip() == self.userName:
            self.messageSendable = True

    def _recvUsers(self):
        _users = self.recvDecoded()
        self.logger.info("Received users : %s", _users)
        users = []
        mul, _users = _users[0], _users[1:]
        userCount = len(_users) // mul
        for i in range(userCount):
            user = _users[i*mul:(i+1)*mul]
            users.append(user)
        self.messages.append((networkOpts.users, users))

    def _checkPassword(self, password: str):
        try:
            password = password.encode()
        except UnicodeEncodeError:
            return False
        if "\\" in repr(password) or len(password) > networkOpts.maxPasswordLenght:
            return False
        return password

    def _getMessage(self):
        while True:
            try:
                msg = self.messages.pop()
                yield msg
            except IndexError:
                pass

    def _getResult(self):
        while self.result == None:
            pass
        result = self.result
        self.result = None
        return result

    def _formatMsg(self, msg: bytes):
        userNameLen = msg[0]
        userName = msg[1:userNameLen+1].decode()
        message = msg[userNameLen+1:].decode()
        return (message, userName)

    def isLoggedIn(self):
        for i in range(10):
            if self._loggedin:
                return True
            else:
                time.sleep(.5)
        return False

    def terminateConnection(self):
        self.close()
        self.logger.info("Connection terminated")

    def sendMsg(self, msg: str):
        if self._loggedin:
            self.sendCode(networkOpts.message)
            self.sendEncoded(msg.encode())
        else:
            return networkOpts.passwordRequired

    def getMessage(self):
        return next(self.receiver)

    def addToIndex(self, msg):
        self._messagesToSend.add(msg)

    def isPasswordRequired(self):
        while self.passwordRequired == None:
            pass
        return self.passwordRequired

    def login(self, password: str) -> int:
        password = self._checkPassword(password)
        if password:
            self.sendEncoded(password)
        else:
            return networkOpts.incorrectPassword
        result = self._getResult()
        self.logger.debug("Login result : %s", result)
        if result == networkOpts.correctPassword:
            return networkOpts.correctPassword
        elif result == networkOpts.incorrectPassword:
            return networkOpts.incorrectPassword


if __name__ == "__main__":
    key = seb.keygen()
    o = input("s/c ")
    if o == "s":
        s = Server("1234")
    elif o == "c":
        c = Client("Kullanıcı", key, "127.0.0.1", log=True)
        if c.isPasswordRequired():
            for i in range(3):
                result = c.login(input("Password : "))
                if result == networkOpts.correctPassword:
                    print("Logged in")
                    break
                elif result == networkOpts.incorrectPassword:
                    print("Incorrect password")
        time.sleep(1)
        input()
        if c.sendMsg("Merhaba") == networkOpts.passwordRequired:
            print("Login required")
        else:
            print(c.getMessage())
        c.terminateConnection()
