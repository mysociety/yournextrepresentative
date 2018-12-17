# Setting up YourNextRepresentative for a new country

## Introduction

This document is a work-in-progress. You'll need to have
experience of developing in Python, and ideally working on
Django projects, for this to make much sense. We're aware that
this should all much simpler to do, and are actively working on
improving that!

## Preliminaries

We've seen that the most important things in creating a
successful new YourNextRepresentative site are:

* Having a clear understanding of the electoral system in the
  country or jurisdiction you're setting up the site for.
* Choosing a realistic set of candidates that you want to
  crowd-source - not being too ambitious!
* Having a core community of moderators who are happy to check
  all the recent changes and follow-up by email with anyone
  making badly sourced edits.

## Components of a YourNextRepresentative site

To broadly introduce the architecture of YourNextRepresentative
(YNR), these are the main bits of software that the site
requires to run:

* [yournextrepresentative](https://github.com/mysociety/yournextrepresentative/) -
  the Django application in this repository, which is the
  web-based front-end for editing candidate data.
* [MapIt](http://mapit.poplus.org/) - MapIt provides an API
  for, among other things, looking up an administrative boundary
  from a longitude / latitude or a postcode. If you want to have
  an address box on the front page of your YNR site, which will
  let users look up the candidates relevant for where they live,
  you will need an instance of MapIt. (You could also use
  [Represent Boundaries](https://github.com/opennorth/represent-boundaries/)
  for this as well.)
* [Varnish](https://www.varnish-cache.org/) - if your site is
  getting enough traffic that performance is poor, we recommend
  using Varnish as a caching reverse proxy in front of
  yournextrepresentative.
* [Memcached](http://memcached.org/) - this is used for caching
  some API results from MapIt.

## Requirements

The next sections of this document go into more detail about
the components of the site and other data that you will need in
order to set up the site.

### MapIt

If candidates in your electoral system are associated with
geographical constituencies, and you wish to have geographic
lookup of candidates so that users can easily find candidates
relevant to them, you will need an instance of MapIt that
contains the boundaries of those constituencies. There are
various options you have here:

* If OpenStreetMap has the administrative boundaries you need,
  they will be in
  [MapIt: Global](http://global.mapit.mysociety.org/).
  (Note that this currently isn't as easy to use as it should be
  in YNR - there are more details here:  https://github.com/mysociety/yournextrepresentative/issues/507)

* If you have access to shapefiles for those boundaries
  (e.g. from an official source like a mapping agency) then you
  have two options:
  * You can
    [set up your own MapIt](http://mapit.poplus.org/docs/self-hosted/)
    and import those boundaries.
  * You can [ask us](mailto:ynr@mysociety.org) to import the
    boundaries into our MapIt instance for boundaries whose
    licensing isn't compatible with OpenStreetMap.

### Create an elections app for the country you're collecting candidates for

You will need to add a new Django application in the `elections`
package. To start with a skeleton application you can copy the
`elections/example` to a new name - `elections/freedonia`, for
example.  You should then set `ELECTION_APP` in your
`general.yml` to the name of that application (not including
`elections.`).

In this new application you will need to do the following:

* Set `SITE_OWNER` and `COPYRIGHT_HOLDER` in the `settings`
  module (and optionally `SITE_OWNER_URL`) - these will be
  displayed on the site to indicate who runs the site
  (`SITE_OWNER`) and who owns the database right of all the
  crowd-sourced data (`COPYRIGHT_HOLDER`).

* Set `MAPIT_BASE_URL` in the settings module
  (e.g. `elections/feedonia/settings.py`) to the URL of the
  MapIt instance you are using

* Override generic templates in your election application; for
  example, usually people want to replace the template for the
  'About' page (which you would do by creating
  `elections/freedonia/templates/candidates/about.html`.

* Optionally add a `urls.py` and `views.py` to override and
  augment and of the generic URLs that you want to customize.

* Optionally you can customize some behaviour (adding extra
  columns to CSV output and decing how post labels are shorted
  for use in slugs) by adding functions in `lib.py` in your
  election application.

#### Setting up Election objects

You will need to log in to the Django admin interface to
create an Election object for each election you want to collect
candidates for.  (You can create a superuser account that can do
this with: `./manage.py createsuperuser`.)

Each election must be associated with one or more AreaType
objects (FIXME: it should be possible to create an election
associated with no area types, but the admin doesn't allow that
at the moment.)  You need to create an AreaType in the Django
admin for each MapIt area type that you'll want to associate
with an election.  The names of these area types are capitalized
three-letter codes, such as (in the UK MapIt, 'WMC' for
Westminster constituencies.)  You can add AreaTypes by going
to:

    /admin/elections/areatype/add/

In each election, we expect that there is an organization that
people are trying to be elected to. This is usually something
like 'Senate' or 'House of Commons'. You will need to create all
such organizations in the Django shell, e.g.:

    $ ./manage.py shell
    Python 2.7.6 (default, Jun 22 2015, 17:58:13)
    [GCC 4.8.2] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    (InteractiveConsole)
    >>> from popolo.models import Organization
    >>> Organization.objects.create(id='senate', name='Senate')
    <Organization: Senate>

Then the elections can be added in the Django admin
interface. To add the election, go to:

    /admin/elections/election/

... on your site, and click "Add election".  There is an
explanation of what the fields on this page mean below:

`Slug`: this is used to refer to the election in URLs, so it's
best to make is short and not contain unusual characters. If you
won't typically support more than one election per year, for
example, you could just make this `2015`.

`For post role` - this is the name of the Post that the
candidates in this election are trying to get elected to
(e.g. 'Member of Parliament')

`Winner membership role` - once the election is over, users in
the 'Result Recorders' group can click on a button that says
"This candidate won!".  If that's used, then a new Membership of
the Post will be created for that candidate with the role given
by this setting.  Usually you should just leave this blank - the
default interpretation of a Membership of a role is that that
person is fulfilling that role. However, in a primary election,
the role that will be created for the winner might be
`Candidate`.

`Candidate membership role` - this is normally just 'Candidate',
unless this is a primary election, in which case you'd use
'Primary Candidate'.  This is used when the code is looking for
Memberships of the Post that represent people standing as a
candidate for that Post.

`Election date` - a Python `datetime.date` object indicating the
day on which votes are cast in the election.

`Name` - This is the name of the election, as it would be
normally described. This shouldn't be prefixed with 'The',
since most of the uses of the election name on the site prefix
it with a 'The' anyway.  For example, this value might be '2015
General Election'

`Current` - This is a boolean value indicating if this election
and candidates from it should be shown on various pages.

`Use for candidate suggestions` - If this is set to True, then on
the page for a Post, the candidates from this election will be
offered as possibile candidates for this election in an "Are
these candidates standing again?" section, so you can quickly
say "Yes, they are" or "No, they aren't".

`Area types` - a list of 3-letter MapIt type codes for the
types of area that these Posts might be associated with.

`Area generation` - the ID of the MapIt generation that the
areas that these Posts might be associated with are from.

`Post id format` - this is a Python format string that is used to
find the ID of the Post in this election for a particular
area. If you include `{area_id}` then that will be replaced by
the area ID.

`Organization id` - This is the ID of the Organization that the
candidates would be serving in if they are elected.  e.g. in
the UK elections this would be "House of Commons"

### Creating Posts in PopIt

YNR uses the Popolo data model, and in particular its concept of
'Posts' to represent the structure of an election.  A 'Post'
will be something like 'Member of Parliament for Cambridge'.  A
Person who is a candidate will then have a Membership of the
Post, with the role 'Candidate' as an attribute of that
Membership.  For example, here are all the posts created for the
elections in Argentina, grouped by election:

  http://investigacion.yoquierosaber.org/posts

If all the Posts that you need to create are associated with
areas in MapIt, it should be possible, once the MapIt instance
is created and at least on `Election` object exists, to create
those posts with the admin command
`candidates_create_areas_and_posts_from_mapit`.  (Otherwise
you'll need to write your own script to create them.)

For example, to set up a post for each consituency in the UK
general election using UK MapIt you might run:

   ./manage.py candidates_create_areas_and_posts_from_mapit \
       http://mapit.mysociety.org WMC '{area_id}'

### Creating parties

The simplest way to create political parties in
YourNextRepresentative is create a
[Popolo JSON file](http://www.popoloproject.com/) where each
party is an Popolo organization.

If you then run, for example:

    ./manage.py candidates_create_parties_from_json parties.json

... the parties will be created in the database and available to
choose for candidates.  Warning: make sure that the `id` field
of each party really does uniquely identify the party or you
won't be able to re-run the script to update the parties.

### Translation and localization

We use [Transifex](https://www.transifex.com/) as the interface
for authoring translations of the site, so that teams of
volunteers can collaborate on creating the translations. If you
want to contribute translations, you should go to:
https://www.transifex.com/mysociety/yournextmp/

(Note that for pages like the "About" page or "Copyright
Assignment" page, which are essentially lots of static text that
will need to be completely different for each site, it's best to
create a new template in your elections application which
overrides the default.)

If you want to take the updated translations from Transifex and
commit them into the codebase, you should follow the
instructions in [docs/transifex.md](transifex.md)

### Programmatically importing candidates

*FIXME: create a new example script for importing candidates
from CSV, or work on
https://github.com/mysociety/yournextrepresentative/issues/587 *

### Deployment

YNR is a fairly standard Django site, so hopefully its
deployment shouldn't be too difficult if you have previous
experience of deploying Django sites.  In the past we have used
Apache / mod_wsgi and nginx / uwsgi for deployment, and other
application servers like gunicorn should work fine.  You'll need
to have memcached installed on the server as well.  We made a
short checklist for Argentina of other things to look out for
when deploying, which you can find here:
https://github.com/mysociety/yournextrepresentative/issues/417

### Further customizations

You will also have to decide if you you want to create "party
sets" or "post groups" for the elections you're supporting.
These are potentially confusing, so here are some quick
descriptions:

#### Party Sets

It's sometimes the case that there are different sets of parties
available for different posts that are up for election.  (For
example, in the UK General Election, there are distinct
registers of parties for constituencies in Northern Ireland and
Great Britain.)

You can add a PartySet in the admin interface at:

    /admin/candidates/partyset/

... and then, mostly likely with a script, you'll need to:

* ... add one or more party sets for each Organization that
  represents a party
* ... make sure the party_set of each PostExtra object is set to
  the correct PartySet.

#### Post Groups

Each post can be in a particular "post group"; these are only
used to group the posts on the party detail page for a
particular election. (For example, in the UK General Election,
it was useful to group posts on that page by whether they were
associated with a constituency in England, Scotland, Northern
Ireland or Wales.)  You can set the post group of a Post by
programmatically setting the 'group' attribute of the
corresponding PostExtra model.
