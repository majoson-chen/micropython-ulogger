try:    import time
except: import utime as time

try:    from micropython import const
except: const = lambda x:x # for debug

from io import TextIOWrapper

__version__ = "v1.2"

DEBUG:    int = const(10)
INFO:     int = const(20)
WARN:     int = const(30)
ERROR:    int = const(40)
CRITICAL: int = const(50)

TO_FILE = const(100)
TO_TERM = const(200)

# fmt map 的可选参数
_level  = const(0)
_msg    = const(1)
_time   = const(2)
_name   = const(3)
_fnname = const(4)


def level_name(level: int, color: bool = False) -> str:
    if not color:
        if level == INFO:
            return "INFO"
        elif level == DEBUG:
            return "DEBUG"
        elif level == WARN:
            return "WARN"
        elif level == ERROR:
            return "ERROR"
        elif level == CRITICAL:
            return "CRITICAL"
    else:
        if level == INFO:
            return "\033[97mINFO\033[0m"
        elif level == DEBUG:
            return "\033[37mDEBUG\033[0m"
        elif level == WARN:
            return "\033[93mWARN\033[0m"
        elif level == ERROR:
            return "\033[35mERROR\033[0m"
        elif level == CRITICAL:
            return "\033[91mCRITICAL\033[0m"


class BaseClock ():
    """
    This is a BaseClock for the logger.
    Please inherit this class by your custom.
    """

    def __call__(self) -> str:
        """
        Acquire the time of now, please inherit this method.
        We will use the return value of this function as the time format of the log,
        such as `2021 - 6 - 13` or `12:45:23` and so on.

        :return: the time string.
        """
        return '%d' % time.time()


class Handler():
    """The Handler for logger.
    """
    _template: str
    _map: bytes
    level: int
    _direction: int
    _clock: BaseClock
    _color: bool
    _file_name: str
    _max_size: int
    _file = TextIOWrapper

    def __init__(self,
        level: int = INFO,
        colorful: bool = True,
        fmt: str = "&(time)% - &(level)% - &(name)% - &(msg)%",
        clock: BaseClock = None,
        direction: int = TO_TERM,
        file_name: str = "logging.log",
        max_file_size: int = 4096
        ):
        """
        Create a Handler that you can add to the logger later

        ## Options available for fmt.
        - &(level)%  : the log level
        - &(msg)%    : the log message
        - &(time)%   : the time acquire from clock, see `BaseClock`
        - &(name)%   : the logger's name
        - &(fnname)%  : the function name which you will pass on.
        - more optional is developing.

        ## Options available for level.
        - DEBUG
        - INFO
        - WARN
        - ERROR
        - CRITICAL

        ## Options available for direction.
        - TO_FILE : output to a file
        - TO_TERM : output to terminal

        :param level: Set a minimum level you want to be log
        :type level: int(see the consts in this module)

        :param colorful: Whether to use color display information to terminal(Not applicable to files)
        :type colorful: bool

        :param fmt: the format string like: "&(time)% - &(level)% - &(name)% - &(fnname)% - &(msg)%"(default)
        :type fmt: str

        :param clock: The Clock which will provide time str. see `BaseClock`
        :type clock: BaseClock(can be inherit )

        :param direction: Set the direction where logger will output
        :type direction: int (`TO_FILE` or `TO_TERM`)

        :param file_name: available when you set `TO_FILE` to param `direction`. (default for `logging.log`)
        :type file_name: str
        :param max_file_size: available when you set `TO_FILE` to param `direction`. The unit is `byte`, (default for 4k)
        :type max_file_size: str
        """
        #TODO: 文件按日期存储, 最大份数的设置.
        self._direction = direction
        self.level = level
        self._clock = clock if clock else BaseClock()
        self._color = colorful
        self._file_name = file_name if direction == TO_FILE else ''
        self._max_size = max_file_size if direction == TO_FILE else 0

        if direction == TO_FILE:
            self._file = open(file_name, 'a+')

        # 特么的re居然不能全局匹配, 烦了, 只能自己来.
        # m = re.match(r"&\((.*?)\)%", fmt)
        # i = 0
        # while True:
        #     # 由于蛋疼的 ure 不能直接获取匹配结果的数量, 只能使用这种蠢蛋方法来循环.
        #     try:
        #         text = m.group(i)

        #     except:
        #         # 发生错误说明已经遍历完毕
        #         break

        #     # 使用指针代替文本来减少开销
        #     if text == "level":
        #         self._map.append(_level)
        #     elif text == "msg":
        #         self._map.append(_msg)
        #     elif text == "time":
        #         self._map.append(_time)
        #     elif text == "name":
        #         self._map.append(_name)
        #     elif text == "fnname":
        #         self._map.append(_fnname)

        #     i += 1

        # 添加映射
        self._map = bytearray()
        idx = 0
        while True:
            idx = fmt.find("&(", idx)
            if idx >= 0:  # 有找到
                a_idx = fmt.find(")%", idx+2)
                if a_idx < 0:
                    # 没找到后缀, 报错
                    raise Exception(
                        "Unable to parse text format successfully.")
                text = fmt[idx+2:a_idx]
                idx = a_idx+2  # 交换位置
                if text == "level":
                    self._map.append(_level)
                elif text == "msg":
                    self._map.append(_msg)
                elif text == "time":
                    self._map.append(_time)
                elif text == "name":
                    self._map.append(_name)
                elif text == "fnname":
                    self._map.append(_fnname)
            else:  # 没找到, 代表后面没有了
                break

        # 将 template 变成可被格式化的文本
        # 确保最后一个是换行字符

        self._template = fmt.replace("&(level)%", "%s")\
            .replace("&(msg)%", "%s")\
            .replace("&(time)%", "%s")\
            .replace("&(name)%", "%s")\
            .replace("&(fnname)%", "%s")\
            + "\n" if fmt[:-1] != '\n' else ''

    def _msg(self, *args, level: int, name: str, fnname: str):
        """
        Log a msg
        """
        
        if level < self.level:
            return
        # generate msg
        temp_map = []
        text = ''
        for item in self._map:
            if item == _msg:
                for text_ in args:  # 将元组内的文本添加到一起
                    text = "%s%s" % (text, text_)  # 防止用户输入其他类型(int, float)
                temp_map.append(text)
            elif item == _level:
                if self._direction == TO_TERM:  # only terminal can use color.
                    temp_map.append(level_name(level, self._color))
                else:
                    temp_map.append(level_name(level))
            elif item == _time:
                temp_map.append(self._clock())
            elif item == _name:
                temp_map.append(name)
            elif item == _fnname:
                temp_map.append(fnname if fnname else "unknownfn")

        if self._direction == TO_TERM:
            self._to_term(tuple(temp_map))
        else:
            self._to_file(tuple(temp_map))
        # TODO: 待验证: 转换为 tuple 和使用 fromat 谁更快

    def _to_term(self, map: tuple):
        print(self._template % map, end='')

    def _to_file(self, map: tuple):
        fp = self._file
        # 检查是否超出大小限制.
        prev_idx = fp.tell()  # 保存原始指针位置
        # 将读写指针跳到文件最大限制的地方,
        # 如果能读出数据, 说明文件大于指定的大小
        fp.seek(self._max_size)
        if fp.read(1):  # 能读到数据, 说明超出大小限制了
            fp = self._file = open(self._file_name, 'w')  # 使用 w 选项清空文件内容
        else:
            # 没有超出限制
            fp.seek(prev_idx)  # 指针回到原来的地方

        # 检查完毕, 开始写入数据
        fp.write(self._template % map)
        fp.flush()


class Logger():
    _handlers: list

    def __init__(self,
        name: str,
        handlers: list = None,
        ):

        self.name = name
        if not handlers:
            # 如果没有指定处理器, 自动创建一个默认的
            self._handlers = [Handler()]
        else:
            self._handlers = handlers

    @property
    def handlers(self):
        return self._handlers

    def _msg(self, *args, level: int, fn: str):

        for item in self._handlers:
            #try:
            item._msg(*args, level=level, fnname=fn, name=self.name)
            #except:
            #    print("Failed while trying to record")

    def debug(self, *args, fn: str = None):
        self._msg(*args, level=DEBUG, fn=fn)

    def info(self, *args, fn: str = None):
        self._msg(*args, level=INFO, fn=fn)

    def warn(self, *args, fn: str = None):
        self._msg(*args, level=WARN, fn=fn)

    def error(self, *args, fn: str = None):
        self._msg(*args, level=ERROR, fn=fn)

    def critical(self, *args, fn: str = None):
        self._msg(*args, level=CRITICAL, fn=fn)


__all__ = [
    Logger,
    Handler,
    BaseClock,


    DEBUG,
    INFO,
    WARN,
    ERROR,
    CRITICAL,

    TO_FILE,
    TO_TERM,

    __version__
]
