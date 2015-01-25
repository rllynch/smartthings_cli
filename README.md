# smartthings_cli
Command line interface to query and control SmartThings devices

# Usage
1. Log into https://graph.api.smartthings.com/ and under My SmartApps, create a new SmartApp with the code in app.groovy.
2. Click App Settings and under OAuth, click _Enable OAuth in Smart App_. Note down the _OAuth Client ID_ and _OAuth Client Secret_. Update the _OAuth Client Display_ to _SmartThings CLI Control_. Click _Update_.
3. Go back to _My SmartApps_ then click on _SmartThings CLI Control_. Click _Publish_ => _For Me_.
4. Clone the smartthings_cli repository, then run the following command, replacing CLIENTID and CLIENTSECRET with the ID and secret from step 2.

   `./smartthings_cli.py --clientid CLIENTID --clientsecret CLIENTSECRET`

5. If you are behind a NAT, open port 8080 and direct it to the computer running smartthings_cli.py (it's only needed for initial authentication then it can be closed).
6. smartthings_cli.py will direct you to a URL to authorized access. Go to that URL in a browser and specify which devices the CLI should be able to access. Click _Authorize_ when finished. You should be redirected to a page reporting _smartthings_cli.py received auth code_. If you get redirected to a broken page (e.g. This webpage is not available) then double check your NAT port forwarding.
7. If you enabled port forwarding on your NAT, you can now disable it.
8. You can now use smartthings_cli.py to query and control devices managed by SmartThings. Examples:
  1. `./smartthings_cli.py query switch all`
  2. `./smartthings_cli.py query switch "Switch Name"`
  3. `./smartthings_cli.py set switch "Switch Name" on`
