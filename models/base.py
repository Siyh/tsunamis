#Class objects for nhwave and funwave
#Simon Libby 2017

import os, sys
import numpy as np
import matplotlib.pyplot as plt
from glob import glob
from shutil import copy2
from subprocess import Popen, PIPE
from stat import S_IEXEC
from matplotlib.widgets import Slider, Button, RadioButtons
from pandas import read_table
from threading import Thread 

from tsunamis.utilities.io import read_configuration_file, read_grid


def sequence(start, step, number):
    """
    Gives a range with both end points based on the start, step and number
    """
    return np.linspace(start, step * number + start, number)


class model:
    """
    NOTE beacuse of how nhwave and funwave handle depth grids, grids should be 
    orientated so that north is 'up'; ie. index [0:0] is north west corner.
    """

    def __init__(self,
                 parameters={},
                 input_directory='',
                 output_directory='',
                 results_folder='results',
                 executable_path='', 
                 input_file='input.txt',
                 depth_file='depth.txt',
                 probe_file='stat.txt',
                 obstacle_file='obstacles.txt',  
                 fresh=False,
                 **kwargs):
        
        """
        
        """                 
        
        print(f'Preparing {self.model}...')
        
        # Copy any provided parameters so the original source can't get modified
        self.parameters = {**parameters}
        self.parameters['RESULT_FOLDER'] = results_folder
        self.input_directory = input_directory
        
        if output_directory:
            self.output_directory = output_directory
        else:
            self.output_directory = os.path.dirname(os.path.abspath(sys.argv[0]))

        if executable_path:
            self.source_executable_path = os.path.abspath(executable_path)
        else:
            self.source_executable_path = self.default_executable_path
        
        self.input_file = input_file
        self.parameters['DEPTH_FILE'] = depth_file
        
        self.linux_link = WSLlink()
        
        self.load_inputs()
        self.load_depth()
        
    
    @property
    def results_path(self):
        return os.path.join(self.output_directory, self.results_folder)
    
    @property
    def results_folder(self):
        return self.parameters['RESULT_FOLDER']
    
    @property
    def depth_path(self):
        return os.path.join(self.output_directory, self.depth_file)
    
    @property
    def depth_file(self):
        return self.parameters['DEPTH_FILE']
        
        
    def load_inputs(self, path=''):
        if not path: path = os.path.join(self.input_directory, self.input_file)
        if not os.path.exists(path): return
        
        self.parameters = read_configuration_file(path)
                        
                        
                        
    def load_depth(self, path=''):
        if not path: path = os.path.join(self.input_directory, self.depth_file)
        if not os.path.exists(path): return
        
        self.depth = read_grid(path)
        
        
                        
    def write_config(self, output_directory=''):
        if not output_directory: output_directory = self.output_directory
        
        print('Writing {} inputs to {}'.format(self.model, output_directory))
        
        self.write_inputs()
        self.write_depth()      
         
        # Copy the executable
        self.target_executable_path = os.path.join(output_directory,
                                                   os.path.basename(self.source_executable_path))
        if not os.path.isfile(self.target_executable_path):
            copy2(self.source_executable_path, self.target_executable_path)        
        
        if sys.platform == 'linux':
            # Give the program the relevant permissions
            st = os.stat(self.program_path)
            os.chmod(self.program_path, st.st_mode | S_IEXEC)
            
        # Check the results folder exists and create it if not
        results_folder_path = os.path.join(output_directory,
                                           self.parameters['RESULT_FOLDER'])
        if not os.path.exists(results_folder_path):
            os.mkdir(results_folder_path)
            
        
        
    def write_inputs(self, path=''):
        if not path: path = os.path.join(self.output_directory, self.input_file)
        with open(path, 'w') as f:
            for k, v in self.parameters.items():
                if isinstance(v, bool):
                    v = 'T' if v else 'F'
                f.write(f'{k} = {v}\n') 
                
      
    def write_depth(self, path=''):
        if not path: path = os.path.join(self.output_directory, self.depth_file)
        if self.depth.mean() < 0:
            print('WARNING, inputs must be depth not elevation')
        np.savetxt(path, self.depth, fmt='%5.1f')
        
        
    def run(self,
            console_text_target=None):
        """
        Run the simulation with the given inputs.
        """
        
        # Make the results folder if it doesn't already exist        
        if not os.path.isdir(self.results_path): os.mkdir(self.results_path)
        
        n = int(self.parameters['PX']) * int(self.parameters['PY'])
        
        command = f'mpirun -np {n} "{self.target_executable_path}"'
        
        # If this is running on Windows change the command appropriately
        if os.name == 'nt':
            command = 'wsl.exe ' + path_to_wsl(command)
            input_path = self.output_directory.replace('\\', '/')
        else:
            input_path = self.output_directory            
         
        print(self.model + ' initiated with command:')
        print(command + '\nin:\n' + input_path)        
        
        p = Popen(command, shell=False, cwd=input_path, stdout=PIPE)
        
        if console_text_target is None:
            print(self.model + ' output:')
            # Write the output to Python stdout
            for c in iter(lambda: p.stdout.read(1), b''):
                sys.stdout.write(c)
            return True
        else:
            t = Thread(target=self.linux_link.run,
                       args=(p, console_text_target))
            t.start()
        


                
    def xyz_to_grid(self, xyz_path, elevation=True):
        """Convert an xyz grid to the model format"""
        print('Loading xyz data')
        xs, ys, zs = np.loadtxt(xyz_path, unpack=True)
        
        xs = np.unique(xs)
        ys = np.unique(ys)
        minx = np.min(xs)
        maxx = np.max(xs)
        miny = np.min(ys)
        maxy = np.max(ys)
        xn = xs.size
        yn = ys.size
        dx = (maxx - minx) / xn
        dy = (maxy - miny) / yn        
        
        self.parameters['Mglob'] = xn
        self.parameters['Nglob'] = yn
        self.parameters['DX'] = dx
        self.parameters['DY'] = dy
        
        print('Converting xyz data to grid')        
        self.depth = zs.reshape((yn, xn))
        
        self.check_save_depth(elevation)       
        
        
        
    def evg_to_grid(self, evg_path, elevation=True, to_cell_centre=True):
        """Convert from earthvision grid to model format"""
        print('Loading EarthVision Grid data')
        xs, ys, zs, Xi, Yi = np.loadtxt(evg_path, skiprows=20, unpack=True)        
        
        yn = int(np.max(Yi))
        xn = int(np.max(Xi))
        zz = np.ndarray((yn, xn))
        #Convert columns/rows to indicies
        yis = (Yi - np.min(Yi)).astype(int)
        xis = (Xi - np.min(Xi)).astype(int)
        #Put zs in right place on grid
        zz[yis, xis] = zs
        
        if to_cell_centre:
            print('Approximating to cell centre')
            yn -= 1
            xn -= 1
            #Change grid to cell center
            self.depth = np.ndarray((yn, xn))
            #Iterate over all but the last cell
            for yi, xi in np.ndindex(yn, xn):
                #Calculate mean of each cell
                self.depth[yi, xi] = (zz[yi, xi] + zz[yi, xi + 1] +
                        zz[yi + 1, xi] + zz[yi + 1, xi + 1]) / 4
        
        minx = np.min(xs)
        maxx = np.max(xs)
        miny = np.min(ys)
        maxy = np.max(ys)
        dx = (maxx - minx) / xn
        dy = (maxy - miny) / yn
        
        self.parameters['Mglob'] = xn
        self.parameters['Nglob'] = yn
        self.parameters['DX'] = dx
        self.parameters['DY'] = dy
        
        self.check_save_depth(elevation) 
                    
        


    def results(self):
        """Display the results of the simulation run"""        
        #Load simulation output as a list of arrays
        depth = np.loadtxt(self.depth_path)
        file_list = sorted(glob(self.output_directory + 'eta_*'),
                key=lambda name: int(name[-5:]))
        
        data = [np.zeros_like(depth)]
        for i, path in enumerate(file_list):
            print('\rLoading output', i + 1, 'of', len(file_list), end='')
            data.append(np.loadtxt(path))

        fig, ax = plt.subplots()
        plt.subplots_adjust(left=0.25, bottom=0.25)
        
        p = ax.imshow(depth)
        fig.colorbar(p)
        
        #Display toggle
        rax = plt.axes([0.025, 0.5, 0.15, 0.15])
        labels = ['Depths', 'Change (fixed colourbar)',
                'Change (stretched colourbar)']
        radio = RadioButtons(rax, labels, active=0)
        
        def displayfunc(label):
            update(stime.val)
            fig.canvas.draw_idle()
        radio.on_clicked(displayfunc)        
        
        #Slider axes
        axtime = plt.axes([0.25, 0.1, 0.65, 0.03])
        #Sliders
        stime = Slider(axtime, 'Time', 0, len(data), valinit=0, valfmt='%0.0f')
        
        #Update function
        def update(val):
            #Round slider value to nearest whole number (for index)
            timepoint = int(stime.val + 0.5)
            #If depths are being displayed
            if radio.value_selected == labels[0]:
                datavals = depth + data[timepoint]
                p.set_data(datavals)
                p.set_clim(np.min(datavals), np.max(datavals))
            #If change is being displayed
            else:
                datavals = data[timepoint]
                p.set_data(datavals)
                #If colourbar is fixed
                if radio.value_selected == labels[1]:
                    p.set_clim(np.min(data[-1]), np.max(data[-1]))
                else:
                    p.set_clim(np.min(datavals), np.max(datavals))
                
            fig.canvas.draw()
        stime.on_changed(update)        
        
        #Arrow buttons
        axprev = plt.axes([0.7, 0.05, 0.1, 0.075])
        axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
        
        bnext = Button(axnext, 'Next')
        def nextf(_):
            stime.set_val(stime.val + 1)
            update(stime.val)
        bnext.on_clicked(nextf)
        bprev = Button(axprev, 'Previous')
        def prevf(_):
            stime.set_val(stime.val - 1)
            update(stime.val)
        bprev.on_clicked(prevf)        
        
        #Reset button
        resetax = plt.axes([0.8, 0.025, 0.1, 0.04])
        button = Button(resetax, 'Reset', hovercolor='0.975')
        
        def reset(event):
            stime.reset()    
        button.on_clicked(reset)        
        
        plt.show()
        
        
    def grid_range(self, grid):
        """Give information about a grid of data"""
        print('Grid shape:', grid.shape)
        print('Max:', np.nanmax(grid), 'Min:', np.nanmin(grid), 
                'Mean:', np.nanmean(grid))
        nanc = np.sum(np.isnan(grid))
        if nanc: print('Nan count:', nanc)
        
        
    def gs(self, xn, xd, xe=0):
        return np.linspace(0, int(xn) * float(xd), int(xn)) + float(xe)
    

    
        
    def export(self, file_form, x0, y0, result_to_convert=False,
            save_path=False, to_elevation=True):
        """
        Converts to xyz file for loading into Petrel
        file_form = one of 'eta', 'u', 'v', 'depth' to save
        to_elevation = change depth data to elevation
        """        
        prefix = self.results_dir + file_form
        if file_form != 'depth':            
            if result_to_convert:
                result_to_convert = str(result_to_convert)
                preceeding_zeros = (5 - len(result_to_convert)) * '0'
                result_to_convert = preceeding_zeros + result_to_convert
            else:
                #List of the results
                results = glob(prefix + '*')
                #Check there are some results to convert
                if not results:
                    print('No results to convert')
                    sys.exit()
                #Find the largest file number to convert
                result_to_convert = max(results)[-5:]
            result_to_convert_path = prefix + '_' + result_to_convert
        else:
            result_to_convert_path = self.depth_path
            ###### implement saving landslide
        
        #Convert file to xyz
        data = np.loadtxt(result_to_convert_path)[:int(self.Nglob)]
        xl = self.gs(self.Mglob, self.DX, x0)
        yl = self.gs(self.Nglob, self.DY, y0)
        xd, yd = np.meshgrid(xl, yl)
        
        if file_form == 'depth':
            landslide = self.gen_ls(int(result_to_convert) *
                    float(self.TOTAL_TIME) * float(self.PLOT_INTV) /
                    (float(self.TOTAL_TIME) - float(self.PLOT_START)))
            
            print('Adding a landslide to the depth file')  
            data -= landslide
            if to_elevation: data = -data
        else:
            #mask spikes
            ############################
            data[:, -1] = 0 ###### get rid of the source of spikes
            data[-1] = 0
            ###########################
        
        print('Saving', result_to_convert_path, 'as xyz file')
        points = np.column_stack((xd.flatten(), yd.flatten(), data.flatten()))
        if not save_path: save_path = prefix + '.xyz'
        np.savetxt(save_path, points, fmt='%5.5g')
        
        
def path_to_wsl(path):
    """
    Convert a path from the windows format to the WSL format.
    """
    path = path.replace('\\', '/')
    coloni = path.find(':')
    if coloni > 0:
        letter = path[coloni - 1].lower()
        path = path[:coloni - 1] + '/mnt/' + letter + path[coloni + 1:]                
    return path


class WSLlink:       
    def __init__(self):
        self.running = False
        
    def run(self, process, output):
        self.running = True
        self.output = output
        
        for line in iter(process.stdout.readline, b''):
            
            if not self.running:
                output('WSL link terminated.')
                return
            
            output(line.decode('utf-8'))            
            
            
    def terminate(self):
        if self.running:
            self.output('WSL link termination called...\n')
            self.running = False

        
        
def batch_run(model, folder_name, runs, number_suffix=1):
    """
    model=what to call run on
    folder=what to call the folder of each run (with number appended)
    runs=A list with a dictionary for each run with keword-value pairs
    number_suffix=folder suffix number to start the run of models with.
    """
    fails = []
    for kwargs in runs:
        folder = folder_name + str(number_suffix)
        number_suffix += 1
        title = str(kwargs)[1:-1].replace("'",'').replace(':','=').replace(' ','')
        try:
            model(folder, TITLE=title, **kwargs).run()
        except:
            fails.append(title)
    if not fails:
        print('No failed runs.')
    else:
        for fail in fails: print(fail, 'failed.')
        
        
        
#http://stackoverflow.com/questions/20144529/shifted-colorbar-matplotlib
from matplotlib.colors import Normalize
class MidpointNormalize(Normalize):
    def __init__(self, vmin=None, vmax=None, midpoint=None, clip=False):
        self.midpoint = midpoint
        Normalize.__init__(self, vmin, vmax, clip)

    def __call__(self, value, clip=None):
        x, y = [self.vmin, self.midpoint, self.vmax], [0, 0.5, 1]
        return np.ma.masked_array(np.interp(value, x, y))
    
                
def single_view(results_path, model, folder, folder_path):
    results = glob(os.path.join(results_path, 'eta_*'))
    if not results: return        
    data = np.loadtxt(max(results))
    data[:, -1] = 0 ######
    
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    plt.figure()
    ax = plt.gca()
    im = ax.imshow(data, norm=MidpointNormalize(midpoint=0.), cmap='seismic')
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    plt.colorbar(im, cax=cax)
    
    input_path = os.path.join(os.path.dirname(results_path), 'input.txt')
    with open(input_path, 'r+') as f: content = f.readlines()
    for line in content:
        line = line.strip()
        if not line: continue
        if line[0] == '!': continue
        if line[:5] == 'TITLE':
            description = line.split(' = ')[-1].strip()
            break
    name = model + ' ' + description
    print('Saving', name)
    ax.set_title(name)
    save_folder = folder_path.replace('*', '')
    if not os.path.isdir(save_folder): os.mkdir(save_folder)                
    plt.savefig(os.path.join(save_folder, name + '.png'), bbox_inches='tight')
    plt.close()
    
        
def batch_view(folder_name):
    """
    folder_name= location relative to script where model folders are. * is wildcard
    """
    ###### need to remove topography
    script_loc = os.path.dirname(os.path.abspath(sys.argv[0]))
    folder_path = os.path.join(script_loc, folder_name)
    folders = glob(folder_path)
    for folder in folders:
        for model in ['nhwave', 'funwave']:            
            model_path = os.path.join(folder, model)
            if os.path.isdir(model_path):
                single_view(os.path.join(model_path, 'results'), model,
                        folder, folder_path)
                
                        
def batch_graph(folder_name, model='nhwave'):
    """
    folder_name= location relative to script where model folders are. * is wildcard
    """
    script_loc = os.path.dirname(os.path.abspath(sys.argv[0]))
    folder_path = os.path.join(script_loc, folder_name)
    folders = glob(folder_path)
    for folder in folders:            
        model_path = os.path.join(folder, model)
        if os.path.isdir(model_path):
            results_path = os.path.join(model_path, 'results')
            results = glob(os.path.join(results_path, 'eta_*'))
            if not results: continue
            data = np.loadtxt(max(results))
            data[:, -1] = 0 ######
            
            section = data[:, 250]
            
            input_path = os.path.join(os.path.dirname(results_path), 'input.txt')
            with open(input_path, 'r+') as f: content = f.readlines()
            for line in content:
                line = line.strip()
                if not line: continue
                if line[0] == '!': continue
                if line[:5] == 'TITLE':
                    description = line.split(' = ')[-1].strip()
                    break
            
            plt.plot(section, label=description)
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
            ncol=2, mode="expand", borderaxespad=0.)
    ylims = plt.ylim()
    depth = np.loadtxt(model_path + '\depth.txt')[:, 250]
    plt.plot(-depth, color='k', linestyle='--')
    plt.ylim(ylims)
    save_folder = folder_path.replace('*', '')
    plt.savefig(os.path.join(save_folder, 'graph_comparison.png'), bbox_inches='tight')
    plt.show()


def plot_gauges(folder_name, model='funwave'):
    """
    folder_name= location relative to script where model folders are. * is wildcard
    """
    script_loc = os.path.dirname(os.path.abspath(sys.argv[0]))
    folder_path = os.path.join(script_loc, folder_name)         
    model_path = os.path.join(folder_path, model)
    if os.path.isdir(model_path):
        results_path = os.path.join(model_path, 'results')
        results = glob(os.path.join(results_path, 'sta_*'))
        if not results: return
        
        station_num = len(results)
        tsteps = len(np.loadtxt(results[0]))
        data = np.ndarray((tsteps, station_num))
        for ix, result in enumerate(results):
            #To get rid of output where E in exponent number is missing            
            d = read_table(result, usecols=(1,),
                    delim_whitespace=True, header=None)
            for iy, r in enumerate(d):
                try: r = float(r)
                except: r = 0
                data[iy, ix] = r
            #data[:, i] = np.loadtxt(result, usecols=(0,1))[:, 1]
            
        
    depth = np.loadtxt(model_path + '\depth.txt')
    depth_indices = np.loadtxt(model_path + '\stations.txt', dtype=int)
    depth_section = depth[depth_indices[:,1], depth_indices[:,0]]

    fig, ax = plt.subplots()
    plt.subplots_adjust(left=0.25, bottom=0.25)
    
    ax.plot(-depth_section, color='k')
    p = ax.plot(data[0], color='b')[-1]
    #Slider axes
    axtime = plt.axes([0.25, 0.1, 0.65, 0.03])
    #Sliders
    stime = Slider(axtime, 'Time', 0, len(data), valinit=0, valfmt='%0.0f')
    
    #Update function
    def update(val):
        #Round slider value to nearest whole number (for index)
        timepoint = int(stime.val + 0.5)
        p.set_ydata(data[timepoint])

        fig.canvas.draw()
    stime.on_changed(update)        
    
    #Arrow buttons
    axprev = plt.axes([0.7, 0.05, 0.1, 0.075])
    axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
    
    bnext = Button(axnext, 'Next')
    def nextf(_):
        stime.set_val(stime.val + 1)
        update(stime.val)
    bnext.on_clicked(nextf)
    bprev = Button(axprev, 'Previous')
    def prevf(_):
        stime.set_val(stime.val - 1)
        update(stime.val)
    bprev.on_clicked(prevf)        
    
    #Reset button
    resetax = plt.axes([0.8, 0.025, 0.1, 0.04])
    button = Button(resetax, 'Reset', hovercolor='0.975')
    
    def reset(event):
        stime.reset()    
    button.on_clicked(reset)        
    
    plt.show()