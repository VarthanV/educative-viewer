import webbrowser
from flask import Flask, render_template, request, redirect
import jinja2
import os
import natsort
import socket
from collections import defaultdict
import random
import sys
import subprocess


ROOT_DIR = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    global course_directory

    if request.method == "POST" and request.form.get("folder"):
        for value in request.form.values():
            folder = value
        if folder+".html" in os.listdir(os.path.join(course_directory, folder)):
            load_templates()
            return redirect(f"/{folder}")
        elif folder+".html" not in os.listdir(os.path.join(course_directory, folder)):
            course_directory = os.path.join(course_directory, folder)
            folders = natsort.natsorted(load_folder(course_directory))
            return render_template("index.html", folder_list=folders, folder=folder)
    elif request.method == "POST" and len(root_course_path) < len(course_directory):
        course_directory = os.path.sep.join(
            course_directory.split(os.path.sep)[:-1])
        folders = natsort.natsorted(load_folder(course_directory))
        folder = os.path.split(course_directory)[-1]
        return render_template("index.html", folder_list=folders, folder=folder)
    folders = natsort.natsorted(load_folder(course_directory))
    folder = os.path.split(course_directory)[-1]
    return render_template("index.html", folder_list=folders, folder=folder)


def get_ip():
    port = random.randint(1000, 9999)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_address = s.getsockname()[0]
    while s.connect_ex((ip_address, port)) != 0:
        port = random.randint(1000, 9999)
    s.close()
    return ip_address, port


def check_code_present(topic):
    if len(os.listdir(os.path.join(course_directory, topic))) > 1:
        return True
    return False


def load_topics(course_directory):
    folders_paths = []
    for folders in os.listdir(course_directory):
        folder_path = os.path.join(course_directory, folders)
        if os.path.isdir(folder_path) and os.path.isfile(os.path.join(folder_path, folders+".html")):
            folders_paths.append(folders)
    return folders_paths


def load_folder(course_directory):
    folders_paths = []
    for folders in os.listdir(course_directory):
        folder_path = os.path.join(course_directory, folders)
        if os.path.isdir(folder_path):
            folders_paths.append(folders)
    return folders_paths


def load_files(topic_directory):
    file_contents, file_names, h_map = [], [], defaultdict(str)
    for root, _, files in os.walk(os.path.join(course_directory, topic_directory)):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.isfile(file_path) and topic_directory not in file:
                content = "\n"
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        f = f.readlines()
                    for line in f:
                        content += f'''{line}'''
                except Exception:
                    pass
                h_map[file_path] = content
    file_path_keys = natsort.natsorted(list(h_map.keys()))
    for file_path in file_path_keys:
        file_contents.append(h_map[file_path])
        file_names.append(file_path)
    return file_contents, file_names


@app.route("/<topics>", methods=['GET', 'POST'])
def topics(topics):
    global itr
    topic_folders = natsort.natsorted(load_topics(course_directory))
    try:
        itr = int(topic_folders.index(topics))
    except ValueError:
        pass
    if request.method == "POST" and request.form.get("back") and itr > 0:
        itr -= 1
        return render_template("topics.html", code_present=check_code_present(topic_folders[itr]), webpage=f"{topic_folders[itr]}/{topic_folders[itr]}.html",  folder=f"{topic_folders[itr]}", url=url)
    elif request.method == "POST" and request.form.get("forward") and itr < len(topic_folders)-1:
        itr += 1
        return render_template("topics.html", code_present=check_code_present(topic_folders[itr]), webpage=f"{topic_folders[itr]}/{topic_folders[itr]}.html", folder=f"{topic_folders[itr]}", url=url)
    elif request.method == 'POST' and request.form.get("home"):
        itr = 0
        return redirect("/")
    elif request.method == 'POST' and request.form.get("code_filesystem"):
        path = f"file:///{course_directory}/{topic_folders[itr]}"
        path = path.replace("\\", "/")
        webbrowser.open(path)
    return render_template("topics.html", code_present=check_code_present(topic_folders[itr]), webpage=f"{topic_folders[itr]}/{topic_folders[itr]}.html", folder=f"{topic_folders[itr]}", url=url)


@app.route("/code/<codes>", methods=['GET', 'POST'])
def codes(codes):
    file_contents, file_names = load_files(codes)
    return render_template("codes.html", file_contents=file_contents, file_names=file_names)


def clear():
    current_os = sys.platform
    if current_os.startswith('darwin'):
        os.system('clear')
    elif current_os.startswith('linux'):
        os.system('clear')
    elif current_os.startswith('win32') or current_os.startswith('cygwin'):
        os.system('cls')


def load_templates():
    my_loader = jinja2.ChoiceLoader([
        app.jinja_loader,
        jinja2.FileSystemLoader([f'{ROOT_DIR}/templates',
                                 f'{course_directory}']),
    ])
    app.jinja_loader = my_loader


def initialization():
    clear()
    print(f'''
                            Educative viewer, made by Anilabha Datta
                            Project Link: https://github.com/anilabhadatta/educative-viewer
                            Read the documentation for more information about this project.
                            
                            -> For Cloudflared, enter the following command in a new terminal
                                    cloudflared tunnel -url {ip_address}:{port} 
                            -> Leave Blank and press Enter to exit
            ''')


if __name__ == "__main__":
    ip_address, port = get_ip()
    initialization()
    localhost_url = f"http://{ip_address}:{port}"
    url = localhost_url
    tunnel_url = input(
        "Enter cloudflared tunnel url or Press Enter to skip: ")
    if "trycloudflare.com" in tunnel_url:
        url = tunnel_url
    try:
        while True:
            initialization()
            course_directory = input("Enter Course Directory Path: ")
            if "trycloudflare.com" not in tunnel_url:
                tunnel_url = input(
                    "Enter cloudflared tunnel url or Press Enter to skip: ")
                url = tunnel_url
            if course_directory == '':
                break
            elif os.path.isdir(course_directory):
                itr = 0
                root_course_path = course_directory
                load_templates()
                print(
                    f'''

                    To Open Mobile/Desktop View,
                    Tunnel Url: {tunnel_url} ,Localhost Url: {localhost_url}
                    
                    ''')
                app.run(host="0.0.0.0", threaded=True, port=port)
            else:
                print("Invalid path")
                input("Press enter to continue")
    except KeyboardInterrupt:
        print("Exited")
    except Exception as e:
        print("Exited", e)
