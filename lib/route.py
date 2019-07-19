import numpy as np
import networkx as nx
import pickle
import operator
import time

def _time_cali(t, np):
    return t*(1-0.135-np*0.0045)

def simple_name_norm(name):
    normed = ''.join([x for x in name if x>u'\u4e00' and x<u'\u9fff'])
    if len(normed)==0: return name
    return normed

def get_coord_with_gd(location, key):
    urlhead = "https://restapi.amap.com/v3/geocode/geo?address="
    url=urlhead+location+"&output=JSON&key="+key
    response = requests.get(url)
    resp = response.json()
    location = resp["geocodes"][0]["location"]
    return tuple([float(x) for x in location.split(',')])

def addr_norm(addr, suffix):
    temp_name = addr
    flag = True
    while(flag):
        flag = False
        for item in suffix:
            if temp_name[-len(item):] == item:
                temp_name = temp_name[:-len(item)]
                flag = True
    if len(temp_name)>0:
        return temp_name
    return addr

def _addr_easy_norm(addr, suffix):
    location_norm = addr
    for item in suffix:
        location_norm = location_norm.replace(item, '')
    return location_norm

def GetDistance(coord1, coord2):
    """
    coord = (longitude, latitude)
    return in km
    """
    radLat1 = np.radians(coord1[1])
    radLat2 = np.radians(coord2[1])
    a = radLat1 - radLat2
    b = np.radians(coord1[0]) - np.radians(coord2[0])

    s = 2 * np.arcsin(np.sqrt(np.sin(a/2)**2 + np.cos(radLat1)*np.cos(radLat2)*np.sin(b/2)**2))
    s *= 6371.393;
    return s;

def search_location(location, addrs, suffix):
    if "东乡族自治县" in location:
        return "甘肃省,东乡族自治县"
    if "内蒙" == location[:2] and "内蒙古" != location[:3]:
        loc = "内蒙古"+location[2:]
    else:
        loc = location
    loc = loc.replace(',','')
    loc = loc.replace('/','')
    loc = loc.replace(' ','')

    location_norm = _addr_easy_norm(loc, suffix)
    currentkey = ""
    for key in addrs:
        if "东乡族自治县" in key:
            continue
        key_norm = _addr_easy_norm(key.replace(',',''), suffix)
        if key_norm == location_norm[:len(key_norm)] and len(key)>len(currentkey):
            currentkey = key
    if len(currentkey)<=0:
        raise ValueError('Cannot parse the address.')
    return currentkey

def cal_distance(orig, dest, key):
    url1 = "https://restapi.amap.com/v3/direction/driving?origin="
    url2 = "&destination="
    url3 = "&output=json&key="
    url = url1+str(orig[0])+","+str(orig[1])+url2+str(dest[0])+","+str(dest[1])+url3+key
    # print(url)
    response = requests.get(url)
    resp = response.json()
    try:
        distance = int(resp["route"]["paths"][0]["distance"])/1000
        time = int(resp["route"]["paths"][0]["duration"])/3600
    except KeyError:
        return -1,-1
    return distance, time

def edge_analyzer(nodeIds,nodes,T,minimum,maximum,verbose):
    edges = set()
    for i in range(len(nodes)-1):
        if verbose>0 and (i+1)%verbose == 0: print(str(i+1)+"/"+str(len(nodes)-1))
        dists = {}
        for j in range(len(nodes)):
            dist = GetDistance(nodeIds[nodes[i]], nodeIds[nodes[j]])
            dists[j] = dist
        sorted_dists = sorted(dists.items(), key=operator.itemgetter(1))[1:]

        for j in range(minimum):
            id1 = nodes[i]
            id2 = nodes[sorted_dists[j][0]]
            if id1<id2:
                e = (id1,id2)
            else:
                e = (id2,id1)
            edges.add(e)
        for j in range(minimum,maximum):
            if sorted_dists[j][1]>T: break
            id1 = nodes[i]
            id2 = nodes[sorted_dists[j][0]]
            if id1<id2:
                e = (id1,id2)
            else:
                e = (id2,id1)
            edges.add(e)

    if verbose>0 and (len(nodes)-1)%verbose != 0:
        print(str(len(nodes)-1)+"/"+str(len(nodes)-1))
    return edges

class route_analyzer:

    def __init__(self, r):
        if '/' == r[-1]:
            root = r
        else:
            root = r+'/'

        with open(root+'gaode_keys.pickle', 'rb') as handle:
            self.gaode_keys = pickle.load(handle)
        with open(root+'suffix.pickle', 'rb') as handle:
            self.suffix = pickle.load(handle)
        with open(root+'addr_id_dict.pickle', 'rb') as handle:
            self.addr_id_dict = pickle.load(handle)
        with open(root+'id_addr_dict.pickle', 'rb') as handle:
            self.id_addr_dict = pickle.load(handle)
        with open(root+'id_coord_dict.pickle', 'rb') as handle:
            self.id_coord_dict = pickle.load(handle)
        with open(root+'semi_city_ids.pickle', 'rb') as handle:
            self.semi_city_ids = pickle.load(handle)
        with open(root+'major_cities_ids.pickle', 'rb') as handle:
            self.major_cities_ids = pickle.load(handle)
        with open(root+'other_cities_ids.pickle', 'rb') as handle:
            self.other_cities_ids = pickle.load(handle)
        with open(root+'not_node_ids.pickle', 'rb') as handle:
            self.not_node_ids = pickle.load(handle)
        self.valid_ids = set(self.semi_city_ids+self.major_cities_ids+self.other_cities_ids)
        with open(root+'edge_dt_dict.pickle', 'rb') as handle:
            self.edge_dt_dict = pickle.load(handle)

        self.addr_id_dict_extended = {}
        for name in list(self.addr_id_dict.keys()):
            self.addr_id_dict_extended[name] = self.addr_id_dict[name]
            if name.split(',')[-1] not in self.addr_id_dict:
                self.addr_id_dict_extended[name.split(',')[-1]] = self.addr_id_dict[name]

        self.g_distance = nx.DiGraph()
        self.g_time = nx.DiGraph()
        for e in self.edge_dt_dict.keys():
            dist = self.edge_dt_dict[e][0]
            self.g_distance.add_edge(e[0], e[1], distance=dist)
        for e in self.edge_dt_dict.keys():
            dist = self.edge_dt_dict[e][1]
            self.g_time.add_edge(e[0], e[1], distance=dist)

    def _zoom(self, lllon, lllat, urlon, urlat):
        lon_addon = (urlon-lllon)*0.1
        lat_addon = (urlat-lllat)*0.1
        lllon -= lon_addon
        lllat -= lat_addon
        urlon += lon_addon
        urlat += lat_addon
        if (urlat-lllat)<0.7*(urlon-lllon):
            center = (urlat+lllat)/2
            urlat = center+0.3*(urlon-lllon)
            lllat = center-0.3*(urlon-lllon)
            return lllon, lllat, urlon, urlat
        if (urlon-lllon)<0.7*(urlat-lllat):
            center = (urlon+lllon)/2
            urlon = center+0.3*(urlat-lllat)
            lllon = center-0.3*(urlat-lllat)
            return lllon, lllat, urlon, urlat
        return lllon, lllat, urlon, urlat

    def find_path(self, node1, node2, mode = "shortest", vehicle_type = "car"):
        assert vehicle_type in ["car", "bus", "truck"]
        if type(node1) is int:
            id1 = node1
        elif type(node1) is tuple:
            id1 = -1
            min_dist = float('inf')
            for _id in self.id_coord_dict.keys():
                if _id in self.not_node_ids: continue
                temp_dist = GetDistance(node1, self.id_coord_dict[_id])
                if temp_dist<min_dist:
                    id1 = _id
                    min_dist = temp_dist
        else:
            addr1 = search_location(node1, self.addr_id_dict_extended, self.suffix)
            id1 = self.addr_id_dict[addr1]

        if type(node2) is int:
            id2 = node2
        elif type(node2) is tuple:
            id2 = -1
            min_dist = float('inf')
            for _id in self.id_coord_dict.keys():
                if _id in self.not_node_ids: continue
                temp_dist = GetDistance(node2, self.id_coord_dict[_id])
                if temp_dist<min_dist:
                    id2 = _id
                    min_dist = temp_dist
        else:
            addr2 = search_location(node2, self.addr_id_dict_extended, self.suffix)
            id2 = self.addr_id_dict[addr2]

        if id1 not in self.valid_ids:
            raise ValueError(str(node1)+' is not a valid address/address_id.')
        if id2 not in self.valid_ids:
            raise ValueError(str(node2)+' is not a valid address/address_id.')

        if mode == "shortest":
            p = nx.dijkstra_path(self.g_distance, id1, id2, 'distance')
        elif mode == "quickest":
            p = nx.dijkstra_path(self.g_time, id1, id2, 'distance')
        else:
            raise ValueError("Invalid mode. Please use 'shortest' or 'quickest' instead.")

        pedges = set()
        dist_sum = 0
        time_sum = 0
        for i in range(len(p)-1):
            e = (p[i],p[i+1])
            pedges.add(e)
            dist_sum+=self.edge_dt_dict[e][0]
            time_sum+=self.edge_dt_dict[e][1]
        time_sum = _time_cali(time_sum, len(p))

        if vehicle_type != "car:":
            return (np.round(dist_sum, 2),1.08*np.round(time_sum, 2))
        else:
            return (np.round(dist_sum, 2),np.round(time_sum, 2))

if __name__ == '__main__':
    ra = route_analyzer("../data/")
    route, distance, time_cost = ra.find_path("深圳", (120,30), mode = "quickest", draw_route = False, in_notebook = False)
    print([ra.id_addr_dict[x] for x in route], distance, 'km, ', time_cost, 'hr')
    route, distance, time_cost = ra.find_path("内蒙包头", "营口", mode = "quickest", draw_route = False, in_notebook = False)
    print([ra.id_addr_dict[x] for x in route], distance, 'km, ', time_cost, 'hr')
    route, distance, time_cost = ra.find_path("内蒙包头", "营口", mode = "shortest", draw_route = False, in_notebook = False)
    print([ra.id_addr_dict[x] for x in route], distance, 'km, ', time_cost, 'hr')
    route, distance, time_cost = ra.find_path("乌鲁木齐", 433, mode = "quickest", draw_route = True, in_notebook = False)
    print([ra.id_addr_dict[x] for x in route], distance, 'km, ', time_cost, 'hr')
