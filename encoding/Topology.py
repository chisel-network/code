from geopy import distance

'''
Overall the optimization needs variables to represent:
(1) Which path is selected to carve a slice (slice var)
(2) How wide is a slice (slice var)
(3) Spectrum used for a slice on a switch (span var) 
(4) Lowest pixel used for a slice on a switch (span var)
'''
class OpticalSwitch:
    def __init__(self, name):
        self.name = name
        
class FiberSpan:
    def __init__(self, srcsite, destsite, init_spectrum, M):
        self.e = (srcsite, destsite)
        self.name = "%s:%s" % (srcsite, destsite)
        self.srcsite = srcsite
        self.destsite = destsite
        self.init_spectrum = init_spectrum
        self.M = M
        # keep track of all fiber paths this span is on
        self.paths = []
        
    def add_fiberpath(self, p):
        assert self.e in [edge.e for edge in p.path]
        if all(p.pathstr != x.pathstr for x in self.paths):
            self.paths.append(p)

class FiberPath:

    site_to_coords = None
    coords_to_distances = {}

    @staticmethod
    def populate_site_to_coords():
        if FiberPath.site_to_coords != None:
            return
        
        FiberPath.site_to_coords = {}
        
        # Commenting to preserve anonymity of site locations

        # with open('locations.csv', 'r') as csv_file:
        #     for line in csv_file:
        #         # SiteCode,Source,Latitude,Longitude
        #         if line.startswith('SiteCode'):
        #             continue
        #         line = line.strip()
        #         parts = line.split(',')
        #         site = parts[0].lower()
        #         site = site[:3]
        #         lat = float(parts[2])
        #         lon = float(parts[3])
        #         FiberPath.site_to_coords[site] = (lat, lon)

    @staticmethod
    def get_coords(site):
        site = site[:3]
        FiberPath.populate_site_to_coords()
        if site in FiberPath.site_to_coords:
            return FiberPath.site_to_coords[site]
        return None, None

    @staticmethod
    def get_distance(src_coords, dst_coords):
        if (src_coords, dst_coords) in FiberPath.coords_to_distances:
            return FiberPath.coords_to_distances[(src_coords, dst_coords)]
        
        path_distance = distance.distance(src_coords, dst_coords).km
        return path_distance

    @staticmethod
    def get_modulation(fiberspans):
        total_distance = 0
        modulation = 0

        for span in fiberspans:
            src = span.srcsite
            dst = span.destsite

            src_coords = FiberPath.get_coords(src)
            dst_coords = FiberPath.get_coords(dst)

            if src_coords == (None, None) or dst_coords == (None, None):
                total_distance += 2500 # if there is no data, assume the longest distance => lowest bw
            else:
                path_distance = FiberPath.get_distance(src_coords, dst_coords)
                total_distance += path_distance
                FiberPath.coords_to_distances[(src_coords, dst_coords)] = path_distance

        if total_distance <= 800:
            modulation = 200
        if total_distance > 800 and total_distance <= 2500:
            modulation = 150
        if total_distance > 2500:
            modulation = 100
        
        
        return modulation

    def __init__(self, path, pathstr, modulation=100):
        # path here is a list of edge objects
        self.path = path
        self.pathstr = pathstr
        self.modulation = self.get_modulation(path)
        for e in path:
            e.add_fiberpath(self)
            
    def name(self):
        return self.pathstr
                 
class Slice:
    def __init__(self, source, destination, bandwidth):
        self.source = source
        self.destination = destination
        self.bandwidth = bandwidth
        self.paths = []
        self.w_var = None
        self.path_vars = []
        self.t_var = None
        self.spectrum_var = None
        
    def init_width_var(self, model):
        var = model.Variable(type="Int", name=f"w_{self.source}_{self.destination}")
        self.w_var = var     

    def init_toggle_var(self, model, M):
        var = model.Variables(1, M, type="Bool", name=f"t_{self.source}_{self.destination}")   
        self.t_var = var
    
    def init_spectrum_var(self, model, M):
        var = model.Variables(1, M, type="Bool", name=f"x_{self.source}_{self.destination}")
        self.spectrum_var = var
    
    def init_path_selection_var(self, model):
        for i in range(len(self.paths)):
            var = model.Variable(type="Bool", name=f"y_{self.source}_{self.destination}_{i}")
            self.path_vars.append(var)

    def add_fiberpath(self, pathobj):
        assert pathobj.pathstr.split(':')[0] == self.source
        assert pathobj.pathstr.split(':')[-1] == self.destination
        if pathobj.pathstr not in [x.pathstr for x in self.paths]:
            self.paths.append(pathobj)
                                                
        
class OpticalNetwork:
    def __init__(self, name):
        self.name = name
        self.opswitches = {}
        self.fiberspans = {}
        self.slices = {}
        self.paths = {}
        self.graph = {}

    def add_opswitch(self, site):
        if site in self.opswitches:
            sw = self.opswitches[site]
        else:
            sw = OpticalSwitch(site)
            self.opswitches[site] = sw

        return sw

    def add_fiberspan(self, srcsite, destsite, initspectrum, M):
        assert isinstance(srcsite, str)
        assert isinstance(destsite, str)
        
        srcsite_obj = self.add_opswitch(srcsite)
        destsite_obj = self.add_opswitch(destsite)
        
        if (srcsite, destsite) in self.fiberspans:
            edge = self.fiberspans[(srcsite, destsite)]
        else:
            edge = FiberSpan(srcsite, destsite, initspectrum, M)
            self.fiberspans[(srcsite, destsite)] = edge
            
        return edge

    def add_slice(self, srcsite, destsite, bw):
        assert isinstance(srcsite, str)
        assert isinstance(destsite, str)
        self.add_opswitch(srcsite)
        self.add_opswitch(destsite)
        
        if (srcsite, destsite) not in self.slices:
            self.slices[(srcsite, destsite)] = Slice(srcsite, destsite, bw)
            
        return self.slices[(srcsite, destsite)]
                                                                    

    def add_fiberpath(self, path):
        assert isinstance(path, list)
        assert isinstance(path[0], str)
        path_str = ":".join(path)
        if path_str in self.paths: return
        
        path_start = path[0]
        path_end = path[-1]
        path_edge_list = []
        for src, dst in zip(path, path[1:]):
            nodeA = self.add_opswitch(src)
            nodeB = self.add_opswitch(dst)
            assert (src, dst) in self.fiberspans
            span = self.fiberspans[(src, dst)]
            path_edge_list.append(span)
            
        path_obj = FiberPath(path_edge_list, path_str)
        self.paths[path_str] = path_obj
        if (path_start, path_end) in self.slices:
            slice = self.slices[(path_start, path_end)]
            slice.add_fiberpath(path_obj)
            
    

        
    
