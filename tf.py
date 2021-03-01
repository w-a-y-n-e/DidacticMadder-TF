from flask import Flask
import uuid
from collections import defaultdict
import subprocess
import json
import time
import os
import pathlib
import random
import socket

from multiprocessing import Pool
database_file = 'infrastructure.db'

import sqlite3


script_dir=os.path.dirname(os.path.realpath(__file__))

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

app = Flask(__name__)

ports_used = list()
main_ip = get_ip()
scenario_listing=[str(eachpath.name) for eachpath in pathlib.Path.cwd().glob("*") if eachpath.is_dir()]
CWD=''

def get_free_port():
    while True:
        check_port=random.randint(1025,2048)
        if check_port not in ports_used:
            ports_used.append(check_port)
            return check_port

def iptables_wrapper(action,nat_ip,port_to_forward=None,destination_port=None):
    if action and nat_ip:
        if port_to_forward and destination_port:
            subprocess.run(['sudo', './port_forwarding.sh', action, str(nat_ip), str(port_to_forward), str(destination_port)], cwd=script_dir)
        if not port_to_forward and not destination_port:
            subprocess.run(['sudo', './port_forwarding.sh', action, str(nat_ip)], cwd=script_dir)

def start_vms(username, scenario_id):
    CWD = f'./{scenario_id}/'
    workspace_id = f"{username}_{scenario_id}"
    print(f"Starting {workspace_id}")
    subprocess.run(['/usr/bin/terraform', 'workspace', 'new', '-lock-timeout=30s', workspace_id], cwd=CWD)
    subprocess.run(['/usr/bin/terraform', 'workspace', 'select', workspace_id], cwd=CWD)
    subprocess.run(['/usr/bin/terraform', 'apply', '-auto-approve', '-lock-timeout=30s'], cwd=CWD)
    p = subprocess.run(['/usr/bin/terraform', 'output', '-json'], cwd=CWD, stdout=subprocess.PIPE)
    terraform_output_json = p.stdout
    terraform_output_dict = json.loads(terraform_output_json)

    p = subprocess.run('''terraform show -json | jq '[.values.root_module.resources[] | select (.type | contains("domain")) | .values.name]' ''', shell=True, cwd=CWD, stdout=subprocess.PIPE)
    terraform_domains_json = p.stdout
    terraform_domains_list = json.loads(terraform_domains_json)

    conn = sqlite3.connect(database_file)
    with conn:
        cur = conn.cursor()

        for d in terraform_domains_list:
            p = subprocess.run(['/usr/bin/virsh', 'vncdisplay', d], cwd=CWD, stdout=subprocess.PIPE)
            virsh_output_vnc = p.stdout.decode().split(":")
            if len(virsh_output_vnc) > 1:
                virsh_output_vnc = virsh_output_vnc[1]
                vnc_port=int(virsh_output_vnc) + 5900
                cur.execute('insert into connections (ref_username,ref_scenario_id,connection_name,admin,access_port,protocol) values (?,?,?,1,?,"vnc");', (username, scenario_id, f"{d}_admin", vnc_port))
                iptables_wrapper('A', vnc_port)
        if 'ip' in terraform_output_dict:
            terraform_output=terraform_output_dict['ip']['value']
            for c_name, c_details in terraform_output.items():
                free_port=get_free_port()
                cur.execute('insert into connections (ref_username,ref_scenario_id,connection_name,admin,access_port,protocol,internal_ip,internal_port) values (?,?,?,0,?,?,?,?);', (username, scenario_id, c_name, free_port, c_details[2], c_details[0], c_details[1] ))
                iptables_wrapper('A', c_details[0], free_port, c_details[1])
            print("NEED TO RETURN JSON OF CONNECTIONS")

        cur.execute("update vms set built=1 where username=? and scenario_id=?;", (username, scenario_id))
        conn.commit()
        print("Completed!")

def stop_vms(username, scenario_id):
    CWD = f'./{scenario_id}/'
    workspace_id = f"{username}_{scenario_id}"
    print(f"Deleting {workspace_id}")
    conn = sqlite3.connect(database_file)
    conn.execute("PRAGMA foreign_keys = ON")
    with conn:
        cur = conn.cursor()
        cur.execute("select admin,access_port,protocol,internal_ip,internal_port from connections where ref_username=? and ref_scenario_id=?;", (username, scenario_id))
        rows = cur.fetchall()

        for row in rows:
            #print(row)
            if row[1]:
                if (not row[3] and not row[4]):
                    iptables_wrapper('D', row[1])
                elif (row[3] and row[4]):
                    iptables_wrapper('D', row[3], row[1], row[4])
            #ports_used.remove(row[1])

        subprocess.run(['/usr/bin/terraform', 'workspace', 'select', workspace_id], cwd=CWD)
        subprocess.run(['/usr/bin/terraform', 'destroy', '-auto-approve', '-lock-timeout=30s'], cwd=CWD)
        subprocess.run(['/usr/bin/terraform', 'workspace', 'select', 'default'], cwd=CWD)
        subprocess.run(['/usr/bin/terraform', 'workspace', 'delete', '-lock-timeout=30s', workspace_id], cwd=CWD)

        cur.execute("delete from vms where username=? and scenario_id=? and built=1;", (username, scenario_id))
        conn.commit()
        print("Deleted")

@app.route('/')
def show_usage():
    return 'Usage: /username/scenario_id/[end]'

@app.route("/<username>/<scenario_id>/")
def start_instance(username, scenario_id):
    if scenario_id not in scenario_listing:
        return f"{scenario_id} not found", 404
    workspace_id = f"{username}_{scenario_id}"
    conn = sqlite3.connect(database_file)
    with conn:
        cur = conn.cursor()
        cur.execute("select built from vms where username=? and scenario_id=?;", (username, scenario_id))
        rows = cur.fetchone()

        if(not rows):
            cur.execute('insert into vms (username,scenario_id) values (?,?);', (username,scenario_id))
            conn.commit()
            pool.apply_async(start_vms,(username,scenario_id))
            return "Create requested", 202
        elif rows[0]==0:
            return "In progress", 202
        elif rows[0]==1:
            cur = conn.cursor()
            cur.execute("select connection_name, admin, access_port, protocol from connections where ref_username=? and ref_scenario_id=?;", (username, scenario_id))
            rows = cur.fetchall()
            return json.dumps(rows), 201

@app.route("/<username>/<scenario_id>/end")
def end_instance(username, scenario_id):
    if scenario_id not in scenario_listing:
        return f"{scenario_id} not found", 404
    workspace_id = f"{username}_{scenario_id}"
    conn = sqlite3.connect(database_file)
    with conn:
        cur = conn.cursor()
        cur.execute("select destroy,built from vms where username=? and scenario_id=?;", (username, scenario_id))
        rows = cur.fetchone()

        if(not rows):
            return "Nothing to delete", 404
        if rows[0]==1:
            return "Delete already in progress", 202
        if rows[1]==0:
            return "Not built yet", 409
        else:
            pool.apply_async(stop_vms, (username, scenario_id))
            cur.execute("update vms set destroy=1 where username=? and scenario_id=? and destroy=0 and built=1;", (username, scenario_id))
            conn.commit()
            return "Delete requested", 202

if __name__ == '__main__':
    pool = Pool(processes=1)
    conn = sqlite3.connect(database_file)
    conn.execute('CREATE TABLE IF NOT EXISTS VMS (username text, scenario_id text, start_time text, time_limit integer, built boolean default 0, destroy boolean default 0, primary key(username, scenario_id));')
    conn.execute('CREATE TABLE IF NOT EXISTS CONNECTIONS (ref_username text not null, ref_scenario_id text not null, connection_name text, admin boolean default 0, access_port int not null, protocol text not null, internal_ip text, internal_port int, FOREIGN KEY (ref_username, ref_scenario_id) REFERENCES VMS(username, scenario_id) on delete cascade);')
    conn.close()
    app.run(host='0.0.0.0')


# Security (SSL)
# Error handling if
