#!/usr/bin/python

import pycurl
import datetime
import pygtk
import ConfigParser
import StringIO
import xml.dom.minidom
import sqlite3 as sqlite
from xml.dom.minidom import Node

class TickAPI:

    def __init__(_self, company, email, password):
        global gC, gE, gP, gR, gD, db
        gC = company
        gE = email
        gP = password
        gR = ""
        db = sqlite.connect(':memory:')

    def load(_self):
        global gC, gE, gP, gR, gD, db
        url = "https://"+gC+".tickspot.com/api/clients_projects_tasks"
        params = "email="+gE+"&password="+gP
        gR = ""

        c = pycurl.Curl()
        c.setopt(c.URL, url)
        c.setopt(c.POST, 1)
        c.setopt(c.POSTFIELDS, params)
        c.setopt(c.WRITEFUNCTION, _self.handleResponse)
        c.perform()

        gD = xml.dom.minidom.parseString(gR)
        crs = db.cursor()
        crs.execute("CREATE TABLE clients (id INTEGER PRIMARY KEY, name VARCHAR(255))")
        crs.execute("CREATE TABLE projects (id INTEGER PRIMARY KEY, client_id INTEGER, name VARCHAR(255))")
        crs.execute("CREATE TABLE tasks (id INTEGER PRIMARY KEY, project_id INTEGER, name VARCHAR(255))")
        db.commit()

        for client in gD.getElementsByTagName('client'):
            for child in client.childNodes:
                if child.nodeType != Node.TEXT_NODE:
                    if child.tagName == "id":
                        clientID = child.childNodes[0].data
                    if child.tagName == "name":
                        clientName = child.childNodes[0].data
            crs.execute("INSERT INTO clients VALUES ("+clientID+",'"+clientName+"')")
            for project in client.getElementsByTagName('project'):
                for child in project.childNodes:
                    if child.nodeType != Node.TEXT_NODE:
                        if child.tagName == "id":
                            projectID = child.childNodes[0].data
                        if child.tagName == "name":
                            projectName = child.childNodes[0].data
                crs.execute("INSERT INTO projects VALUES ("+projectID+","+clientID+",'"+projectName+"')")
                for task in project.getElementsByTagName('task'):
                    for child in task.childNodes:
                        if child.nodeType != Node.TEXT_NODE:
                            if child.tagName == "id":
                                taskID = child.childNodes[0].data
                            if child.tagName == "name":
                                taskName = child.childNodes[0].data
                    crs.execute("INSERT INTO tasks VALUES ("+taskID+","+projectID+",'"+taskName+"')")
        db.commit();


    def getClients(_self):
        global db
        clients = []
        crs = db.cursor()
        crs.execute("SELECT * FROM clients")
        for client in crs.fetchall():
            clients.append({"id":client[0], "name":client[1]})
        return clients

    def getProjectsByClientID(_self, cID):
        global db
        projects = []
        crs = db.cursor()
        crs.execute("SELECT * FROM projects WHERE client_id = "+str(cID))
        for project in crs.fetchall():
            projects.append({"id":project[0], "name":project[2]})
        return projects

    def getTasksByProjectID(_self, pID):
        global db
        tasks = []
        crs = db.cursor()
        crs.execute("SELECT * FROM tasks WHERE project_id = "+str(pID))
        for task in crs.fetchall():
            tasks.append({"id":task[0], "name":task[2]})
        return tasks

    def createEntry(_self, tID, hours, date, notes):
        global gC, gE, gP, gR, gD, db
        url = "https://"+gC+".tickspot.com/api/create_entry"
        params = "email="+gE+"&password="+gP+"&task_id="+str(tID)+"&hours="+str(hours)+"&date="+str(date)+"&notes="+notes
        gR = ""

        c = pycurl.Curl()
        c.setopt(c.URL, url)
        c.setopt(c.POST, 1)
        c.setopt(c.POSTFIELDS, params)
        c.setopt(c.WRITEFUNCTION, _self.handleResponse)
        c.perform()

        print gR


    def handleResponse(_self, response):
        global gR
        gR+=response


class ticktimer:


    def __init__(_self):
        global config, api
        config = ConfigParser.RawConfigParser()
        config.read("ticktimer.cfg")
        api = TickAPI(config.get('API', 'company'), config.get('API', 'email'), config.get('API', 'password'))
        api.load()

    def selectClient(_self):
        global api
        clients = api.getClients()
        inc = 0
        clt = [];
        print "CLIENTS:"
        for c in clients:
            print "["+str(inc)+"]: "+c['name']
            clt.append(c['id'])
            inc = inc+1;
        client_id = raw_input('Enter a client number: ')
        return clt[int(client_id)]

    def selectProject(_self, clientID):
        global api
        projects = api.getProjectsByClientID(clientID)
        inc = 0
        prj = [];
        print "PROJECTS:"
        for p in projects:
            print "["+str(inc)+"]: "+p['name']
            prj.append(p['id'])
            inc = inc+1;
        project_id = raw_input('Enter a project number: ')
        return prj[int(project_id)]

    def selectTask(_self, projectID):
        global api
        tasks = api.getTasksByProjectID(projectID)
        inc = 0
        tsk = [];
        print "TASKS:"
        for t in tasks:
            print "["+str(inc)+"]: "+t['name']
            tsk.append(t['id'])
            inc = inc+1;
        task_id = raw_input('Enter a task number: ')
        return tsk[int(task_id)]

    def getTime(_self):
        return raw_input('Number of hours: ');

    def submitEntry(_self, cID, pID, tID, time, notes):
        global api
        api.createEntry(tID, time, datetime.date.today(), notes)


if __name__ == "__main__":
    tt = ticktimer()
    cl = tt.selectClient()
    pr = tt.selectProject(cl)
    tk = tt.selectTask(pr)
    tm = tt.getTime()
    tt.submitEntry(cl, pr, tk, tm, raw_input('Notes: '))
