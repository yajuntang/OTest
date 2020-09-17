

from library.application.AndroidApp import AndroidApp
from src.page.demo_page import DemoPage



pages = [DemoPage]

app = AndroidApp("com.otest.android")
app.start_test(pages, device_id="LMA710EAW83530563")
# app.start_test(pages, ip="127.0.0.1", port="7555")
# app.start_test(pages, device_id="emulator-5554")#模拟器


# app = IOSApp("com.otest.ios")
# app.start_test(pages, ip="127.0.0.1", port="8100")
# app.start_test(pages) # 不写就使用默认值的


# export PYTHONPATH=$PYTHONPATH:./library
# alias python3="/usr/local/bin/python3"
