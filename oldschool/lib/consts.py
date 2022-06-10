"""Constants for modules"""

class generalOpts:
    maxUserNameLenght = 16
class loggerOpts:
    directory = "log"
    file = "oldschool.log"
    format = "%(asctime)s > %(name)s > %(levelname)s > %(message)s"

class displayOpts:
    class colorPairs:
        greenBlack = 1
        yellowBlack = 2
    class chars:
        verticalSeparator = "│"
        horizontalSeparator = "─"
        connector = "├"
    class sizes:
        minUserBarWidth = 20
        minDisplayWidth = 40
        minDisplayHeight = 20

class networkOpts:
    defaultPort = 31415
    byteorder = "little"
    constLenght = 3
    timeout = 45
    maxPasswordLenght = 64
    maxMessageLenght = 2048
    reasonLenght = 1024
    keySize = 4100
    packageSize = 256
    dataSizeLenght = 8
    hashLenght = 16
    passwordRequired = 0xfff000
    passwordNotRequired = 0xfff001
    correctPassword = 0xfff002
    incorrectPassword = 0xfff003
    userName = 0xfff004
    appropriateUserName = 0xfff005
    inappropriateUserName = 0xfff006
    message = 0xfff007
    terminateConnection = 0xfff008
    loginSuccessful = 0xfff009
    loginFailed = 0xfff00a
    key = 0xfff00b
    users = 0xfff00c
    dataLenght = 0xfff00d
    hash = 0xfff00e
    data = 0xfff00f
    response = 0xfff010