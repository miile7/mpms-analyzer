# -*- coding: utf-8 -*-
"""
Created on Mon Mar 19 09:13:52 2018

@author: Maximilian Seidler
"""

import os
import Constants

def listFiles(path, blacklist = (), groups = [], group = "main", parent = None):
    files = os.scandir(path)
    
    names = [i["name"] for i in groups]
    if group in names:
        current_index = names.index(group)
    else:
        groups.append({"name": group, "parent": parent, "values": []})
        current_index = len(groups) - 1
    
    for file in files:
        if file.name in blacklist :
            continue
        
        if file.is_dir():
            groups = listFiles(file.path, blacklist, groups, file.name, group)
        elif file.name.split(".")[-1] == "py":
            if file.name == "Controller.py":
                groups.append({"name": "Controller", "parent": group, "values": [file.name]})
            else:
                groups[current_index]["values"].append(file.name)
    
    return groups

def printGroups(groups, current_parent = None, used_groups = [], lvl = 0):
    html = ""
    
    for group in groups:
        if (group["name"] not in used_groups and 
            group["parent"] == current_parent and 
            len(group["values"]) > 0):
            
            if lvl == 1:
                html += "<fieldset class='group' data-group-name='{}'>\n".format(group["name"])
                html += "<legend>{}</legend>\n".format(group["name"])
            else:
                html += "<div class='group-higher-lvl'>\n"
            
            for name in sorted(group["values"]):
                html += "<div class='class'>{}</div>\n".format(".".join(name.split(".")[0:-1]))
            
            if lvl == 0:
                html += "</div>\n"
                
            used_groups.append(group["name"])
            html += printGroups(groups, group["name"], used_groups, lvl + 1)
            
            if lvl == 1:
                html += "</fieldset>\n"
            elif lvl > 1:
                html += "</div>\n"
    
    if lvl == 0:
        html += "<br />\n"
    
    return html
            

blacklist = (
        "__pycache__",
        "fit_squid_parameter.py",
        "noGUI.py",
        "noGUI_background_subtraction.py",
        "noGUI_csv_export.py",
        "noGUI_Anton_SrCu_symmetric.py",
        "noGUI_datapoint_viewer.py",
        "quick_create_background.py",
        "quick_cut_datapoint.py",
        "quick_remove_background.py",
        os.path.basename(__file__)
        )

path = str(os.path.dirname(os.path.abspath(__file__)))
groups = listFiles(path, blacklist)

file = open(path + "/klassendiagramme.html", "w+")

file.write(
"""<html>
    <head>
        <title>Klassendiagramme """ + Constants.NAME + """</title>
        <style>
            body{
                font-family: sans-serif;
                text-align: center;
                vertical-align: middle;
            }
            
            .class{
                vertical-align: middle;
                display: inline-block;
                padding: 20px;
                border: 1px solid #000;
                margin: 5px;
                background: #fff;
            }
            
            .group{
                vertical-align: middle;
                border: 3px dashed #000;
                /* max-width: calc(40% - 70px); */
                padding: 10px;
                /* display: inline-block; */
                margin: 20px;
            }
            
            .group[data-group-name='Controller']{
                margin: 20px;
                border: none;
                background: repeating-linear-gradient(
                  45deg,
                  #fff,
                  #fff 10px,
                  #eee 10px,
                  #eee 20px /* determines size */
                );
            }
            
            .group[data-group-name='Controller'] legend{
                display: none;
            }
        </style>
    </head>
    <body>""")

file.write(printGroups(groups))

file.write("""
    </body>
</html>""")

file.close()