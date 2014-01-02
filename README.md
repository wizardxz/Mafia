#Mafia

在线杀人游戏服务器

##安装


###Windows:

  * 下载并安装python

    Mafia是用python语言开发的，因此需要下载并安装python编译器
  
    <http://www.python.org/ftp/python/2.7.6/python-2.7.6.msi>

  * 下载并安装web.py
  
    Mafia的web框架采用的是web.py，有两种安装方法。

    * 通过[easy_install](https://pypi.python.org/pypi/setuptools#windows)的方法安装web.py
      
      `c:\Python27\Scripts\easy_install web.py`

    * 通过下载压缩包的方法安装web.py

      压缩包的链接是 http://webpy.org/static/web.py-0.37.tar.gz
      
      使用解压软件将压缩包解压到某临时文件夹，如c:\temp\webpy\。
      
      通过命令行`cmd`进入该文件夹`cd c:\temp\webpy\`
      
      在命令行下运行`python setup.py install`完成安装。
  
  * 下载Mafia
    
    Mafia有两种下载方法。

    * 通过[git](http://git-scm.com/download/win)下载
      
      通过命令行`cmd`运行`git clone https://github.com/wizardxz/Mafia.git`
    
    * 通过下载压缩包的方法安装Mafia
      
      压缩包的链接是 <https://github.com/wizardxz/Mafia/archive/master.zip>
      
      下载完毕后，解压至某文件夹，如c:\Mafia\


### Ubuntu

  `sudo apt-get install python python-setuptools git`
  
  `sudo easy_install web.py`
  
  `git clone https://github.com/wizardxz/Mafia.git`
  
## 运行
  
  在命令行中运行`python mafiaweb.py xxx.xxx.xxx.xxx:xxxx`
  
  *注意xxx.xxx.xxx.xxx:xxxx为你的IP地址和端口号，你需要替换成类似192.168.1.100:8080的形式*
  
  *如何获取我的IP地址？*[Windows](http://zh.wikipedia.org/wiki/Ipconfig) [Ubuntu](http://zh.wikipedia.org/wiki/Ifconfig)
  
  接着，让你和你的朋友打开浏览器进入http://xxx.xxx.xxx.xxx:xxxx
  
  Have fun.




