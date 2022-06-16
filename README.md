# micropython-ulogger
Logging on `micropython` is not an easy task. `micropython` has many unfinished interfaces, so the log content that can be recorded is very limited. I designed this `ulogger` library based on the situation of `micropython`. 

**Note:** This article uses `Google Translate` as a reference. There may be many ambiguities due to inaccurate translations. Welcome to submit a pull request.  

**English**|[简体中文](./README-ZH.md)
![LOGO](./src/logo_transparent.png)

## Features:
In `micropython`, due to the limited computing power of the single-chip microcomputer, everything needs to be processed and responded quickly, so the purpose of this module is to reduce worthless operations. Therefore, this module will be more differences with the standard library `logging` of `CPython`.



## How to install?
### by `pypi`
```python
#repl on your board
import upip
upip.install("micropython-ulogger")
```

### by manually
Please download the latest version of `.mpy` file in the [release](https://github.com/Li-Lian1069/micropython-ulogger/releases) of this project, and put it in the `/lib` directory of the development board or the directory of your program. 



## How to use?
### quick-start
This is the simplest example:
```python
import ulogger
loggor = ulogger.Logger(__name__)
loggor.info("hello world")
```


### About Handler
**Now. Let's give it some condiment**
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
# Support multi-parameter filling.
```

In `ulogger`, one thing is different with the `logging` module of `CPython`: In the `logging` module, `formatter` and `handler` are separate, but in this module, I combine them into One, this can reduce the workload of this module (you certainly don't want your development board to spend too much time to recording logs!), of course, this will reduce configurability, but we always have to pay a little price for improving performance. 



#### The params Handler can use:
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
- level: Specify the lowest level accepted by this Handler, optional:
  - ulogger.DEBUG
  - ulogger.INFO
  - ulogger.WARN
  - ulogger.ERROR
  - ulogger.CRITICAL
  
- colorful: Specify whether to enable the color of the console text (only available when `direction=TO_TERM`)

- fmt: Set the output text format, support built-in variables, currently supports:
  - `&(time)%`: Print the timestamp, see the `clock` parameter for the time format.
  - `&(level)%`: print the level of the message
  - `&(name)%`: Print the name of the Logger, which is provided when the Logger is instantiated.
  - `&(fnname)%`: Print function name, because `micropython` does not support `traceback` currently and more advanced error management, so you need to provide information manually. If this item is not provided when calling the record, the default value is `unknownfn`, example:
  ```python
  def hello():
    logger.info("in hello", fn=hello.__name__)
    # or
    logger.info("in hello", fn="hello")
    # or fill in what you want
    logger.info("in hello", fn="world")
  ```
  - `&(msg)%`: print the message, that is, the information you filled in `info()`
  
- clock: Because the MCU does not have the `rtc` module that is always powered on, its time is not necessarily synchronized with the international time, so we open the clock interface, when we need to record `&(time)%` every time will get the time from this clock

- direction: Set the direction of text output, optional `TO_TERM`(output to terminal) or `TO_FILE`(output to file)

- file_name: The output file name, which will only be enabled when `TO_FILE`, and it can be a relative path or an absolute path.

- max_file_size: Set the maximum file size (unit: byte), when the file size exceeds the upper limit, we will automatically empty the file. 


### About Clock
Perhaps you have noticed the `clock` parameter in `Handler`, we provide an interface for customizing the time output format, you only need to inherit the `BaseClock` class to customize your clock. 

For Example:
```python
import ntptime, machine
class RealClock(ulogger.BaseClock):
    def __init__ (self):
        self.rct = machine.RTC ()
        ntptime.settime()  # Get and set network time 
        # * Note: Get here is the international standard time 
        # * For more information about the RTC module, see: 
        # http://docs.micropython.org/en/latest/library/machine.RTC.html#machine.RTC

    def __call__(self) -> str:
        # When we need to get the time, this function will be called automatically, and its return value will be used as the timestamp text.

        # self.rtc.datetime () -> (year, month, day, weekday, hours, minutes, seconds, subseconds)
        y,m,d,_,h,mi,s,_ = self.rtc.datetime ()
        return '%d-%d-%d %d:%d:%d' % (y,m,d,h,mi,s)
    	# In micropython, formatting text with'%' is the fastest way to process it. 
        # See details at: https://blog.m-jay.cn/?p=329
```
If you want to customize your time-zone, you can follow this methods: 
```python
def __init__ (self):
        self.rct = machine.RTC ()
        # now = ntptime.time ()
        # tp_time = time.localtime (now)
        # self.rtc.init (tp_time)
        self.rtc.init (
            time.localtime (
                ntptime.time () + 28800  # Add eight hours (Beijing time) 
            )
        )
```
The principle is to add or subtract the corresponding time from the obtained network time, for example, Beijing time (+8), add 60\*60\*8=28800 seconds




### A complete sample code: 
```python
import ulogger

# Example for esp8266 & esp32
from machine import RTC
import ntptime
class Clock(ulogger.BaseClock):
    def __init__(self):
        self.rtc = RTC()
        ntptime.host = "ntp.ntsc.ac.cn"  # Setting up a faster ntf server can reduce latency
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




## Structure
  - Constants:
    - use for level:
      - DEBUG
      - INFO
      - WARN
      - ERROR
      - CRITICAL
    - use for direction:
      - TO_FILE
      - TO_TERM
    - VERSION

  - class Logger
    - Public_Methods:
      - \_\_init\_\_(name, handlers: Iterable)
      - debug(*args, fn: str)
      - info(*args, fn: str)
      - warn(*args, fn: str)
      - error(*args, fn: str)
      - critical(*args, fn: str)
    - Public_Attributes
      - handlers: list

  - class Handler
    - Public_Methods:
      - \_\_init\_\_(level, colorful, fmt, clock, direction, file_name, max_file_size)
    - Public_Attributes
      - level: change it to modify level.

  - class BaseClock
    - Public_Methods:
      - \_\_call\_\_()


## Design Guidelines
### Encapsulate it as a module 

It is not scientific to configure a Clock or Handler separately in each python file, and it will take up a lot of space, so we recommend encapsulating it as a module for use, for example: 

```python
# loguitl.py
import ulogger

from machine import RTC
import ntptime
class Clock(ulogger.BaseClock):
    def __init__(self):
        self.rtc = RTC()
        ntptime.host = "ntp.ntsc.ac.cn"
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

**Note:** The above saves two `Handler` into a `tuple`, so that multiple memory allocations can be avoided when `get_logger` is called multiple times. If you ask me embedded devices How to design the faster code? I will tell you **can save, just save** 

### Reduce IO operations

IO operation has always been the slowest part of the computer, especially on the microcontroller. Therefore, you can:

- Reduce printing unnecessary information
- Simplified `fmt` template of `Handler` (output less content)
- Set the level of `TO_FILE` to a higher level: `ERROR` or `CRITICAL`
- Use more efficient text processing methods (up to `400%` faster)  
  See : [The fastest way to process text in micropython ](https://blog.m-jay.cn/?p=329)

### Code hint
You can install this module on the computer where you write the code to enable the editor's code hint function:
```shell
pip install micropython-ulogger
``` 
