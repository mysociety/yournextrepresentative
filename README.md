# A PopIt frontend for sourcing candidate data

The idea of this project is to make a web-based front-end to
[PopIt](http://popit.poplus.org/) for crowd-sourcing candidates
who are standing in the next UK general election in 2015.

This is pretty functional now - we're testing with small numbers
of users at the moment, but will make it more widely available
soon.

## Known Bugs

You can find a list of known issues to work on here:

* https://github.com/mysociety/yournextmp-popit/issues

These are prioritized in Huboard:

* https://huboard.com/mysociety/yournextmp-popit

## Getting a development version running:

(These are very rough instructions, written for a colleague who
who's using Vagrant v1 for local development.)

Make a new directory, change into that directory and create a
`Vagrantfile` with:

    vagrant init precise64

Edit the Vagrantfile to forward a local port to the port that
the development server will be listening to, by adding this
line:

    config.vm.network :forwarded_port, guest: 8000, host: 8080

... in the `Vagrant.configure` block.

Start that vagrant box with:

    vagrant up

Log in to the box with:

    vagrant ssh

Install git, which you'll need to clone the repository:

    sudo apt-get update
    sudo apt-get install git

Clone the repository with:

    git clone --recursive <REPOSITORY-URL>

Copy the example configuration file to `conf/general.yml`:

    cp yournextmp-popit/conf/general.yml{-example,}

Edit `yournextmp-popit/conf/general.yml` to fill in details of
the PopIt instance you're using.

If that instance hasn't already been set up, then you can create
basic data in it with the `create-popit.py` script. (FIXME: add
more instructions for this.)

Install some required packages:

    sudo apt-get install python-virtualenv curl yui-compressor

Create a virtualenv with all the Python packages you'll need:

    yournextmp-popit/bin/pre-deploy

Edit the .bashrc to make the gems that has installed available
and the virtualenv be activated on login. Add these lines to the
end of `~/.bashrc`:

    export PATH="/home/vagrant/gems/bin:$PATH"
    export GEM_HOME='/home/vagrant/gems'
    source ~/venv/bin/activate

Now source your `.bashrc` for those changes to take effect:

    source ~/.bashrc

Create the database tables:

    cd yournextmp-popit
    ./manage.py syncdb

Add a superuser account:

    ./manage.py createsuperuser

Run the development server:

    ./manage.py runserver 0.0.0.0:8000

Now you should be able to see the site at:

    http://localhost:8080/

Go to the admin interface:

    http://localhost:8080/admin/

... and login with the superuser account.

### Restarting the development server after logging out

After logging in again, the only steps you should need to run
the development server again are:

    cd yournextmp-popit
    ./manage.py runserver 0.0.0.0:8000
