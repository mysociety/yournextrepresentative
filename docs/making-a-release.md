### Making a new release

If there are significant new features or changed dependencies
that are worth highlighting to reusers, you should create a tag
for a new release. (Note that if there are backwards
incompatible changes to the API, that's more complicated, and
you'll need to look at changing the API version.)

#### Update the changelog

First, edit CHANGELOG.md to add a helpful description of what's
changed since the last release.  You can see the changes between
releases with, for example:

    git log --reverse -p v0.2.1..v0.3

You don't need to describe every change - there's no need to
just repeat what's in the git log - instead pick out anything
that might be significant or interesting to reusers.

#### Create an annotated tag

You can do this with a command like:

    git tag -a v0.3

The message should be brief (more concise than the changelog
entry), e.g.:

```
Version 0.3 of YourNextRepresentative

This tag marks when the source code was usable under
Python 2.7, Python 3.4 and Python 3.5.  (Previously
it couldn't be used with Python 3.)
```
