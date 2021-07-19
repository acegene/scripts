import os
import string
import re
import json
import stat
import sys

if 'GWSST' in os.environ:
    json_globals_file = os.path.join(os.environ['GWSST'], 'globals.json')
else:
    print('WARNING: could not find GWSST environment var')
    json_globals_file = None

protected = True
def import_vid_exts(f=json_globals_file):
    """Returns extensions from global file f"""
    with open(f, 'r') as json_file:
        data = json.load(json_file)
        return data['globals']['video_exts']
exts = '|'.join(['.' + val for val in import_vid_exts()])
path = 'E:'
# path = os.path.normpath(path)
regex = '.*(\.git|System Volume Information|RECYCLE\.BIN|tumblr|!!pics|!!currtrrs).*'
regex_vids = '^.*(' + exts + ')$'
# print(regex_vids)
def choice_rm_files_root(files, files_protected, root):
    print('PROMPT: enter yes/no/quit on whether to delete the above files')
    while True:
        choice = input().lower()
        if choice == 'yes' or choice == 'y':
            for f in files:
                os.chmod(f, stat.S_IWRITE)
                os.remove(f)
            try:
                os.rmdir(root)
            except:
                pass
            break
        if choice == "force":
            for f in files + files_protect:
                os.chmod(f, stat.S_IWRITE)
                os.remove(f)
            try:
                os.rmdir(root)
            except:
                pass
            break
        elif choice == 'no' or choice == 'n':
            break
        elif choice == 'open' or choice == 'o':
            os.startfile(root)
        elif choice == 'quit' or choice == 'q':
            break
        else:
            print("ERROR: respond with yes/no/quit")
for root, dirs, files in os.walk(path, topdown=False):
    if re.search(regex, root):
        continue
    # if len(dirs) != 0:
    #     # print('WARNING: dir=' + str(root) + ' contains directories: ' + str(dirs))
    #     continue
    if len(files) == 0 and len(dirs) == 0:
        print('DELETE: ' + str(root))
        choice_rm_files_root(files, [], dirs)
        continue
    if len(files) == 0:
        continue
    files = [os.path.join(root, f) for f in files]
    total_size = 0
    for f in files:
        total_size += (os.stat(f).st_size / 1024 / 1024)
    if len([True for f in files if re.search(regex_vids, f, re.IGNORECASE)]) == 0 or True:
        files = sorted(files, key=lambda f: os.stat(f).st_size )
        rm_max_sz_width = '{0:>' + str(len(str(max([int(round(os.stat(f).st_size / 1024 / 1024)) for f in files])))) + '}' # formatting
        if len(files) > 2000:
            # print(str(root) + ': too many files')
            pass
        else:
            files_protected = [f for f in files if re.search(regex_vids, f, re.IGNORECASE)]
            files = [f for f in files if f not in files_protected]
            if protected == True and len(files) == 0:
                continue
            for d in dirs:
                print('    ' + str(d))
            print('    ------dirs above------')
            for f in files_protected:
                print('    ' + rm_max_sz_width.format(str(int(round(os.stat(f).st_size / 1024 / 1024)))) + ' - ' + os.path.basename(f))
                continue
            print('    ----protected above----')
            for f in files:
                print('    ' + rm_max_sz_width.format(str(int(round(os.stat(f).st_size / 1024 / 1024)))) + ' - ' + os.path.basename(f))
                continue
            print(root)
            choice_rm_files_root(files, files_protected, root)
