# Functions for IO to Tsunami GUI
# Simon Libby and Marcus Wild 2020


def load_config_file(path):     
    parameters = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                if line[0] != '!':
                    try:
                        k, vs = line.split(' = ')
                    except:
                        print('Odd line: ' + line)
                        continue
                    try:                            
                        # Might be a better way to check for different float types
                        if any(c in vs for c in ['.', 'e', 'E']):
                            v = float(vs) 
                        else:
                            v = int(vs)
                    except ValueError:
                        if vs == 'T':
                            v = True
                        elif vs == 'F':
                            v = False
                        else:
                            v = vs
                    parameters[k] = v
                    
    return parameters


                
                
    