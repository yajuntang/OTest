# OTest

### 快速使用
* 第一步   
在 src/pages 目录下 新建一个 DemoPage 继承 TestPage   
![图片](https://github.com/yajuntang/OTest/tree/master/server/static/guide_images/01.png)  
* 第二步   
运行 server 目录下的 manager.py   
![图片](https://github.com/yajuntang/OTest/tree/master/server/static/guide_images/02.png)  
* 第三步   
新建一个版本计划,在这里可以单独为每一个页面或测试方法配置变量   
![图片](https://github.com/yajuntang/OTest/tree/master/server/static/guide_images/03.png)  
![图片](https://github.com/yajuntang/OTest/tree/master/server/static/guide_images/04.png)  
![图片](https://github.com/yajuntang/OTest/tree/master/server/static/guide_images/05.png)  
* 第四步   
新建一个测试计划,并选择你要测试的界面，每一个测试计划可以为所选择的测试页面配置全局变量，注意，如果变量与页面所配置的变量相同，会覆盖其变量   
![图片](https://github.com/yajuntang/OTest/tree/master/server/static/guide_images/06.png)  
![图片](https://github.com/yajuntang/OTest/tree/master/server/static/guide_images/07.png)  
* 第五步   
选择Android，新建一个包名并选择它。执行一个测试的用例或用例组。   
![图片](https://github.com/yajuntang/OTest/tree/master/server/static/guide_images/08.png)  
![图片](https://github.com/yajuntang/OTest/tree/master/server/static/guide_images/09.png)  
![图片](https://github.com/yajuntang/OTest/tree/master/server/static/guide_images/10.png)  
### API
目前这里只列出测试开发中会用到的API   
* App   
有两个子类，分别为AndroidApp 和 IOSApp   
     * start_app   
      启动App   
     * stop_app   
      停止App   
     * start_test   
      开始测试，ip和port IOS默认的是 127.0.0.1:8081。Android 无默认值   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      pages | 测试页面的对象可以是 class对象或者 PageData 对象，必须是继承 TestPage 的 class | 无   
      ip | 设备IP地址 | None   
      port | 设备端口 | None   
      device_id | 设备ID | None   
* TestPage   
测试页面，所有的测试脚本都必须继承这个类   
     * setUpClass   
      所有的测试方法运行前运行，为单元测试做前期准备,整个测试页面只执行一次   
     * tearDownClass   
      所有的测试方法运行结束后运行，为单元测试做后期清理工作,整个测试页面只执行一次   
     * setUp   
      每个测试方法运行前运行，测试前的初始化工作。一条用例执行一次，若N次用例就执行N次，根据用例的数量来定。默认是执行 stop_app 和 start_app，如果你不想这样处理，可在子类中覆盖此方法   
     * tearDown   
      每个测试方法运行结束后运行，测试后的清理工作。一条用例执行一次，若N次用例就执行N次。 默认是执行 stop_app，如果你不想这样处理，可在子类中覆盖此方法   
     * is_ios_device   
      返回当前运行的平台是 True 为IOS，False 为Android   
     * scroll_down   
      页面往下滚动一段距离   
     * wait_stable   
      等待稳定状态，实际上只是sleep了0.8秒   
     * set_ui   
      如果你的UI对象不是在__init__中初始化的，比如是方法的本地变量，那么在本地变量初始化后之后，调用此方法，进行设置。self.set_ui(UI)   
     * freeze   
      冻结页面，也就是dump一份页面的数据，使用它来查找效率会快很多，缺点是在时效性只有在调用它的那一刻，之后的手机上的UI更新不会同步到这里   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [] Airtest   
      - [x] poco   
     * wait_for_any   
      等待任意一个元素出现，目前只支持poco   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      objects | 需要等待的元素的集合，必填 | 无   
      timeout | 等待时长 | 120秒   
     * wait_for_all   
      等待所有的元素都出现，目前只支持poco   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      objects | 需要等待的元素的集合，必填 | 无   
      timeout | 等待时长 | 120秒   
     * assert_for_any   
      断言任意一个元素出现，组合操作，wait_for_any + assert_exists   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      objects | 需要等待的元素的集合，必填 | 无   
      msg | 断言的描述 | 无   
      timeout | 等待时长 | 120秒   
     * scroll   
      滑动，使用poco实现   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      direction | 滑动方向 'up', 'down', 'left', 'right'，必填 | 无   
      focus | 滑动的焦点["anchor","center",(x:0 - 1, y:0 - 1)] | anchor   
      duration | 滑动时长 | 0.5秒   
     * pinch   
      缩放，使用poco实现   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      direction | 滑动方向 'in', 'out' | in   
      percent | 滑动的距离，宽或高的百分比 0 - 0.1 | 0.3   
      duration | 滑动时长，单位秒 | 1秒   
      dead_zone | 缩放的半径,请不要超过 1 | 0.1   
     * snapshot   
      截图，使用poco实现   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      fileName | 图片名字，默认是截图.jpg | None   
      msg | 图片的描述，以便于在报告上查看 | ""   
     * assert_equal   
      断言两者是相等   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      first | 必填 | 无   
      second | 必填 | 无   
      msg | 断言描述 | ""   
     * assert_not_equal   
      断言两者不相等   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      first | 必填 | 无   
      second | 必填 | 无   
      msg | 断言描述 | ""   
     * get_screen_size   
      获取屏幕大小   
* UI   
节点对象   
     * wait_for_appearance   
      等待元素出现，默认等待超时120秒，Airtest 找不到对象会抛出 TargetNotFoundError，Poco 则是抛出 PocoTargetTimeout   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      timeout | 等待时长 | 120秒   
     * wait_for_disappearance   
      等待元素消失，默认等待超时120秒,规定时间内 对象仍然存在，则会抛出 PocoTargetTimeout('disappearance', self)   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      timeout | 等待时长 | 120秒   
     * click   
      执行该元素的点击事件， 如果点击时 元素不存在，会尝试第二次，时间间隔2秒   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
     * exists   
      判断元素是否存在   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      is_retry | 报错后是否尝试,默认会重试 | True   
      sleeps | 重试间隔，单位秒 | 2秒   
      max_attempts | 重试次数 | 2次   
     * wait_click   
      组合操作，wait_for_appearance + click   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      timeout | 等待时长 | 120秒   
     * wait_exists   
      组合操作，wait_for_appearance + exists   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      timeout | 等待时长 | 120秒   
     * swipe   
      滑动，使用poco实现   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      direction | 滑动方向 'up', 'down', 'left', 'right'，必填 | 无   
      focus | 滑动的焦点["anchor","center",(x:0 - 1, y:0 - 1)] | anchor   
      duration | 滑动时长 | 0.5秒   
     * airtest_swipe   
      滑动，使用Airtest实现   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [] poco   
      参数名称 | 描述 | 默认值   
      v2 | 滑动目的对象:Template/pos'  | None   
      vector | 滑动目的坐标(x:-1 - 1, y:-1 - 1) | None   
      duration | 滑动时长 | 0.5秒   
     * sendKeys   
      发送文字到文本输入框,这是一个组合操作   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      keys | 需要发送的数据 | 无   
      enter | 回车 | True   
     * clear   
      清空输入框，但只支持Android   
      平台支持:   
      - [x] android   
      - [] ios   
      测试框架支持:   
      - [] Airtest   
      - [x] poco   
     * find   
      查找元素是否存在，如果找找不到会往所设的方向，滑动一段距离继续查找，直至被找到或超时。适用于滚动的视图或者列表   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      direction | 滑动方向，默认为竖直方向 | 'vertical'   
      percent | 滑动的距离，宽或高的百分比 0 - 0.1 | 0.3   
      duration | 滑动时长，单位秒 | 1秒   
      timeout | 等待时长 | 120秒   
     * assert_not_exists   
      断言元素不存在   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      msg | 断言描述 | ""   
     * assert_exists   
      断言元素存在   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      msg | 断言描述 | ""   
     * child   
      从元素中获取指定描述的子元素   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      name | 元素的 name | None   
      attrs | 元素的 属性 | 无   
     * children   
      从元素中获取子元素集合   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
     * offspring   
      从元素中获取指定描述的后代   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      name | 元素的 name | None   
      attrs | 元素的 属性 | 无   
     * sibling   
      从元素中获取指定描述的兄弟元素   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
      参数名称 | 描述 | 默认值   
      name | 元素的 name | None   
      attrs | 元素的 属性 | 无   
     * parent   
      获取该元素的父元素   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [x] Airtest   
      - [x] poco   
     * freeze   
      冻结页面并从该页面查找改元素，也就是dump一份页面的数据，使用它来查找效率会快很多，缺点是在时效性只有在调用它的那一刻，之后的手机上的UI更新不会同步到这里   
      平台支持:   
      - [x] android   
      - [x] ios   
      测试框架支持:   
      - [] Airtest   
      - [x] poco   


听说长得好看的人都会点star哦
