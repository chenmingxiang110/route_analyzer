大陆地区城市间路程耗时计算器
=====
运行环境
* numpy 1.12+
* networkx 2.3+
-----
Example Code

    from lib.route import route_analyzer

    print("All packages loaded.")

    ra = route_analyzer("data/")
    addr1 = '杭州'
    addr2 = '乌鲁木齐'
    d, t = ra.find_path(addr1, addr2, mode = "quickest")
    print(d,"km")
    print(t,"hrs")
    
![alt text](https://github.com/chenmingxiang110/route_analyzer/blob/master/pics/pic_level_1.png)
