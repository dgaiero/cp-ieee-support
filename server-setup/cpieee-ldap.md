# Setup and Configuration of sldap on cpieee-ldap server

In this guide:

* [Setup and Configuration of sldap on cpieee-ldap server](#setup-and-configuration-of-sldap-on-cpieee-ldap-server)
    * [Assumptions](#assumptions)
    * [Setting up server](#setting-up-server)
        * [Configuring Network settings](#configuring-network-settings)
            * [Firewall Rule 1](#firewall-rule-1)
            * [Firewall Rule 2](#firewall-rule-2)
    * [Configuring sldap](#configuring-sldap)
        * [Install and configure LDAP Server](#install-and-configure-ldap-server)
        * [Secure LDAP server](#secure-ldap-server)
            * [Copying the Let's Encrypt Certificates](#copying-the-lets-encrypt-certificates)
            * [Updating the Certbot Renewal Cron Job](#updating-the-certbot-renewal-cron-job)
            * [Configuring slapd to Offer Secure Connections](#configuring-slapd-to-offer-secure-connections)
    * [Configuring custom IEEE Attributes and Object Classes](#configuring-custom-ieee-attributes-and-object-classes)
    * [Credits](#credits)

## Assumptions

In using this guide, there are several software and server configuration instructions shown below:

* Ubuntu 16.04 LTS
* sldap 2.4.42

## Setting up server

In Google Cloud Platform Console, visit the VM Instances section. Select `CREATE INSTANCE`. Under Instance Type, type the following:

Name|Description
---|---
Name|`cpieee-ldap`
Region|`us-west1 (Oregon)\|us-west1-a`
Machine Type|`small (1 shared CPU)`
Boot Disk|`Ubuntu 16.04 LTS`
Boot disk type|`SSD persistent disk`
Size|`10 GB`
Firewall|`Allow both`
Networking \> Network Tags|`ldap`,`ldaps`
SSH Keys|Add your SSH key

### Configuring Network settings

In Google Cloud Platform Console, visit VPC network > External IP addresses. Change the IP for the `cpieee-ldap` server to `static` from `Ephemeral`.

Then, select `Firewall Rules`. Create two firewall rules:

#### Firewall Rule 1

Name | Description
---|---
Network|`default`
Priority|`1000`
Direction|`Ingress`
Action on match|`Allow`
Target tags|`ldaps`
IP ranges|`0.0.0.0/0`
Protocols and ports|`tcp:636, udp:636`

#### Firewall Rule 2

Name | Description
---|---
Network|`default`
Priority|`1000`
Direction|`Ingress`
Action on match|`Allow`
Target tags|`ldap`
IP ranges|`0.0.0.0/0`
Protocols and ports|`tcp:389, udp:389`

## Configuring sldap

These instructions are adapted from: [digital ocean](https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-openldap-and-phpldapadmin-on-ubuntu-16-04)

### Install and configure LDAP Server

```bash
> sudo apt-get update
> sudo apt-get install slapd ldap-utils
```

When configuring sldap, you will be asked to select and confirm an administrator password for LDAP. You can enter anything here, because you'll have the opportunity to update it in just a moment.

```bash
> sudo dpkg-reconfigure slapd
```

During the configuration, follow the following configuration steps:

Name|Value
---|---
Omit OpenLDAP server configuration|No
DNS Domain Name|calpolyieee.com
Organization Name|Cal Poly IEEE Student Branch
Administrator password?|Enter ldap password given to you
Database backend|MDB
Remove the database when slapd is purged|No
Move old database|Yes
Allow LDAPv2 protocol|No

At this point, your LDAP server is configured and running. Open up the LDAP port on your firewall so external clients can connect:

```bash
> sudo ufw allow ldap
```

### Secure LDAP server

Although we've encrypted our web interface, external LDAP clients are still connecting to the server and passing information around in plain text. Let's use our Let's Encrypt SSL certificates to add encryption to our LDAP server.

First, add the repository:

```bash
> sudo add-apt-repository ppa:certbot/certbot
```

You'll need to press ENTER to accept. Afterwards, update the package list to pick up the new repository's package information:

```bash
> sudo apt-get update
```

And finally, install Certbot from the new repository with apt-get:

```bash
> sudo apt-get install python-certbot-apache
```

The certbot Let's Encrypt client is now ready to use.

#### Copying the Let's Encrypt Certificates

Because the `slapd` daemon runs as the user _openldap_, and Let's Encrypt certificates can only be read by the root user, we'll need make a few adjustments to allow `slapd` access to the certificates. We'll create a short script that will copy the certificates to `/etc/ssl/`, the standard system directory for SSL certificates and keys. The reason we're making a script to do this, instead of just entering the commands manually, is that we'll need to repeat this process automatically whenever the Let's Encrypt certificates are renewed. We'll update the `certbot` cron job later to enable this.

```bash
> sudo vim /usr/local/bin/renew.sh
```

Edit the `renew.sh` file:

```bash
#!/bin/sh

SITE=ldap.calpolyieee.com

# move to the correct let's encrypt directory
cd /etc/letsencrypt/live/$SITE

# copy the files
cp cert.pem /etc/ssl/certs/$SITE.cert.pem
cp fullchain.pem /etc/ssl/certs/$SITE.fullchain.pem
cp privkey.pem /etc/ssl/private/$SITE.privkey.pem

# adjust permissions of the private key
chown :ssl-cert /etc/ssl/private/$SITE.privkey.pem
chmod 640 /etc/ssl/private/$SITE.privkey.pem

# restart slapd to load new certificates
systemctl restart slapd
```

Save and close the file, then make it executable:

```bash
> sudo chmod u+x /usr/local/bin/renew.sh
```

Then run the script with `sudo`:

```bash
> sudo /usr/local/bin/renew.sh
```

Verify that the script worked by listing out the new files in `/etc/ssl`:

```bash
> sudo su -c 'ls -al /etc/ssl/{certs,private}/ldap.calpolyieee.com*'
```

The `sudo` command above is a little different than normal. The `su -c '. . .'` portion wraps the whole `ls` command in a **root** shell before executing it. If we didn't do this, the `*` wildcard filename expansion would run with your non-sudo user's permissions, and it would fail because `/etc/ssl/private` is not readable by your user.

ls will print details about the three files. Verify that the ownership and permissions look correct:

```bash
Output
-rw-r--r-- 1 root root     1793 May 31 13:58 /etc/ssl/certs/ldap.calpolyieee.com.cert.pem
-rw-r--r-- 1 root root     3440 May 31 13:58 /etc/ssl/certs/ldap.calpolyieee.com.fullchain.pem
-rw-r----- 1 root ssl-cert 1704 May 31 13:58 /etc/ssl/private/ldap.calpolyieee.com.privkey.pem
```

Next we'll automate this with `certbot`.

#### Updating the Certbot Renewal Cron Job

We need to update our certbot cron job to run this script whenever the certificates are updated:

```bash
> sudo crontab -e
```

You should already have a `certbot renew` line. Add the highlighted portion below:

```bash
15 3 * * * /usr/bin/certbot renew --quiet --renew-hook /usr/local/bin/renew.sh
```

Save and close the crontab. Now, whenever `certbot` renews the certificates, our script will be run to copy the files, adjust permissions, and restart the `slapd` server.

#### Configuring slapd to Offer Secure Connections

We need to add the **openldap** user to the **ssl-cert** group so `slapd` can read the private key:

```bash
> sudo usermod -aG ssl-cert openldap
```

Restart slapd so it picks up the new group:

```bash
> sudo systemctl restart slapd
```

Finally, we need to configure `slapd` to actually use these certificates and keys. To do this we put all of our config changes in an *LDIF* file — which stands for LDAP data interchange format — and then load the changes into our LDAP server with the `ldapmodify` command.

Open up a new LDIF file:

```bash
> cd ~
> vim ssl.ldif
```

This will open a blank file. Paste the following into the file:

```bash
ssl.ldif
dn: cn=config
changetype: modify
add: olcTLSCACertificateFile
olcTLSCACertificateFile: /etc/ssl/certs/ldap.calpolyieee.com.fullchain.pem
-
add: olcTLSCertificateFile
olcTLSCertificateFile: /etc/ssl/certs/ldap.calpolyieee.com.cert.pem
-
add: olcTLSCertificateKeyFile
olcTLSCertificateKeyFile: /etc/ssl/private/ldap.calpolyieee.com.privkey.pem
```

Save and close the file, then apply the changes with ldapmodify:

```bash
> sudo ldapmodify -H ldapi:// -Y EXTERNAL -f ssl.ldif
```

```bash
Output
SASL/EXTERNAL authentication started
SASL username: gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth
SASL SSF: 0
modifying entry "cn=config"
```

We don't need to reload `slapd` to load the new certificates, this happened automatically when we updated the config with `ldapmodify`. Run the `ldapwhoami` command one more time, to verify. This time we need to use the proper hostname and add the `-ZZ` option to force a secure connection:

```bash
> ldapwhoami -H ldap://ldap.calpolyieee.com -x -ZZ
```

We need the full hostname when using a secure connection because the client will check to make sure that the hostname matches the hostname on the certificate. This prevents man-in-the-middle attacks where an attacker could intercept your connection and impersonate your server.

The `ldapwhoami` command should return `anonymous`, with no errors. We've successfully encrypted our LDAP connection.

## Configuring custom IEEE Attributes and Object Classes

Our IEEE Student branch requires a custom structural object and three custom attributes:

* ieeeMemberNumber
* ieeeGroups
* ieeeExpiration

A breif outline of the ieeeUser structural object is shown below (with default values):

```text
objectDataFor        : IEEE User Data

Alias                : ieeeUser
OID                  : 1.3.6.1.4.1.52310.108100097112.1
Description          : IEEE Member Data Object Container for general IEEE User Information
Superior Classes     : top - (2.5.6.0)
Class type           : Structural
Mandatory Attributes : 
    cn, commonName                - (2.5.4.3)                           = LFirst
    displayName                   - (2.16.840.1.113730.3.1.241)         = Last, First M.
    mobile, mobileTelephoneNumber - (0.9.2342.19200300.100.1.41)
    o, organizationName           - (2.5.4.10)                          = Cal Poly IEEE Student Branch
    uid, userid                   - (0.9.2342.19200300.100.1.1)
    sn, surname                   - (2.5.4.4)                           = Last Name
    ieeeMemberNumber              - (1.3.6.1.4.1.52310.108100097112.2)  = 8 Digits
    mail, rfc822Mailbox           - (0.9.2342.19200300.100.1.3)
    ieeeGroups                    - (1.3.6.1.4.1.52310.108100097112.4)  = MinOne(member,officer,admin,service)
    ieeeExpiration                - (1.3.6.1.4.1.52310.108100097112.3)  = YYYY
Optional attributes  :
    description                   - (2.5.4.13)                          = Officer Position
    userPassword                  - (2.5.4.35)
```

The following is the `ieee_user_object.schema`:

```text
attributetype ( 1.3.6.1.4.1.52310.108100097112.2 NAME 'ieeeMemberNumber'
    SYNTAX 1.3.6.1.4.1.1466.115.121.1.27{8}
    USAGE userApplications )
attributetype ( 1.3.6.1.4.1.52310.108100097112.3 NAME 'ieeeExpiration'
    SYNTAX 1.3.6.1.4.1.1466.115.121.1.27{4}
    USAGE userApplications )
attributetype ( 1.3.6.1.4.1.52310.108100097112.4 NAME 'ieeeGroups'
    SYNTAX 1.3.6.1.4.1.1466.115.121.1.26
    USAGE userApplications )
objectclass ( 1.3.6.1.4.1.52310.108100097112.1 NAME 'ieeeUser'
    DESC 'IEEE Member Data Object Container for general IEEE User Information'
    SUP inetOrgPerson
    STRUCTURAL
    MUST ( cn $ displayName $ ieeeExpiration $ ieeeGroups $ ieeeMemberNumber $ mail $ mobile $ o $ sn $ uid )
    MAY ( description $ userPassword ) )
```

Create this file in `/etc/ldap/schema/ieee_user_object.schema`.

```bash
> vim /etc/ldap/schema/ieee_user_object.schema
```

Then, insert the text with your preferred method.

The following guide assumes that you are in the `/etc/ldap/ieee` directory.

Before starting, make and change to the directory to store the custom IEEE schema configuration files:

```bash
> sudo -s & mkdir /etc/ldap/ieee && cd $_
```

Next, we will create a conversion file:

```bash
> cat > ./schema_conv.conf << EOL
include /etc/ldap/schema/ieee_user_object.schema
EOL
```

Convert the schema files to LDIF:

```bash
> mkdir /tmp/ldif
> slaptest -f ./schema_conv.conf -F /tmp/ldif
```

Open `/tmp/ldif/cn\=config/cn\=schema/cn\=\{5\}ieee_user_object.ldif` file and change the following lines:

```bash
dn: cn={5}ieee_user_object
objectClass: olcSchemaConfig
cn: {5}ieee_user_object
```
to

```bash
dn: cn=ieee_user_object,cn=schema,cn=config
objectClass: olcSchemaConfig
cn: ieee_user_object
```

Also, dekete these lines at the bottom:

```bash
structuralObjectClass: olcSchemaConfig
entryUUID: d53d1a8c-4261-1034-9085-738a9b3f3783
creatorsName: cn=config
createTimestamp: 20150206153742Z
entryCSN: 20150206153742.072733Z#000000#000#000000
modifiersName: cn=config
modifyTimestamp: 20150206153742Z
```

Copy the files to `/etc/ldap/schema` and insert the new schema to the LDAP tree:

```bash
> cp ldif/cn\=config/cn\=schema/cn\=\{5\}ieee_user_object.ldif etc/ldap/ieee_user_object.ldif
> ldapadd -Q -Y EXTERNAL -H ldapi:/// -f /etc/ldap/schema/ieee_user_object.ldif
```

Verify:

```bash
> ls -1 /etc/ldap/slapd.d/cn\=config/cn\=schema

cn={0}core.ldif
cn={1}cosine.ldif
cn={2}nis.ldif
cn={3}inetorgperson.ldif
cn={4}ieee_user_object.ldif
```

The server is now configured.


## Credits

This guide could not be written without the support of the following articles:

* https://www.lisenet.com/2015/convert-openldap-schema-to-ldif/
* https://www.digitalocean.com/community/tutorials/how-to-secure-apache-with-let-s-encrypt-on-ubuntu-16-04
* https://www.digitalocean.com/community/tutorials/how-to-encrypt-openldap-connections-using-starttls
* https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-openldap-and-phpldapadmin-on-ubuntu-16-04
