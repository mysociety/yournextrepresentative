# A PopIt frontend for sourcing candidate data

The idea of this project is to make a web-based front-end to
[PopIt](http://popit.poplus.org/) for crowd-sourcing candidates
who are standing in the next UK general election in 2015.

Why wouldn't we do this just in the standard PopIt web
interface? This is a good question, and the reasons initially
were:

* Currently, if you use the PopIt web interface to add a person,
  it's very tailored to adding representatives in a
  constituency-based parliament - it's not clear how you should
  add candidates, and the obvious way ends up creating data that
  doesn't make much sense in the Popolo data model.  (Thus, it's
  confusing to use the API to retrieve these people afterwards.)
  If we have a custom front-end that can constrain data to be
  entered in a way such that it's immediately usable.
  (See https://github.com/mysociety/popit/issues/604 )

* PopIt doesn't currently support versioning or rollback of data
  that has been entered.  However, if we had a custom frontend,
  you could add a "versions" field to each person (say) that
  tracks how that person's data has been changed over time and
  allows a one-click rollback. (See
  https://github.com/mysociety/popit/labels/versioning )

* PopIt has only recently had support added for allowing
  multiple users to edit a repository, but those users
  currently have to be added by the repository owner, so you
  can't easily allow crowd-sourcing of data without a lot of
  intervention from the owner.

* PopIt doesn't currently support autocompletion of area names
  or constraining them to some useful set (e.g. a
  [MapIt](http://mapit.mysociety.org/) type and generation) so
  when people enter constituency names, they might use variant
  spellings, constituencies that no longer exists, etc. This is
  easy to enforce in a custom front-end. (See
  https://github.com/mysociety/popit/issues/564 )

@mhl volunteered to work on this, and paired with @jennyd for a
large part of it, but both have had very little time for the
project - also, it's more involved than one might think at
first.

Arguably, a better solution might be to put time into fixing the
PopIt issues listed above - after all, they will need to be done
soon anyway, and there's not necessarily any point in
duplicating that effort in a one-off front-end.  The argument
against that is that
[people have some candidate data already](https://github.com/DemocracyClub/ge2015-candidates/)
and we want to get going with collecting this data as soon as
possible.

Whatever is decided, here's a small Django project that makes a
start on such a custom front-end.  I'm putting this on GitHub
since I really have to take holiday for the first time in ages
and someone else from mySociety or elsewhere may be able to take
it over for the next couple of weeks.

## Things Already Done:

* A script that will import all the old YourNextMP data from the
  last election (which you can download from
  [YourNextMP](http://www.yournextmp.com/) into a PopIt instance
  using the PopIt API.  This also sets up "Candidate List"
  organisations for each constituency for both the 2010 and 2015
  elections, and creates an organisation for each party in that
  2010 data. (See below for more about this data model.)

* A front page that lets you enter a postcode or a constituency
  and takes you to a constituency page.

* A constituency page that:

  * Lists all the candidates from YourNextMP for the 2010
    election with their party, and allows you to click to
    indicate that they're standing for that constituency again.

  * Lists all the candidates currently thought to be standing in
    2015 with their party and allows you to click to indicate
    that they're not actually standing.

  * A form to add a new candidate with their basic contact
    details, Twitter username, etc.

  * Similarly, allow the contact details (or 2015 constituency)
    of any candidate to be edited.

So this is enough for basic entry of candidate data, but there's
a lot more that should be done to make this a useful and usable
tool.

## Things Still To Do:

* Auto-complete parties

* Add an attribute of a person to indicate that they're not
  standing, so that can be recorded with a source and username.

* Allow search for a candidate based on their name.

* Stub out the PopIt API in tests (or this could be provided in
  the PopIt-Python module so that it's reusable).

* Add documentation for you to make common API queries to the
  PopIt instance to get candidate data back.

* Add basic versioning of the kind suggested above.

* Consider changing the data model in PopIt. At the moment the
  script that sets up the PopIt instance (create-popit.py) and
  the Django project relies on there being two artifical
  "candidate list" organisations (2010 and 2015) for each
  constituency.  A person is made a candidate by making them a
  member of that candidate list organisation.  It would be more
  natural in the Popolo data model to have a post of "MP for
  Ambridge" and multiple people who have memberships associated
  with that post with role "candidate" and start and end dates
  indicating which election that was for.

* Add photo upload once
  https://github.com/mysociety/popit/issues/431 ,
  https://github.com/mysociety/popit/issues/470 and
  https://github.com/mysociety/popit/issues/214 are resolved.

* Reduce the number of requests made to PopIt once
  https://github.com/mysociety/popit/issues/593 (or something
  similar) is done.

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

Run the development server:

    cd yournextmp-popit
    ./manage.py runserver 0.0.0.0:8000

Now you should be able to see the site at:

    http://localhost:8080/

### Restarting the development server after logging out

After logging in again, the only steps you should need to run
the development server again are:

    cd yournextmp-popit
    ./manage.py runserver 0.0.0.0:8000
