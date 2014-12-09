#!env/bin/python

import sys
import os
import json

from stack.controller import Controller
from stack.db import DB

basedir = os.getcwd()
db = DB()

def main():
    print '\n'
    print 'STACK v1.0'
    print '----------'
    print '\n'

    print 'Welcome to the STACK setup tool. Follow the instructions below to\nsetup your first project account and initialize the configuration\nfiles for your STACK toolkit.'
    print '\n'

    project_name = raw_input('Enter a project account name: ')
    password = raw_input('Enter a project account password: ')
    description = raw_input('Enter a project account description: ')

    project_list = [{
        'project_name': project_name,
        'password': password,
        'description': description
    }]

    resp = db.setup(project_list)
    if resp['status']:
        print '\n'
        print 'SUCCESS! You can now login to your account %s from the\n STACK front-end. Happy researching.' % project_name
    else:
        print '\n'
        print 'Oops. Something went wrong. Please try again and make sure\n the account name you entered does not already exist.'

if __name__ == "__main__":
    main()
