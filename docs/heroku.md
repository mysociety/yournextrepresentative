# Running YourNextRepresentative on Heroku

### Introduction

Note that this only covers installing and running on Heroku.
Please see [our guide to setting up YourNextRepresentative for a new country](./new-instance.md)
for details on setting up the data.

### Preliminaries

This assumes you have a Heroku account and have installed the Heroku
Command Line Interface. For more details on this and a basic
introduction to running Python apps on Heroku see
[Heroku's Getting Started guide](https://devcenter.heroku.com/articles/getting-started-with-python#introduction).

### Fetch the code

Clone the YourNextRepresentative respository from GitHub:

```
git clone https://github.com/mysociety/yournextrepresentative.git
```

### Initial setup

Firstly you need to create a Heroku app and deploy the code to it using
the standard Heroku procedure for this:


```
heroku apps:create <Name of app>
git push heroku master
```

### Environment Variables

Next we need to tell YourNextRepresentative that it should load
configuration information from environment variables rather than a file:

```
heroku set CONFIG_FROM_ENV=True
```

As well as this we need to let YourNextRepresentative know it is runnig
on Heroku so it behaves in a way appropriate to the Heroku platform. At
the same time we tell it not to try to save any minified Javascript or
compiled SASS to the disk as Heroku apps run on a read only file system:


```
heroku set ON_HEROKU=1
heroku DISABLE_COLLECTSTATIC=1
```

Setting `ON_HEROKU` alters how the database connection details are
loaded and also how the application is run by WSGI.

And now set some of the standard YourNextRepresentative configuration
options:

```
heroku set STAGING=1
heroku set ELECTION_APP=<name of election app, e.g. uk>
heroku set SECRET_KEY=<this should be a random string of numbers and letters>
```

You will need to configure more of these later but these are the bare
minimum required to get the app up and running.

### Create the database

Now you should run Django's database migrations to set up the database:

```
heroku run python manage.py migrate
```

### Check things are running

At this point you should be able to use `heroku open` to open a browser
window with your YourNextRepresentative app. If that doesn't work then
you can check the logs using `heroku logs` to see what has gone wrong.

The most likely thing is that one of the Environment varables has not
been set correctly.

### Set up a super user

In order to allow us to log in to the admin interface we need to create
a super user:

```
heroku run python manage.py createsuperuser
```

### Other configuration options

There's lots of other configuration options which you can see in [the
example configuration file](../conf/general.yml-example) which also
contains notes on the values for those. If you are just testing how
YourNextRepresentative works then you probably don't need to set them.

Note that Heroku takes care of the database settings so you can ignore
that part of the file.

However, if you are in the United States or a country that uses the same
date conventions then setting `DD_MM_DATE_FORMAT_PREFERRED` will make
entering dates easier.

### Setting up the data

From here on the process is the same as the [standard install](./new-instance.md)
except for running commands using `heroku run`. Also, any reference to
edit the configuration file should be replaced by running `heroku set`.
