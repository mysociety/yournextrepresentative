// Use with "mongo < reset-mongo.js"
// Hard codes the DB name for now

conn = new Mongo();
db = conn.getDB('popitdev_candidates');
db.organizations.remove({})
db.posts.remove({})
db.memberships.remove({})
db.persons.remove({})
