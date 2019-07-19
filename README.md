大陆地区城市间路程耗时计算器
=====
本程序可查询县级市及以上行政单位之间的距离和行车时间。
运行环境
* numpy 1.12+
* networkx 2.3+
-----
Example Code

    from lib.route import route_analyzer

    # initialize the dicts
    ra = route_analyzer("data/")
    # 地址应当按照行政区划的顺序从上向下写，可以直接写县市的名字，比如"玉环"，"玉环县"，"浙江玉环县"，"台州市玉环"等等。但不应写作"台州浙江玉环"。
    addr1 = '杭州'
    addr2 = '乌鲁木齐'
    # mode = "quickest" or "shortest"
    # vehicle_type = "car" or "bus" or "truck"
    d, t = ra.find_path(addr1, addr2, mode = "quickest", vehicle_type = "car")
    print(d,"km")
    print(t,"hrs")
    
通过维护一张图网络从而在不爬取 n\*n 网络的前提下实现查询各个节点最短距离/时间的查询。

该网络由四层构成：

第一层：省会城市和计划单列市之间的网络，该层共319条边
![alt text](https://github.com/chenmingxiang110/route_analyzer/blob/master/pics/pic_level_1.png)
第二层：地级市和省直辖县级市之间的网络，该层共3283条边（与第一层网络有重复）
![alt text](https://github.com/chenmingxiang110/route_analyzer/blob/master/pics/pic_level_2.png)
第三层：其他县级市之间的网络，该层共15389条边（与前两层有重复）
![alt text](https://github.com/chenmingxiang110/route_analyzer/blob/master/pics/pic_level_3.png)
第四层：省内城市之间的网络（与前三层有重复，这里以浙江省省内网络距离）
![alt text](https://github.com/chenmingxiang110/route_analyzer/blob/master/pics/pic_level_4.png)
剔除重复的边，整个网络共36326条边。由于使用的是有向图，故数据库内总共约有2300个节点和72652条边。使用dijstra算法寻找最短/最快路径。
