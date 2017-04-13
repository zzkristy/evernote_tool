# evernote
同步文件夹下的md文件到evernote的笔记本

## 配置
配置文件放在用户主目录下的.evernote

    {
        "token": 开发者token,
        "path": 文件的根路径
    }

## 命令

```python evernote_sync.py -b dir_name```

dir_name 需要同步的文件夹(evernote中需要有同名笔记本)

## 特性
可以根据修改时间增量不同。在同步的文件夹下生成.evernote文件，里面保存上次同步时文件的修改时间，再次同步时比较文件的修改时间，只同步修改时间变化的文件。

