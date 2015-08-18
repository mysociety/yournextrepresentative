# A PopIt frontend for sourcing candidate data

YourNextRepresentative is a web application for crowd-sourcing candidates for
upcoming elections. It was created for the UK's 2015 General Election, where it
ran successfully as [YourNextMP](https://yournextmp.com).

### Why YourNextRepresentative?

In the UK, there's no single, official source of candidate data before the
election. But if this data exists, developers can build tools that help inform
citizens about who they can vote for. The data gathered in this way has
longevity: after an election, the database contains elected representatives.

This situation is not uncommon: before elections, it's useful to have access to
the data about candidates, but for a variety of reasons, this is often not easy
to get. YourNextRepresentative lets you gather this data where the official
data is either missing or incomplete.

In the UK,
[YourNextMp's data was widely used](https://www.mysociety.org/2015/04/23/have-you-seen-yournextmp-lately/)
by developers, journalists, and beyond.

The project is effectively a web-based front-end to a [PopIt](http://popit.poplus.org/) database, although we're working to de-couple
that so it's more general.

## What you need to know before you start

* Currently, you must have a Popit database (although we're currently working
  on removing that dependency). See
  [popit.mysociety.org](http://popit.mysociety.org) -- it's easy and free to
  set up on our hosted service.
* YourNextRepresentative is written in Python using the
  [Django framework](http://djangoproject.com/).
* We think you need to be familiar with Django, and have some confidence with
  Unix (managing packages, creating symbolic links on the command line, etc.)
  to deploy it.
* If you want to run YourNextRepresentative, the first step is *always* to get
  a development version running first -- the example below uses
  [Vagrant virtual box](https://www.vagrantup.com/).
* You can customise the core application by overriding features in your own
  Election app (that's a Dajngo application within the core application). This
  means you're free to change both the behaviour and the appearance of your
  site. (But did we mention that you'll need to know Django to do this easily?)
* We use [Sass](http://sass-lang.com/) to define the CSS stylesheets.

## Known Bugs

YourNextRepresentative is in active development!
You can find a list of known issues to work on here:

* https://github.com/mysociety/yournextrepresentative/issues

These are prioritized in Waffle:

* https://waffle.io/mysociety/yournextrepresentative


## Get a development version running:

The following instructions are for getting YourNextRepresentative running on
your local machine, using Vagrant.

Make a new directory named after your project (for example, in the UK this was `yournextmp`; the examples below use `myproject` which you should replace with your project's name). Change into that directory and clone the repository:

    cd myproject
    git clone --recursive https://github.com/mysociety/yournextrepresentative

Copy the example Vagrantfile to the root of your new directory:

    cp yournextrepresentative/Vagrantfile-example ./Vagrantfile

Copy the example configuration file to one named after your own project `conf/general-myproject.yml`:

    cp yournextrepresentative/conf/general.yml-example yournextrepresentative/conf/general-myproject.yml

Create a symbolic link to this file, called `general.yml` (the application
expects to find `conf/general.yml` and also checks that it is a symlink).

    cd yournextrepresentative/conf
    ln -s general-yournextmp.yml general.yml
    cd -

Edit `yournextrepresentative/conf/general.yml`:

  * Nominate the election you want to use -- this is the `ELECTION_APP`
    config setting, and it must match one of the Django apps found within
    the `/elections` directory. The "default" one, is `simple_election`,
    but you can also try any of the others if you're curious to see
    what they look like 
  * Fill in details of the PopIt instance you're using -- to find your own
    PopIt API key, log into your PopIt instance, and click on your
    profile link in the top right-hand corner: choose *Get API key*).

Now start that vagrant box with:

    vagrant up

This may take a little time, especially the first time, because Vagrant
provisions all the system libraries and so on. You'll see lots of output on the
screen while it reports what it's doing.

When it's finished, log in to the box with:

    vagrant ssh

Move to the app directory:

    cd yournextrepresentative

Add a superuser account (using Django's own management tool):

    ./manage.py createsuperuser

Run the development server:

    ./manage.py runserver 0.0.0.0:8000

Now you should be able to see the site at:

    http://127.0.0.1.xip.io:8000/

The site `[xip.io](http://xip.io/)` is mapping onto your own `localhost`.
This means you *can* use `http://localhost:8000` but generally `xip` will
behave well *FIXME: why?**

Go to the admin interface:

    http://127.0.0.1.xip.io:8000/admin/

...and login with the superuser account.

If you want to create a PopIt database based on an existing live
instance, see the "Mirror the live database into your
development copy" section below, and follow those steps at this
stage.

You can stop the server from within Vagrant by hitting `^C`.

### Restarting the development server after logging out

You don't need to provision the Vagrant box again. If you stop the virtual
machine (with `vagrant halt`), you can start it up again with `vagrant up` and
it won't take so long as the very first time.

After logging in again, the only steps you should need to run
the development server again are:

    cd yournextrepresentative
    ./manage.py runserver 0.0.0.0:8000

### Running the tests

SSH into the vagrant machine (`vagrant ssh`), then run:

    cd yournextrepresentative
    ./manage.py test

### Mirror the live database into your development copy

You may already have a live PopIt database with some potential candidate information in it. If so, you should make a local copy for your development
server to work with.

You'll need to install a local version of PoPit: see
[the PopIt github repo](https://github.com/mysociety/popit) and
[the installation docs](http://popit.poplus.org/docs/install/).

Download the live database, and save the location in an environment variable:

    ./manage.py candidates_get_live_database
    export DUMP_DIRECTORY="$(pwd)"

Assuming you have a local development instance of PopIt, change
into the root of the PopIt repository, and run:

     NODE_ENV=development bin/replace-database \
         "$DUMP_DIRECTORY"/yournextrepresentative- \
         candidates \
         popitdev__master

...replacing `candidates` with the slug of your YourNextRepresentative
PopIt instance, and `popitdev__master` with the name of your PopIt
master database in MongoDB.

Then set the maximum PopIt person ID by running:

    ./manage.py candidates_set_max_person_id

### Customizing YourNextRepresentative for a new election

Once you've got a development version up and running, you can start building a
customised version to collect information about candidates.

You need to create a new Election app, in the `elections` directory. We
strongly recommend you duplicate `simple_election` and build your site up from
there. The rest of this section describes how.

We've stripped down `simple_election` to use basic colours and minimal templates. Remember you can override any templates: for examples of this
at work, have a look inside the "real" elections that have already been run
in the Real World:

* `elections/ar_elections_2015` for 2015 elections in Argentina
* `elections/uk_general_election_2015` for the UK's national election

To start with, the changes may be straighforward, but elections vary
considerably from country to country, so we know it's likely that you'll need
to add specific customisations too. That's OK: you do it by overriding specific
parts within the Django app, and it's why we recommend you start by duplicating
the `simple_election` one... because later you can customise its code however
you need.

> Don't simply edit the `simple_election` application -- be sure to follow
> the steps below and duplicate it, giving it your own project name.

#### Duplicate the `simple_election` election application

If you've got YourNextRepresentative running as a development server on your
local machine (from the instructions above), close it down (ctl-C in the
server window) and update the source code and configuration as follows.

Start in the `yournextrepresentative` directory.

You can manipulate the files from within Vagrant, or from your local machine's
native command line -- it doesn't matter because the `yournextrepresentative`
can be accessed from either of them.

In the `elections` directory, copy the `simple_election` directory (and all its
contents) and give it the name of your own election:

    cp elections/simple_election elections/yourelection

#### Set ELECTION_APP to be your election application

Edit `conf/general.yml` (which is a symlinked version of a copy of
`conf/general.yml-example`, from when you set up the development version).

Set `ELECTION_APP` in your `general.yml` to the name of that application (not
including `elections.`).

####  Edit `settings.py` in your application

In your application, edit the `settings` module which defines `ELECTIONS`. That
is, edit

    elections/yourelection/settings.py

You probably only need to specify one election in there, but as you'll see,
`ELECTIONS` can contain more than one. See the comments in that file for hints
on what each of the settings is for.

#### Further customisation

The election app is a Django application, so you can override templates and so 
on as you would any other Django application. Remember you can also see examples
of this being done in the `ar_elections_2015` and `uk_general_election_2015`
apps.

* Override generic templates in your election application.

* Add a `urls.py` and `views.py` and override and augment and of the
  generic URLs that you want to customize.

* Some data and behaviour will need to be customized by adding
  functions or variables in `lib.py` in your election application.

You will also have to decide if you you want to create "party sets" or
"post groups" for the elections you're supporting.  These are
potentially confusing, so here are some quick descriptions:

#### Party Sets

It's sometimes the case that there are different sets of parties
available for different posts that are up for election.  (For example,
in the UK General Election, there are distinct registers of parties
for constituencies in Northern Ireland and Great Britain.)

#### Post Groups

Each post can be in a particular "post group". These are only used to
group the posts on the party detail page for a particular
election. (For example, in the UK General Election, it was useful to
group posts on that page by whether they were associated with a
constituency in England, Scotland, Northern Ireland or Wales.

### Translating the interface

We use the standard mechanism of i18n within Django. That is, strings for
translation in the templates are all within Django's `trans` and `blocktrans`,
and in views with gettext() (or its aliased `_()` version). If you add your own
templates, please consider using this convention too.
See [the Django docs](https://docs.djangoproject.com/en/1.8/topics/i18n/translation/)
for lots more detail. Please also read
[mySociety's information on internationalization](http://mysociety.github.io/internationalization.html).

Use:

    django-admin makemessages

...to create message files. Once those are translated, use:

    django-admin compilemessages

...to make them available in the application.
 
If you want to run your application in a different language, make sure
the locale is installed. For example, in the Vagrant box you may need
to do:

    sudo locale-gen <LOCALE_NAME>

...to install a new locale.




