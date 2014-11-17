#!/bin/sh

# It seems bizarre to me, but you can't get command-line parameters
# from a mongo shell script, so you have to wrap it in a shell script.
# https://groups.google.com/forum/#!topic/mongodb-user/-pO7Cec6Sjc

if [ -z "$1" ] || [ "$#" != 1 ]
then
    echo "Usage: reset-mongo POPIT-INSTANCE-DB-NAME"
    exit 1
fi

POPIT_INSTANCE_DB_NAME="$1"

mongo <<EOF
    conn = new Mongo();
    db = conn.getDB('$POPIT_INSTANCE_DB_NAME');
    db.organizations.remove({})
    db.posts.remove({})
    db.memberships.remove({})
    db.persons.remove({})
EOF
