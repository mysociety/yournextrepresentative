### Customizing YourNextMP for a new election

(This is a rough description at the moment; making YourNextMP fully
generic is a work-in-progress.)

To use this code to collect informations about candidates in a new
jurisdiction, you should start by adding a new election application
under `elections` - you can use `uk_general_election_2015` as an
example. You should then set `ELECTION_APP` in your `general.yml` to
the name of that application (not including `elections.`).

In that application, you should create a `settings` module which
defines `ELECTIONS`.

If you want to customize behaviour of YourNextMP for this
jurisdiction, then you can do one of the following:

* Override generic templates in your election application.

* Add a urls.py and views.py and override and augment and of the
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

Each post can be in a particular "post group"; these are only used to
group the posts on the party detail page for a particular
election. (For example, in the UK General Election, it was useful to
group posts on that page by whether they were associated with a
constituency in England, Scotland, Northern Ireland or Wales.

FIXME: add details of translating the interface
