"""ncurses based displaying module"""
try:
    import curses
except ImportError:
    print("First of all run 'pip install windows-curses'")
    quit()
try:
    from .logger import *
    from .consts import *
except ImportError:
    from logger import *
    from consts import *
class _Messages:
    """Storage for last <numberOfLines> messages"""

    def __init__(self, numberOfLines: int) -> None:
        self.messages = []
        self.nol = numberOfLines

    def add(self, item: object) -> None:
        """Adds a new message to storage"""
        self.messages.append(item)
        l = len(self.messages)
        if l > self.nol:
            self.messages = self.messages[-self.nol:]

    def __repr__(self) -> str:
        return self.messages.__repr__()


class _YX:
    """Makes easier to access size of windows"""

    def __init__(self, _yx: tuple) -> None:
        self._size = (0, 0)
        self.x = 0
        self.y = 0
        self.size = _yx

    @property
    def size(self) -> tuple:
        """Returns current size"""
        return (self._size)

    @size.setter
    def size(self, newyx) -> None:
        if self.control(newyx):
            self._size = tuple(newyx)
            self.y, self.x = self._size

    def control(self, yx) -> bool:
        """Checks if given value is appropriate"""
        _error = False
        if type(yx) != tuple and type(yx) != list:
            _error = True
        elif len(yx) != 2:
            _error = True
        if _error:
            self.raiseError()
            return False
        else:
            return True

    def raiseError(self) -> None:
        raise ValueError("Given value must be tuple or list and have 2 items")


class _WindowBase:
    """Fundamental features for windows"""

    def __init__(self, window: curses.window, name: str):
        self._window = window
        self.size = None
        self.name = name
        self.logger = Logger(self.name)
        self.resize()

    @property
    def window(self) -> curses.window:
        return self._window

    @window.setter
    def window(self, window: curses.window) -> None:
        self._window = window
        self.resize()

    def resize(self) -> _YX:
        """Updates self.size"""
        if self.window:
            self.size = _YX(self.window.getmaxyx())
            self.logger.info("Resized window : %s",self.size.size)
        return self.size


class _Grid(_WindowBase):
    """Grid method for sepataring display"""

    def __init__(self, window: curses.window, y: int, x: int):
        super().__init__(window, "display._Grid")
        self.x = x
        self.y = y
        self.grids = [[self]]

    def vsep(self, x: int) -> None:
        """Vertical separator"""
        counter = 0
        for line in self.grids:
            endOfTheLine = line[-1]
            subwin = endOfTheLine.window.subwin(
                endOfTheLine.size.y, x, endOfTheLine.y, endOfTheLine.x)
            self.grids[counter][-1] = _Grid(subwin,
                                            endOfTheLine.y, endOfTheLine.x)
            subwin = endOfTheLine.window.subwin(
                endOfTheLine.size.y, endOfTheLine.size.x - x, endOfTheLine.y, endOfTheLine.x + x)
            self.grids[counter].append(_Grid(subwin, endOfTheLine.y, x))
            counter += 1

    def hsep(self, y) -> None:
        """Horizontal separator"""
        counter = 0
        newLine = []
        for column in self.grids[-1]:
            subwin = column.window.subwin(y, column.size.x, column.y, column.x)
            self.grids[-1][counter] = _Grid(subwin, column.y, column.x)
            subwin = column.window.subwin(
                column.size.y - y, column.size.x, column.y + y, column.x)
            newLine.append(_Grid(subwin, y, column.x))
            counter += 1
        self.grids.append(newLine)

    def __repr__(self) -> str:
        return "< _Grid " + str(self.size.size) + "  " + str(self.y) + "  " + str(self.x) + " >"


class _UserBar(_WindowBase):
    """Lists users in the list <self.users>"""

    def __init__(self, window: curses.window) -> None:
        super().__init__(window, "display._UserBar")
        self.users = list()
        self.refresh()

    def addUser(self, user: str) -> None:
        """Adds a new user to the list"""
        self.users.append(user)
        self.logger.debug("Added user : %s",user)
        self.refresh()

    def removeUser(self, user: str):
        """Remove a user from the list"""
        try:
            self.users.remove(user)
            self.logger.debug("Removed user : %s",user)
            self.refresh()
        except ValueError:
            pass

    def updateUser(self, users: list):
        """Removes all users and adds the news"""
        self.users = users
        self.logger.debug("New users list : %s", users)
        self.refresh()

    def rightBorder(self, char: str, connectionChar: str) -> None:
        """Separates _MessagesBar from itself"""
        if self.window:
            colPair = curses.color_pair(displayOpts.colorPairs.greenBlack)
            for y in range(1, self.size.y-1):
                self.window.addstr(y, self.size.x-1, char, colPair)
            self.window.addstr(self.size.y-6, self.size.x -
                               1, connectionChar, colPair)

    def refresh(self) -> None:
        """Refreshes the users in the list in the window"""
        if self.window:
            self.window.clear()
            y = 1
            for user in self.users:
                self.window.addstr(y, 2, user, curses.color_pair(
                    displayOpts.colorPairs.yellowBlack))
                y += 1
            self.rightBorder(displayOpts.chars.verticalSeparator,
                             displayOpts.chars.connector)
            self.window.refresh()


class _MessageBar(_WindowBase):
    def __init__(self, window: curses.window, display) -> None:
        """Shows the messages in the list (self.messages)"""
        super().__init__(window, "display._MessageBar")
        self.display = display
        self.messages = _Messages(self.size.y - 2)
        self.userNameLen = generalOpts.maxUserNameLenght+2
        self.colorPair = curses.color_pair(displayOpts.colorPairs.yellowBlack)
        self.rawMessages = []

    def addMessage(self, msg: str, user: str) -> None:
        """Adds a new message to the list"""
        self.rawMessages.append((msg, user))
        message = self.formatMsg(msg, user)
        for line in message:
            self.messages.add(line)
        self.logger.info("Added message : %s",msg)
        self.refresh()

    def formatMsg(self, msg: str, user: str) -> list:
        """Formats message (msg) in list format (lines)"""
        maxMsgLen = self.size.x - 3 - generalOpts.maxUserNameLenght
        lines = [msg[i*maxMsgLen:(i+1)*maxMsgLen]
                 for i in range((len(msg) // maxMsgLen) + 1)]
        counter = 0
        message = []
        for line in lines:
            if counter == 0:
                message.append(f" {user.ljust(16)} " + line.ljust(maxMsgLen))
            else:
                message.append(" "*18+line)
            counter += 1
        message.append(" "*(18+maxMsgLen))
        return message

    def refresh(self) -> None:
        """Refreshes messages in the window"""
        self.messages = _Messages(self.size.y - 2)
        for m in self.rawMessages:
            for l in self.formatMsg(*m):
                self.messages.add(l)
        self.window.clear()
        y = 1
        for line in self.messages.messages:
            if line[:self.userNameLen] != " "*self.userNameLen:
                self.window.addstr(
                    y, 0, line[:self.userNameLen], self.colorPair)
                self.window.addstr(y, self.userNameLen,
                                   line[self.userNameLen:])
            else:
                self.window.addstr(y, 0, line)
            y += 1
        self.window.refresh()
        self.display.inputBar.window.touchwin()


class _InputBar(_WindowBase):
    """Gets messages from user"""

    def __init__(self, window: curses.window, display) -> None:
        super().__init__(window, "display._InputBar")
        self.input = ""
        self.display = display
        self.bottomLeft = (self.size.y - 1, 0)
        self.colorPair = curses.color_pair(displayOpts.colorPairs.greenBlack)
        self.sep = displayOpts.chars.horizontalSeparator
        self.refresh()

    def getInput(self) -> str:
        """Gets message from user"""
        self.window.move(1, 0)
        while True:
            char = self.getch()
            if char == 8:  # Backspace
                self.input = self.input[:-1]
                self.refresh()
            elif char == 10:  # Enter
                break
            else:
                yx = self.window.getyx()
                self.input += chr(char)
                if yx == self.bottomLeft:
                    self.refresh()
        input = self.input
        self.input = ""
        self.refresh()
        return input

    def getch(self) -> int:
        """Redirects got char if it is not special key that the method uses"""
        while True:
            char = self.window.get_wch()
            if char == curses.KEY_RESIZE:
                self.display.reseparate()
            elif char == 3:
                raise KeyboardInterrupt
            else:
                return ord(char)

    def topBorder(self) -> None:
        """Separates _MessagesBar from itself"""
        for x in range(self.size.x-1):
            self.window.addstr(0, x, self.sep, self.colorPair)

    def formatInput(self) -> None:
        """Scrolls message if it is too long"""
        cursors = self.size.x * (self.size.y - 3)
        length = len(self.input) % self.size.x
        input = self.input[-(cursors + length):]
        self.logger.debug("Input : %s")
        self.window.addstr(input)

    def refresh(self) -> None:
        """Refreshes the window"""
        self.window.clear()
        self.topBorder()
        self.window.move(1, 0)
        self.formatInput()
        self.window.refresh()


class Display(_WindowBase):
    """Main window"""

    def __init__(self, user: str) -> None:
        """user : user name"""
        window = curses.initscr()
        window.keypad(1)
        curses.cbreak()
        super().__init__(window, "display.Display")
        self.user = user
        self.colors()
        self.bars()
        self.userBar.addUser(user)
        self.refresh()
        self._ready = True

    def exit(self):
        self.window.keypad(0)
        curses.nocbreak()
        curses.endwin()

    def reseparate(self) -> None:
        """Updates the windows and the grid"""
        self.resize()
        if not self.checkSizes():
            curses.endwin()
            self.logger.fatal("Small Screen")
            quit()
        else:
            self.userBarSubwin, self.messageBarSubwin, self.inputBarSubwin = self.windows()
            self.userBar.window = self.userBarSubwin
            self.messageBar.window = self.messageBarSubwin
            self.inputBar.window = self.inputBarSubwin
            self.userBar.refresh()
            self.messageBar.refresh()
            self.inputBar.refresh()
            self.logger.debug("Windows reseparated")

    def bars(self) -> None:
        """Initilazes windows"""
        self.userBarSubwin, self.messageBarSubwin, self.inputBarSubwin = self.windows()
        self.userBar = _UserBar(self.userBarSubwin)
        self.messageBar = _MessageBar(self.messageBarSubwin, self)
        self.inputBar = _InputBar(self.inputBarSubwin, self)

    def windows(self) -> tuple:
        """Calculates windows size"""
        grid = _Grid(self.window, 0, 0)
        if self.size.x > 64:
            grid.vsep(displayOpts.sizes.minUserBarWidth)
            grid.grids[0][1].hsep(self.size.y - 6)
            userBar = grid.grids[0][0].window
            messageBar = grid.grids[0][1].grids[0][0].window
            inputBar = grid.grids[0][1].grids[1][0].window
        else:
            grid.hsep(self.size.y - 6)
            userBar = None
            messageBar = grid.grids[0][0].window
            inputBar = grid.grids[1][0].window
        return userBar, messageBar, inputBar

    def checkSizes(self) -> bool:
        """Checks if the sizes of the display are appropriate"""
        if self.size.x < displayOpts.sizes.minDisplayWidth or self.size.y < displayOpts.sizes.minDisplayHeight:
            self.logger.debug("Sizes : %s %s  %s %s",self.size.x, self.size.y , displayOpts.sizes.minDisplayWidth,displayOpts.sizes.minDisplayHeight)
            return False
        else:
            return True

    def colors(self) -> None:
        """Initilazes the colors"""
        curses.start_color()
        curses.init_pair(displayOpts.colorPairs.greenBlack,
                         curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(displayOpts.colorPairs.yellowBlack,
                         curses.COLOR_YELLOW, curses.COLOR_BLACK)

    def refresh(self) -> None:
        """Refreshes the display"""
        self.window.refresh()


if __name__ == "__main__":
    d = Display("Sebatkar")
    try:
        while True:
            msg = d.inputBar.getInput()
            d.messageBar.addMessage(msg,d.user)
    except KeyboardInterrupt:
        print("hahahahahhaha")
    except:
        print("error")
    finally:
        d.exit()