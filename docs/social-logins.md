# Creating social logins for YourNextRepresentative

YourNextRepresentative supports conventional login (with a email
confirmation) and social login with Facebook, Twitter and
Google.

In order to make the social logins work, you need to generate
IDs and keys for each of those plaforms.  This is a brief guide
to how to do that.  Please bear in mind that all of these social
login providers change the UI of their developer dashboards all
the time, so if you find that this is out of date, please submit
a pull request to update it.

The sections below explain how to get the client ID and secret
for each of these social networks.  You should them enter them
when adding a new Social Application in the admin
interface. (When adding a new Social Application, make sure you
select and add the site as well as entering the other details.)

## Twitter

* Go to https://dev.twitter.com/apps and login
* Click "Create New App"
* Fill in the fields; "Website" and "Callback URL" should both
  be the base URL of your site, e.g. https://edit.yournextmp.com
* Click the checkbox to agree to the Developer Agreement and
  submit the form
* Under the "Settings" tab, make sure the "Allow this application
  to be used to Sign in with Twitter" is checked
* Under the "Permissions" tab, make sure that the application is
  only requesting "Read only" access
* You can then find the API Key and API Secret on the "Keys and
  Access Tokens" page

## Facebook

* Go to https://developers.facebook.com/apps
* Click on "Add a New App"
* Select "Website" as the platform
* Enter a name for the app (e.g. "YourNextMP")
* Click "Create New Facebook App ID"
* Leave "Is this a test version [...]?" set to "No"
* Choose a category (we usually pick "Education" for YNR sites)
* Click "Create App ID"
* Scroll down to "Tell us about your website" and enter the base
  URL of the site as "Site URL" and click "Next"
* Then re-enter https://developers.facebook.com/apps in the URL
  bar
* Click on the app you just created
* Select the "Settings" tab from the bar on the left
* Enter the bare domain of your website in "App Domains"
* Add a contact email address in "Contact Email"
* (Site URL should already be filled in.)
* Click on "Save Changes"
* Select the "Status & Review" tab in the bar on the left
* Change the "Do you want to make this app and all its live
  features available to the general public?" option to "Yes" and
  confirm that
* Select the "Dashboard" tab - you can find the the "App ID" and
  "App Secret" fields there

## Google

* Go to https://console.developers.google.com
* In the project drop-down, select "Create a project..."
* Enter a project name, e.g. "YourNextMP"
* Click "Create"
* It'll take a while to create, but progress is shown in the
  "Activities" windown in the bottom right
* Click on "Credentials" in the left sidebar
* Select "New credentials" > "OAuth Client ID"
* That will prompt you to "Configure consent screen" so do that
* Enter the product name
* Enter the homepage URL
* Click save and you'll go back to the "Create client ID"
  options
* Select "Web application"
* Enter a name, e.g. "YourNextMP login"
* As "Authorized JavaScript origins" add the base URL of your
  site, e.g. https://edit.yournextmp.com
* As "Authorized Redirect URIs" enter the base URL followed by
  `/accounts/google/login/callback/`, e.g.
  https://edit.yournextmp.com/accounts/google/login/callback/
* Click "Create"
* Your client ID and client secret will be displayed
