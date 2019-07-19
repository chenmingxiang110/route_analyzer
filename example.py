from lib.route import route_analyzer

print("All packages loaded.")

ra = route_analyzer("data/")
addr1 = '杭州'
addr2 = '乌鲁木齐'
d, t = ra.find_path(addr1, addr2, mode = "quickest")
print(d,"km")
print(t,"hrs")
