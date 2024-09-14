import configparser
import os
import sys

def modify_tox_ini(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    
    # Ensure the necessary sections exist
    if 'tox' not in config.sections():
        config.add_section('tox')
    if 'testenv:gather_tests' not in config.sections():
        config.add_section('testenv:gather_tests')

    # Modify the envlist in [tox] section
    envlist = config['tox'].get('envlist', '')
    envlist_items = [item.strip() for item in envlist.split('\n') if item.strip()]
    if 'gather_tests' not in envlist_items:
        envlist_items.append('gather_tests')
    config['tox']['envlist'] = '\n'.join(envlist_items)
    
    ## Add or update the [testenv:gather_tests] section
    ## Will add condition if requirement-test.txt only exists
    #if os.path.isfile("requirements-test.txt"):
    #    config['testenv:gather_tests'] = {
    #        'deps': '\n    -r requirements-test.txt\n    -r requirements-dev.txt',
    #        'commands': 'python list_pytest_tests.py'
    #    }
    ## Write the changes back to the tox.ini file
    with open(file_path, 'w') as configfile:
        config.write(configfile)
    
    print(f"Updated {file_path} successfully.")

if __name__ == "__main__":
    proj_name = sys.argv[1]
    # Path to the tox.ini file
    tox_ini_path = proj_name+"/tox.ini"
    
    # Check if the tox.ini file exists
    if os.path.exists(tox_ini_path):
        modify_tox_ini(tox_ini_path)
    else:
        print(f"{tox_ini_path} does not exist.")

