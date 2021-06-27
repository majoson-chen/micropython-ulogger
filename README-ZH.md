# micropython-ulogger
 在 `micropython` 上做logging不是一件容易的事情,  `micropython` 有很多尚未完成的接口, 因此能记录到的日志内容非常有限, 我根据 `micropython` 的情况设计了这个 `ulogger` 的库.

[English](./README.md)|**简体中文**  
![LOGO](./src/logo_transparent.png)

## 特色:
在 `micropython` 中, 由于单片机的计算能力有限, 一切事情都需要快速地被处理和响应, 因此本模块设计的目的就是减少无所谓的操作. 因此本模块会和 `CPython` 的标准库 `logging` 有很大的不同.



## 如何安装?
### 通过 `pypi` 安装
```python
#repl on your board
import upip
upip.install("micropython-ulogger")
```

### 手动安装(推荐)

请在本项目的 [release](https://github.com/Li-Lian1069/micropython-ulogger/releases) 中下载一个最新版的`.mpy`文件, 将其放到开发板的 `/lib` 目录中或您程序的目录中.

**注意**: 推荐使用 `.mpy` 的文件, 这是针对 `micropython` 已经事先编译好的文件, 可以有效提高执行速度和内存开销.



## 如何使用?
### 快速入门
这是一个最简单的例子:
```python
import ulogger
loggor = ulogger.Loggor(__name__)
loggor.info("hello world")
```
在上面的例子中, 一切将会使用默认的参数(级别为INFO, 输出到终端中.)


### Handler的使用
**现在. 我们来给他加点料**
```python
import ulogger

handler_to_term = ulogger.Handler(
    level=ulogger.INFO,
    colorful=True,
    fmt="&(time)% - &(level)% - &(name)% - &(fnname)% - &(msg)%",
    clock=None,
    direction=ulogger.TO_TERM,
)
handler_to_file = ulogger.Handler(
    level=ulogger.INFO,
    fmt="&(time)% - &(level)% - &(name)% - &(fnname)% - &(msg)%",
    clock=None,
    direction=ulogger.TO_FILE,
    file_name="logging.log",
    max_file_size=1024 # max for 1k
)
logger = ulogger.Logger(
    name = __name__,
    handlers = (
        handler_to_term,
        handler_to_file
    )
)

logger.info("hello", "world")
# 支持多参数填入
```
在 `ulogger` 中, 有一点与 `CPython` 的 `logging` 模块不一样: 在 `logging` 模块中, `formatter` 和 `handler` 是分开的, 但是在本模块中, 我将两者合为一体, 这可以减少日志模块的工作量(你肯定不希望你的开发板花费太多时间在记录日志吧!), 当然这会减少可配置性, 但是我们总是要为了提高性能付出一点代价.



#### Handler可以使用的参数:
```python
# default args
ulogger.Handler(
    level: int = INFO,
    colorful: bool = True,
    fmt: str = "&(time)% - &(level)% - &(name)% - &(msg)%",
    clock: BaseClock = None,
    direction: int = TO_TERM,
    file_name: str = "logging.log",
    max_file_size: int = 4096
)

```
- level: 指定这个Handler接受的最低等级, 可选:
  - ulogger.DEBUG
  - ulogger.INFO
  - ulogger.WARN
  - ulogger.ERROR
  - ulogger.CRITICAL
  
- colorful: 指定是否启用控制台文本颜色(仅在 `direction=TO_TERM` 时可用)

- fmt: 设置输出的文本格式, 支持内置变量, 目前支持:
  - `&(time)%`: 打印时间戳, 关于时间的格式详见 `clock` 参数. 
  - `&(level)%`: 打印消息的级别
  - `&(name)%`: 打印Logger的名字, 在实例化Logger时提供.
  - `&(fnname)%`: 打印函数名, 由于`micropython`目前尚未支持 `traceback` 和更高级的错误管理, 因此需要手动提供信息. 如果在调用记录时未提供本项, 默认值为 `unknownfn`, 例子:
  ```python
  def hello():
    logger.info("in hello", fn=hello.__name__)
    # or
    logger.info("in hello", fn="hello")
    # or fill in what you want
    logger.info("in hello", fn="world")
  ```
  - `&(msg)%`: 打印消息, 即你在 `info()` 中填入的信息
  
- clock: 由于单片机没有一直通电的 `rtc` 模块, 因此它的时间并不一定是与国际时间同步的, 因此我们开放了时钟接口, 当每次需要记录 `&(time)%` 的时候我们会从这个时钟中获取时间

- direction: 设置文本输出的方向, 可选 `TO_TERM`(输出到终端) 或 `TO_FILE`(输出到文件)

- file_name: 输出的文件名, 在 `TO_FILE` 时才会被启用, 可以是相对路径也可以是绝对路径.

- max_file_size: 设置最大文件大小(单位:byte), 当文件大小超过上限的时候, 我们会自动清空文件.



### Clock的使用
也许你已经注意到在 `Handler` 中的 `clock` 参数, 我们提供了一个自定义时间输出格式的接口, 您只需要继承 `BaseClock` 这个类即可自定义您的时钟.

例子:

```python
import ntptime, machine, time
class RealClock(ulogger.BaseClock):
    def __init__ (self):
        self.rct = machine.RTC ()
        ntptime.settime()  # 获取并设置网络时间
        # * 注意: 此处获取的是国际标准时间
        # * 关于RTC模块的更多信息, 详见: 
        # http://docs.micropython.org/en/latest/library/machine.RTC.html#machine.RTC

    def __call__(self) -> str:
        # 当需要获取时间时, 此函数会自动被调用, 并将其返回值作为时间戳文本.
        # self.rtc.datetime () -> (year, month, day, weekday, hours, minutes, seconds, subseconds)
        y,m,d,_,h,mi,s,_ = self.rtc.datetime ()

        return '%d-%d-%d %d:%d:%d' % (y,m,d,h,mi,s)
    	# 在 micropython 中, 使用 '%' 格式化文本是最快的处理方式,
        # 详见: https://blog.m-jay.cn/?p=329
```

如果您想自定义您的时区, 可以按照以下方法: 

```python
def __init__ (self):
        self.rct = machine.RTC ()
        # now = ntptime.time ()
        # tp_time = time.localtime (now)
        # self.rtc.init (tp_time)
        self.rtc.init (
            time.localtime (
                ntptime.time () + 28800  # 增加八小时(北京时间)
            )
        )
```

原理就是在获取的网络时间上增加或减去相应的时间, 例如北京时间(+8), 就增加 60\*60\*8=28800秒



### 一份完整的示例代码:

```python
import ulogger

# Example for esp8266 & esp32
from machine import RTC
import ntptime
class Clock(ulogger.BaseClock):
    def __init__(self):
        self.rtc = RTC()
        ntptime.host = "ntp.ntsc.ac.cn"  # 设置更快的ntf服务器, 可以减少延迟
        ntptime.settime()
        
    def __call__(self) -> str:
        y,m,d,_,h,mi,s,_ = self.rtc.datetime ()
        return '%d-%d-%d %d:%d:%d' % (y,m,d,h,mi,s)

clock = Clock()
handler_to_term = ulogger.Handler(
    level=ulogger.INFO,
    colorful=True,
    fmt="&(time)% - &(level)% - &(name)% - &(fnname)% - &(msg)%",
    clock=clock,
    direction=ulogger.TO_TERM,
)

handler_to_file = ulogger.Handler(
    level=ulogger.INFO,
    fmt="&(time)% - &(level)% - &(name)% - &(fnname)% - &(msg)%",
    clock=clock,
    direction=ulogger.TO_FILE,
    file_name="logging.log",
    max_file_size=1024 # max for 1k
)
logger = ulogger.Logger(
    name = __name__, 
    handlers = (handler_to_term, handler_to_file)
    )

logger.info("hello world")
```

## 程序结构
- 常量:
  - 适用于level:
    - DEBUG
    - INFO
    - WARN
    - ERROR
    - CRITICAL
  - 适用于direction:
    - TO_FILE
    - TO_TERM
  - VERSION

- class Logger
  - 公开方法:
    - \_\_init\_\_(name, handlers: Iterable)
    - debug(*args, fn: str)
    - info(*args, fn: str)
    - warn(*args, fn: str)
    - error(*args, fn: str)
    - critical(*args, fn: str)
  - 公开属性
    - handlers: list

- class Handler
  - 公开方法:
    - \_\_init\_\_(level, colorful, fmt, clock, direction, file_name, max_file_size)
  - 公开属性
    - level: 通过修改它来控制输出级别.

- class BaseClock
  - 公开方法:
    - \_\_call\_\_()



## 设计指南
### 将其封装为模块

在每一个 `python` 文件里都单独配置一个 `Clock` 或者 `Handler` 是不太科学的, 而且会占据大量空间, 因此我们建议将其封装为一个模块来使用, 例子:

```python
# loguitl.py
import ulogger

from machine import RTC
import ntptime
class Clock(ulogger.BaseClock):
    def __init__(self):
        self.rtc = RTC()
        ntptime.host = "ntp.ntsc.ac.cn"  # 设置更快的ntf服务器, 可以减少延迟
        ntptime.settime()
        
    def __call__(self) -> str:
        y,m,d,_,h,mi,s,_ = self.rtc.datetime ()
        return '%d-%d-%d %d:%d:%d' % (y,m,d,h,mi,s)
clock = Clock()
    
handlers = (
    ulogger.Handler(
        level=ulogger.INFO,
        colorful=True,
        fmt="&(time)% - &(level)% - &(name)% - &(fnname)% - &(msg)%",
        clock=clock,
        direction=ulogger.TO_TERM,
    ),
    ulogger.Handler(
        level=ulogger.ERROR,
        fmt="&(time)% - &(level)% - &(name)% - &(fnname)% - &(msg)%",
        clock=clock,
        direction=ulogger.TO_FILE,
        file_name="logging.log",
        max_file_size=1024 # max for 1k
    )
)

def get_logger(name: str):
    return ulogger.Logger(name, handlers)
all = (get_logger)
```

**注意:** 上面将两个 `Handler` 保存到一个 `tuple` 中, 这样当多次调用 `get_logger` 的时候就可以避免发生多次内存分配. 你告诉我在嵌入式设备上运行的代码怎么设计? 我会告诉你 **能省则省**

### 减少 IO 操作

IO操作一直以来就是计算机中最慢的一环, 在单片机上更是如此, 因此, 您可以:

- 减少打印不必要的信息

- 简化 `Handler` 的 `fmt` 模板(输出更少的内容)

- 将 `TO_FILE` 的级别设置为更高: `ERROR` 或 `CRITICAL`

- 使用更高效的文本处理方式(最高可提速`400%`)  
  详见: [micropython中处理文本最快的方法 - M - Jay 的个人博客](https://blog.m-jay.cn/?p=329)

### 代码提示
你可以在你编写代码的计算机中安装本模块来启用编辑器的代码提示功能:
```shell
pip install micropython-ulogger
```