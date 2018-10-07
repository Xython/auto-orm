

## Auto-ORM

## 简介

auto-orm 使用一个很小的DSL(`dbg script`)用来管理数据库Schema.

其主要目的是, 让使用者以尽量少的精力对Schema进行重构和维护.

auto-orm的一个价值显著的feature是它与IDE契合良好.虽然大量ORM框架提供了运行时的Python类型映射, 但却少有对检查工具
的支持.auto-orm相当好地支持了静态检查, 从而有效帮助用户在运行之前发现程序错误.

同时, 对Schema的静态分析是可以扩展的, 从而能够让用户对数据库添加更多的自定义约束.

auto-orm 需要绑定一个ORM后端工作(为了简便和稳定).

目前来说, auto-orm更多的意义是提供一些新鲜的思路和DSL作用的展示, 因为在实际应用中, 它在功能上有部分缺失, 例如没有联合主键等.
扩展它以支持更多的特性是可以的, 但一旦稍微复杂起来, 就偏离了本意.

- 使用: 使用setup.py安装后, 使用命令`dbg gen <dbg脚本文件名> <生成python文件名>`

## 核心DSL说明

`dbg-script`是 auto-orm 所用的核心语言. 它能够直观简洁地对表和关系进行定义, 也可以把Python嵌入.
编译它会产生对应的Python代码, 为我们提供很多便利安全的API.

- Engine初始化参数
```
engine {
     url = "sqlite:///:memory:"
     # url = "mysql+pymysql://root:12345@localhost/test?charset=utf8"
     # 其他的keyword参数, 用于sqlalchemy.engine.create_engine
}
```

- 表和字段

通过表名、主键和字段进行定义.

```
<TableName>{
   data1: Integer?
   data2: Float~
   data3: DateTime!
   data4: String(30)
}
```
对于一张表会提供一个默认字段`id`, 其非空、自增.

当前实现中, 支持[sqlalchemy的数据类型](https://docs.sqlalchemy.org/en/latest/core/type_basics.html).

数据类型后可以添加后缀修饰符:

|  修饰符   | 含义      |
|-----------|----------|
| ~         | sequence |
| !         | unique   |
| ?         | optional |

字段默认情况下是不可空的, 可空类型一定需要用`?`标记.

- 默认值

```
MyType {
   value: Integer = 42
}
```

- Python representation

定义被Python的`repr`渲染的字段:

```
MyType{

   value1: Integer = 42,
   value2: String(30),
   value3: String(40)

   repr {id, value1, value2}
}
```

(下面的代码看起来和普通的sqlalchemy没什么差别, 但当你真正在IDE里尝试后应该会觉得相当畅快)

```python
from my_generated_module import *
obj = MyType(value2="v2", value3="v3")
session.commit()
print(obj)

# MyType(id = 1, value1 = 42, value2 = 'v2')
```

发现并不显示`value3='v3'`.

repr默认打印所有的字段, 但有时要debug数据库, 只打印指定部分会非常人性化(想想10+个字段, 这是相当常见的).



- 嵌入python与枚举类型

```
python
    from enum import Enum
    class MyEnum(Enum):
        cpython = 0
        pypy = 1
        ironpython = 2
        jython = 3

MyType{
    v1 : enum MyEnum,
    v2 : DateTime
}
```
效果如下:

```python
from my_generated_module import *
from datetime import datetime
obj = MyType(v1=MyEnum.ironpython, v2=datetime.now())
session.add(obj)
session.commit()
print(obj)

# MyType(id = 1, v1 = <MyEnum.ironpython: 2>, v2 = datetime.datetime(2018, 10, 8, 4, 59, 34, 710011))
```

- 定义关系
```

Person {
 name: String(20)

}

Cost {
  amount: Float
}

Person with Cost {
    time: DateTime
}
```

效果:

```python
from my_generated_module import *
from datetime import datetime

marisa = Person(name="marisa")
cost = Cost(amount=100.0)

session.add(marisa)
session.add(cost)
session.commit()

marisa.add_rel_with_cost(cost, time=datetime.now())
session.commit()

print(PersonCost.query.filter(PersonCost.id == marisa.id).all())

# => [PersonCost(person_id = 1, cost_id = 1, time = datetime.datetime(2018, 10, 8, 4, 59, 58, 623655))]
```

由于时间、精力原因, 我只实现了具有中间表的关系, 一般而言中间表被Many-To-Many使用, 但实际上出于解耦的目的, 中间表也是可以用来描述其他关系的.

获取一个对象`obj`对某一个类型B(表名b)的中间关系, 使用
```python
obj.rel_$b : Query[B]
```
至于`Query`泛型有什么方法, 赶快拿起IDE进行欢快的链式调用吧!
值得注意的是, 通过`rel_xxx`获取的中间关系都是激活的.


- 取消激活以及依赖伪删除

伪删除似乎使用得极为广泛, 虽然我对相关开发不甚熟悉, 但实际所见的几次, 项目都是用的伪删除.

伪删除指的是使用激活状态来表示数据是否可用.而真正的删除数据可能需要在其他时间执行.

auto-orm用所有权来描述伪删除的依赖关系, 所有对象的激活状态均使用字段`dbg_is_status_activated`.

诚然这个字段很长, 但是因为有非常舒适的补全, 这不是什么大事.

这个字段被设计得很长的rational原因是有的. 在python中无法轻松地做name mangling, 从而有必要在dbg-script中使用一些保留字.
太过正常的保留字会阻止用户写正常的字段名.

下面我们看一个例子:
```

Person {
 name: String(20)

}

Cost {
  amount: Float
}

Person^ with Cost {
    time: DateTime
}

```

上述dbg代码表示Person对于Cost有所有权. `^`表示具有所有权的一方.

当一个Cost对象被取消激活时, 仅它和它持有的关系被取消激活.

而当Person对象取消激活时, 将取消激活关系另一端的对象与关系本身.


```python
from my_generated_module import *
from datetime import datetime, timedelta
marisa = Person(name="marisa")
cost1 = Cost(amount=100.0)
cost2 = Cost(amount=50.0)

session.add(marisa)
session.add(cost1)
session.commit()

marisa.add_rel_with_cost(cost1, time=datetime.now())
marisa.add_rel_with_cost(cost2, time=datetime.now() + timedelta(days=200.0))
session.commit()

print(marisa.rel_cost.all())
#=> [
#   PersonCost(person_id = 1, cost_id = 1, time = datetime.datetime(2018, 10, 8, 5, 23, 14, 440808)),
#   PersonCost(person_id = 1, cost_id = None, time = datetime.datetime(2019, 4, 26, 5, 23, 14, 442297))
#   ]
print(Person.query.filter(Person.dbg_is_status_activated == 1).all())
# => [Person(id = 1, name = 'marisa')]

cost2.deactivate()
session.commit()
print(marisa.rel_cost.all())
# [PersonCost(person_id = 1, cost_id = 1, time = datetime.datetime(2018, 10, 8, 5, 23, 14, 440808))]
print(Person.query.filter(Person.dbg_is_status_activated == 1).all())
# [Person(id = 1, name = 'marisa')]

marisa.deactivate()
session.commit()
print(marisa.rel_cost.all())
# => []
print(Person.query.filter(Person.dbg_is_status_activated == 1).all())
# => []
print(Cost.query.filter(Cost.dbg_is_status_activated == 1).all())
# => []
```

有一种特殊的例子是双方都具有所有权.
我们知道人活在世界上其实很多时候要靠其他事情来证明存在，
而这些事情恰恰又依赖于人而存在.

这里就有一个例子:

有一群元气少女, 她们分别是:
- **稳重成熟**
- **端茶送水**
- **威严满满**
- **称职门卫**

她们的居处在某某乡1到13个分区.

假如这13个地方没有了, 她们就会无处可去消失在这世界上.
而如果她们都不在了, 这13个地方也就成了无人可以达到的失落之地.

上述关系使用dbg-script可以这样描述

```
# test.dbg
# actually, not maiden :-)

Spirit { name: str }
Site   {}

Spirit^ with ^Site {
    time: DateTime
}
```

然后我们用`dbg gen -i test.dbg -o my_generated_module.py`生成python模块, 来描述上述问题:

```python
from test_orm import *
from random import random

s1 = Spirit(name='威严满满')
s2 = Spirit(name='稳重成熟')
s3 = Spirit(name='称职门卫')
s4 = Spirit(name='端茶送水')

spirits = [s1, s2, s3, s4]
sites = [Site() for each in range(13)]

session.add_all(spirits + sites)

for spirit in spirits:
    for site in sites:
        spirit.add_rel_with_site(site, score=random() * 100)

session.commit()


def monitor():
    print(Spirit.query.filter(Spirit.dbg_is_status_activated == 1).all())
    print(Site.query.filter(Spirit.dbg_is_status_activated == 1).all())

monitor()

# =>
# [Spirit(id = 1, name = '威严满满'),
#  Spirit(id = 2, name = '稳重成熟'),
#  Spirit(id = 3, name = '称职门卫'),
#  Spirit(id = 4, name = '端茶送水')]
# [Site(id = 1),
#  Site(id = 2),
#  Site(id = 3),
#  Site(id = 4),
#  Site(id = 5),
#  Site(id = 6),
#  Site(id = 7),
#  Site(id = 8),
#  Site(id = 9),
#  Site(id = 10),
#  Site(id = 11),
#  Site(id = 12),
#  Site(id = 13)]

```

现在我们开始伪删除:
```
for spirit in spirits:
    spirit.deactivate()
    session.commit()
    monitor()

# =>
# [Spirit(id = 1, name = '威严满满'), Spirit(id = 2, name = '稳重成熟'), Spirit(id = 3, name = '称职门卫'), Spirit(id = 4, name = '端茶送水')]
# [Site(id = 1), Site(id = 2), Site(id = 3), Site(id = 4), Site(id = 5), Site(id = 6), Site(id = 7), Site(id = 8), Site(id = 9), Site(id = 10), Site(id = 11), Site(id = 12), Site(id = 13)]
# [Spirit(id = 2, name = '稳重成熟'), Spirit(id = 3, name = '称职门卫'), Spirit(id = 4, name = '端茶送水')]
# [Site(id = 1), Site(id = 2), Site(id = 3), Site(id = 4), Site(id = 5), Site(id = 6), Site(id = 7), Site(id = 8), Site(id = 9), Site(id = 10), Site(id = 11), Site(id = 12), Site(id = 13)]
# [Spirit(id = 3, name = '称职门卫'), Spirit(id = 4, name = '端茶送水')]
# [Site(id = 1), Site(id = 2), Site(id = 3), Site(id = 4), Site(id = 5), Site(id = 6), Site(id = 7), Site(id = 8), Site(id = 9), Site(id = 10), Site(id = 11), Site(id = 12), Site(id = 13)]
# [Spirit(id = 4, name = '端茶送水')]
# [Site(id = 1), Site(id = 2), Site(id = 3), Site(id = 4), Site(id = 5), Site(id = 6), Site(id = 7), Site(id = 8), Site(id = 9), Site(id = 10), Site(id = 11), Site(id = 12), Site(id = 13)]
# []
# []
```

可以看到删除最后一个睿智少女时才触发了关系删除.
同理, 如果我们依此删除Site, 也会出现最后一个Site被删除时才失去所有少女的情况.

- dbg保留字

```
repr
with
db
python
session
engine
dbg_is_status_activated
deactivate
enum
```

- 最后

dbg-script生成的代码质量还是很不错的, 并且通常对python代码有着一比十几的扩张率.

auto-orm主要展示的是敏捷便利和类型安全, 在功能上还有欠缺.但虽说如此, 在绝大部分情况下(博客系统,
无访问量骤升的中小型网站等)都是非常够用的, 就开发体验上静态检查一条龙的优势, 使用auto-orm是
一件明智的事情.

当然你可以先学会这里面所有的与静态检查相处的技巧, 然后自己造轮子.

