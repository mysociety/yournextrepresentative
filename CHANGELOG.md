# YourNextRepresentative Changelog

## v0.3

* This release is the first which is compatible with Python 3.4
  and Python 3.5 as well as Python 2.7.  Thank-you to @wfdd for
  this significant contribution to the project.

* The following changes are also of note:

    * There is now a search box at the top of each page to look
      for a candidate by name.

    * The project now requires Elasticsearch to be installed to
      support that search.

    * You can now use Javascript-based geolocation to find
      candidates standing in the areas you're located in.

    * The code that submitted page view to Google Analytics (if
      you have set a property ID in conf/general.yml) was
      missing a line; that is now fixed.

    * You can add "Yes / No / Don't know" fields as customizable
      extra fields.

    * You can now mark multiple people as the winner of the
      election for a post. (The number of people who can be
      marked as a winner is configured as the
      `people_elected_per_post` attribute of the Election
      model; if that is -1, then there is no limit.)

## v0.2.1 (2016-01-14)

* This release fixes a bug that would allow a malicious user to
  delete Election objects from the site.

* Since version v0.2 there have also been a number of bugfixes
  and the following notable changes:

    * A simple API endpoint was added to show upcoming elections
      in the UK.

    * A command to mirror a live YNR site using its API was
      added: `candidates_import_from_live_site`.

    * An elections app for the 2016 municipal elections in Costa
      Rica was added.

    * The date of birth field is more liberal in the formats it
      will accept now.

    * Additional fields to be crowd-sourced can now be added in
      the admin interface.

## v0.2 (2015-12-18)

* This version has switched from using PopIt to the
  django-popolo project for storage of the candidate and party
  data.  You can read a blog post about this migration here:
  http://longair.net/blog/2016/02/15/migrating-yournextrepresentative-from-popit-to-django-popolo/

* We supplied the following notes for partners who had deployed
  YourNextRepresentative:

> This email is to warn you that we're planning soon to merge to
> the master branch some changes to YourNextRepresentative that
> will migrate away from using PopIt to store its core data and
> use (somewhat augmented) Django models from django-popolo
> instead.
>
> This work is important in order to (a) make it much easier to
> set up new YNR instances (b) to make development on the project
> quicker and easier (c) greatly reduce problems with bad data
> being introduced (since PopIt didn't have constraints or
> transactions like a relational database) and (d) stop depending
> on a now-deprecated project.
>
> This is a very large change to the codebase, but we've tried to
> make the migration as smooth and automatic as possible.  (One of
> the Django migrations will export all the data from your live
> PopIt instance and import it into the new models.)  The aim was
> to make the site behave identically before and after the
> migration.
>
> Here are some important notes about the upgrade:
>
>  * There is a new TWITTER_USERNAME config option that you should
>    set in conf/general.yml - this is the Twitter username that
>    will be referenced in the Twitter card metadata when people
>    share pages on Twitter.
>
>  * After migrating you should run the
>    candidates_record_new_versions command to make sure that the
>    small changes made to people by the migration are recorded
>    rather than being picked up by the next edit.
>
>  * Previously we said to just use PopIt's API as the API to get
>    data from the site, but obviously that's no longer an option.
>    Instead, we're now using Django REST Framework to provide a
>    read-only API for the site at /api/v0.9/
>
>    [...]
>
>    Any applications still using the PopIt API will continue to
>    work, of course (until we shut PopIt down completely in
>    July 2016) but won't benefit from any new edits.
>
>    The (much more popular) CSV export of site data is unaffected
>    by the migration - it should work the same as before.
>
>  * Some things that could only previously be done by editing
>    PopIt or via its API (e.g. adding alternative names or
>    identifiers) should now be done in the Django admin interface
>    at /admin/ instead.
>
>  * We've added some tests that are specific to particular
>    ELECTION_APP values - this means that there are now tests
>    specifically for the St Paul address lookup and area views,
>    for example.  In order to run all of the tests you'll now
>    need to run "./run-tests" (or "./run-tests --coverage" if you
>    want coverage data to be generated).  Just running
>    "./manage.py test" only runs the core tests (i.e. those that
>    aren't country-specific).
>
>  * If you were using a local_settings.py file to override
>    settings then that should be moved from
>    mysite/local_settings.py to mysite/settings/local_settings.py

## v0.1 (2015-11-01)

* This is the last version of the project that used PopIt as the
  primary storage for data on candidates, parties and their
  candidacies.
