# Making a new instance of YourNextRepresentative

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
* Giving us early feedback (to <ynr@mysociety.org>) when you
  encounter any problems or bugs - this is still alpha software!

## Components of a YourNextRepresentative site

To broadly introduce the architecture of YourNextRepresentative
(YNR), these are the main bits of software that the site
requires to run:

* [yournextrepresentative](https://github.com/mysociety/yournextrepresentative/) -
  the Django application in this repository, which is the
  web-based front-end for editing candidate data.
* [Memcached](http://memcached.org/) - this is used for caching
  some API results from PopIt and MapIt.
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

## Requirements

The next sections of this document go into more detail about
the components of the site and other data that you will need in
order to set up the site.

### Create a list of political parties in Popolo JSON

YNR has a strong assumption that there is a fixed list of
political parties that candidates may be standing for. (n.b. the
list of parties can be different in different geographical
areas - for this more advanced feature see the description of
"Party Sets" below).

We recommend that you create a
[Popolo JSON file](http://www.popoloproject.com/) with all the
political parties that candidates might stand for. This is used
for the party options shown in drop-down lists in the site's
interface. There is a Django admin command called
`candidates_create_popit_organizations` you can use to create
the corresponding party organizations in PopIt based on this
JSON file. The IDs of the parties in the JSON file should be
stable (ideally some official ID if such exists) so that
re-running this command will update the parties in PopIt without
creating duplicates.

For examples of such Popolo JSON files of political parties, you
can look at those for the UK and Argentina:

* https://github.com/mysociety/yournextrepresentative/blob/master/elections/uk_general_election_2015/data/all-parties-from-popit.json
* https://github.com/mysociety/yournextrepresentative/blob/master/elections/ar_elections_2015/data/all-parties-from-popit.json

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

* Override generic templates in your election application; for
  example, usually people want to replace the template for the
  'About' page (which you would do by creating
  `elections/freedonia/templates/candidates/about.html`.

* Optionally add a `urls.py` and `views.py` to override and
  augment and of the generic URLs that you want to customize.

* Some data and behaviour might need to be customized by adding
  functions or variables in `lib.py` in your election
  application.

#### Setting up Election objects

*FIXME: this part of the setup needs work to make it a lot simpler.*

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

`Candidacy start date` - When someone is added as a candidate, a
Membership of that Post (typically with role 'Candidate') is
created. This is when the start date of that Membership should
be.  It's a bit artificial to make this the same for all
candidates in the election, but in the countries we've used the
code in so far it has been rare to actually know the date when
someone becomes a candidate, and having a `start_date` on these
Memberships makes certain queries that use date ranges work
properly. We normally set this date to the day after the
previous election.

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

`Party membership start date` / `Party membership end date` - These
are similar to `Candidacy start date` in being rather artificial;
these are the start and end dates of party Memberships that are
created when you set the party that a candidate is standing
for.  We usually (artificially) set the `start_date` to the day
after the previous election of the same type and the `end_date`
to `9999-12-31` for current elections.

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

*FIXME: update this section for the django-popolo migration
after writing an equivalent of the post-creating script which
makes Post objects in the database*

YNR uses the Popolo data model, and in particular its concept of
'Posts' to represent the structure of an election.  A 'Post'
will be something like 'Member of Parliament for Cambridge'.  A
Person who is a candidate will then have a Membership of the
Post, with the role 'Candidate' as an attribute of the
Membership.  For example, here are all the posts created for the
elections in Argentina, grouped by election:

  http://investigacion.yoquierosaber.org/posts

If all the Posts that you need to create are associated with
areas in MapIt, it should be possible, once the MapIt instance
is created and the ELECTIONS data structure in
`elections/*/settings.py` has been created, to create those
posts with the admin command `candidates_create_popit_posts`.

### Creating parties

*FIXME: write this section after writing an equivalent of the
organization-creating script which makes Organization objects in
the database*

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

*FIXME: update this import script*

It's frequently the case that some lists of candidates, however
incomplete, may be available, and it can be useful to see your
YNR site with these candidates.

This should be done with a Django management command using the
`PopItPerson` model to make sure that they're created with all
the right data attributes, and an initial version history.  As a
model, you can look at
[this code](https://github.com/mysociety/yournextrepresentative/blob/master/elections/ar_elections_2015/management/commands/ar_elections_2015_import_candidates.py#L170-L215),
for example.

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

To create multiple party sets, you must subclass two
classes. This should be done in `elections/*/lib.py`:

1. Create a class `PartyData`, inheriting from
   `BasePartyData`. In its `__init__` method it should, after
   calling the superclass initializer, set `ALL_PARTY_SETS` to a
   tuple of dicts giving the slug and name of each party set. It
   must also override the `party_data_to_party_sets` method,
   which should take a party data dictionary (essentially the
   Python version of the party's Popolo JSON from
   `all-parties-from-popit.json`) and return a list of slugs of
   the party sets that party is in. Here are examples for the UK
   and Argentina:
   * https://github.com/mysociety/yournextrepresentative/blob/master/elections/uk_general_election_2015/lib.py#L11-L31
   * https://github.com/mysociety/yournextrepresentative/blob/master/elections/ar_elections_2015/lib.py#L87-L102
2. Create a class `AreaPostData` inheriting from
   `BaseAreaPostData` which overrides
   `post_id_to_party_set`. This method should take a post ID and
   return the slug of the party set that should be used for that
   post. Here are examples for the UK and Argentina:
   * https://github.com/mysociety/yournextrepresentative/blob/master/elections/uk_general_election_2015/lib.py#L45-L53
   * https://github.com/mysociety/yournextrepresentative/blob/master/elections/ar_elections_2015/lib.py#L120-L126

Once you've made those updates, you'll also need to generate a
Javascript file with data about the party sets by running the
Django management command
[candidates_make_party_sets_lookup](https://github.com/mysociety/yournextrepresentative/blob/master/candidates/management/commands/candidates_make_party_sets_lookup.py)
and commit the generated `post-to-party-set.js` file.

#### Post Groups

Each post can be in a particular "post group"; these are only
used to group the posts on the party detail page for a
particular election. (For example, in the UK General Election,
it was useful to group posts on that page by whether they were
associated with a constituency in England, Scotland, Northern
Ireland or Wales.)

To create multiple post groups, you must create a class
`AreaPostData`, inheriting from `BaseAreaPostData` and override
these methods:

* `__init__` - after calling the superclass initializer, set
  `self.ALL_POSSIBLE_PARTY_SETS` to a list of the names of all
  post groups. Example:
  * https://github.com/mysociety/yournextrepresentative/blob/master/elections/uk_general_election_2015/lib.py#L36-L40
* `area_to_post_group` - this should take area data (a MapIt
  area data dictionary) and return the name of the post group
  that area is associated with. Example:
  * https://github.com/mysociety/yournextrepresentative/blob/master/elections/uk_general_election_2015/lib.py#L42-L43
* `post_id_to_post_group` should take an election and a post ID
  and return the name of a post group. Example:
  * https://github.com/mysociety/yournextrepresentative/blob/master/elections/uk_general_election_2015/lib.py#L55-L60
