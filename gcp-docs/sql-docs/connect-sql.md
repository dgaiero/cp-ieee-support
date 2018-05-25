# Connecting to the GCP SQL instances using the GCP proxy

1. Download and install the Google Cloud platform from here: [https://cloud.google.com/sdk/](https://cloud.google.com/sdk/)
2. To connect to a GCP instance, you must downlad the GCP SQL proxy (which can be found here: [Right Click to download](https://dl.google.com/cloudsql/cloud_sql_proxy_x64.exe))
    1. Store this excetuable somehwere on your computer that you can reference easily. I would recommend storing it in the root directory of the SDK.
3. To connect to an instance, start the GCP SDK. Complete the initalization process to setup a default project.
    1. If you have already setup a different project, type `gcloud auth login` to login with your google credentials to a specific project. Note, you can also authorize with a service account if your google account is not credentialed to access the project. For help with a service account, please submit an inquiry at: [https://calpolyieee.com/contact-us/](https://calpolyieee.com/contact-us/)
    2. Then, set the project that you would like to work on with `gcloud config set project [PROJECT_NAME]`. This will most likely be `cpieee-prod` or `ieee-member-database`.
4. To proxy into the database, open the Google Cloud Shell SDK command prompt and type `./cloud_sql_proxy -instances=[INSTANCE_NAME]=tcp:PORT (-credential_file=[FILE_NAME])` (Linux). For windows, replace `./cloud_sql_proxy` with `cloud_sql_proxy.exe` (Make sure to enter the path to the proxy if you are not in the current directory.)
    1. The credential file is optional. Use only if you are authenticating with a provided service agent account key.
    2. `INSTANCE NAMES`
        1. cpieee-prod (used for main website located at [https://calpolyieee.com](https://calpolyieee.com): `cpieee-prod-sql-backend`. Command would be: `cloud_sql_proxy.exe -instances=cpieee-prod-sql-backend=tcp:5432`
        2. ieee-member-database (used for member database website located at [https://members.calpolyieee.com](https://members.calpolyieee.com)): `ieee-member-database:us-west1:ieee-member-database`. Command would be: `cloud_sql_proxy.exe -instances=ieee-member-database:us-west1:ieee-member-database=tcp:3306`

The cpieee-prod database is a MySQL database. To access it locally, you can use the mysql commandline or MySQL workbench. To use MySQL workbench, the hostname should be `127.0.0.1` and the port should be `3306`. For username and passwords, visit: [https://console.cloud.google.com/sql/instances/cpieee-prod-sql-backend/users?project=ieee-prod](https://console.cloud.google.com/sql/instances/cpieee-prod-sql-backend/users?project=ieee-prod). If you need an account and your google account is not authorized to access this project, submit an inquiry at: [https://calpolyieee.com/contact-us/](https://calpolyieee.com/contact-us/).

The ieee-member database is a PostgreSQL database. More information coming soon.