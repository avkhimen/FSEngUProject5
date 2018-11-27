# Linux Server Configuration #

The project is to deploy the **flask** Item Catalog application from Udacity's Item Catalog project (link [here](https://github.com/avkhimen/FSEngUProject5)) onto the Amazon Web Services (AWS) server using the **postgresql** relational database to be accessible on the world wide web with the server's IP address. The application is accessible from the following url: _[http://52.12.16.248.xip.io/](http://52.12.16.248.xip.io/)_ and the connection to the server is available via port 2200. 

### Getting Started ###

##### Prerequisites #####

In order to compile python applications, you will need a terminal program. You can download `git` from [here](https://git-scm.com/download/win). Install git bash on your machine. In order to work in the Linux environment, you can install Vagrant from this link [here](https://www.vagrantup.com/downloads.html). Install Vagrant on your machine. The link to the flask documentation is [here](http://flask.pocoo.org/).

The _[https://github.com/avkhimen/FSEngUProject5](https://github.com/avkhimen/FSEngUProject5)_ repository contains the files that generate the application. The `__init__.py` file is the file that provides functionality for the item catalog application. The _templates_ folder contains the html templates of the web-pages that the `__init__.py` file accesses. The `database_setup.py` file contains all the setup configurations for the data tables that will be used to store item information. The `countryfooditems.py` file contains the initial few items that will be stored in the database. 

The following changes were applied to the files from the Item Catalog project to enable them to be displayed on the live server:

- `client_secrets.json` was updated to include the addition of the _[http://52.12.16.248.xip.io/](http://52.12.16.248.xip.io/)_ url.
- `application.py` file was renamed `__init__.py`.
- `database_setup.py`, `__init__.py`, and `countryfooditems.py` were modified for `engine = create_engine('postgresql://catalog:catalog@localhost/catalog')`
- in `__init__.py` the code `app.run(host='0.0.0.0', port=5000, threaded=False)` was modified to `app.run()`
- in `__init__.py` added absolute path to `client_secrets.json` to be `/var/www/FlaskApp/FlaskApp/client_secrets.json`

##### Installing #####

Please follow these steps:

1. Using `git` login into the server using `ssh grader@52.12.16.248 -p2200 -i graderkey` command.
2. In order to deploy the web application on the live server the contents of the application must be stored on the server in the `/var/www/` directory. Navigate to the `/var/www/` directory using `cd /var/www/` command.
3. Create the `FlaskApp` directory using `mkdir FlaskApp` and navigate into it using `cd FlaskApp`. This directory will house the `.wsgi` file that will execute the `__init__.py` file.
4. Using `sudo touch FlaskApp.wsgi` create the file `FlaskApp.wsgi` and paste the following into it:

            `#!/usr/bin/python
            import sys
            import logging
            logging.basicConfig(stream=sys.stderr)
            sys.path.insert(0,"/var/www/FlaskApp/")
            from FlaskApp import app as application
            application.secret_key = 'Add your secret key'`

5. Create the `FlaskApp` directory using `mkdir FlaskApp` and navigate into it using `cd FlaskApp`. This directory will house the files that will generate the application. Using `git` populate the directory with the files from the _[https://github.com/avkhimen/FSEngUProject5](https://github.com/avkhimen/FSEngUProject5)_ github repository. 
6. Navigate to `/etc/apache2/sites-enabled` directory using `cd /etc/apache2/sites-enabled` to create the `.conf` file for the `FlaskApp` directory. 
7. The `.conf` file for the application is called `FlaskApp.conf`. Create the file using `sudo touch FlaskApp.conf` and populate it with:
        
        `<VirtualHost *:80>
                        ServerName 52.12.16.248.xip.io
                        ServerAdmin admin@52.12.16.248
                        WSGIScriptAlias / /var/www/FlaskApp/FlaskApp.wsgi
                        <Directory /var/www/FlaskApp/FlaskApp/>
                                Order allow,deny
                                Allow from all
                        </Directory>
                        Alias /static /var/www/FlaskApp/FlaskApp/static
                        <Directory /var/www/FlaskApp/FlaskApp/static/>
                                Order allow,deny
                                Allow from all
                        </Directory>
                        ErrorLog ${APACHE_LOG_DIR}/error.log
                        LogLevel warn
                        CustomLog ${APACHE_LOG_DIR}/access.log combined
        </VirtualHost>`

8. Install **postgresql** using `sudo apt-get install postgresql` command. 

### Run the Application ###

The application is designed to display on the _[http://52.12.16.248.xip.io/](http://52.12.16.248.xip.io/)_ url. To launch the application, do the following:

1. Navigate to the `/var/www/FlaskApp/FlaskApp` directory using `cd /var/www/FlaskApp/FlaskApp`.
2. Run `sudo -u postgres psql` to login as `postgres` user. 
3. Create the `catalog` database to house the food items using the `CREATE DATABASE catalog` command.
4. Log out of **postgresql** by typing `\q`. Type `\q` again.  
2. Run the `countryfooditems.py` file using the `python countryfooditems.py` command to populate the `catalog` database with food items. You should see the '_added food items!_' message display in `git`.
1. Activate the `FlaskApp.conf` file by typing `sudo a2ensite FlaskApp` in `git`.
2. Restart the `Apache2` server using `sudo service apache2 reload` command. 

See the application on _[http://52.12.16.248.xip.io/](http://52.12.16.248.xip.io/)_. In order to perform the CRUD operations on the items in the database the user must sign in with their existing gmail or Google+ account. Otherwise the use can only see the items in the database. 

### Design of the Code ###

The `database_setup.py` file imports all the necessary **SQL-Alchemy** modules and then proceeds to define two main classes used in the structure of the database. The `Country` class assigns an id to each country in the database and contains its name. The `FoodItem` class has a foreign-key relationship to the country which the food item is from and contains its name and description.

The `__init__.py` file imports all the necessary **flask** modules and then defines each route and the function associated with that route. Each function queries the database based on the route input parameters to extract the items needed and then either returns an input to another function or returns an html page with content. 

The `.html` files are html templates used by the `__init__.py` file to display the database items. The `.html` files are constructed with a combination of html and css.

### Built With ###

**Flask** - web framework
**SQl-Alchemy** - ORM database framework
**Postgresql** - object-relational SQL database
**AWS** - server provider

### Resources ###

**[How To Deploy a Flask Application on an Ubuntu VPS](https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps)** - tutorial explaining how to set up a **flask** application on Ubuntu OS. 

### Packages ###

From [https://packages.ubuntu.com/](https://packages.ubuntu.com/) the following packages were used:

- **apache2** - Apache HTTP Server
- **libapache2-mod-wsgi** - Python WSGI adapter module for Apache
- **postgresql** - object-relational SQL database
