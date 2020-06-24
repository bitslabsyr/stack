#!env/bin/python

import sys
import os
import json

from werkzeug import generate_password_hash

from app.controller import Controller
from app.models import DB

basedir = os.getcwd()
db = DB()

def main():
    print('\n')
    print('STACK')
    print('----------')
    print('\n')

    print('Welcome to the STACK setup tool. Follow the instructions below to\nsetup your first project account and initialize the configuration\nfiles for your STACK toolkit.')
    print('\n')

    project_name = input('Enter a project account name: ')
    password = input('Enter a project account password: ')
    description = input('Enter a project account description: ')

    hashed_password = generate_password_hash(password)

    resp = db.create(project_name=project_name, password=password, hashed_password=hashed_password,
                     description=description)
    if resp['status']:
        print('\n')
        print('SUCCESS! You can now login to your account %s from the\n STACK front-end. Happy researching.' % project_name)
    else:
        print('\n')
        print('Oops. Something went wrong. Please try again and make sure\n the account name you entered does not already exist.')

if __name__ == "__main__":
    main()
