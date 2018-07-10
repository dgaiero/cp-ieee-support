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
Protocols and ports|`tcp:689`

#### Firewall Rule 2

Name | Description
---|---
Network|`default`
Priority|`1000`
Direction|`Ingress`
Action on match|`Allow`
Target tags|`ldap`
IP ranges|`0.0.0.0/0`
Protocols and ports|`tcp:389`

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

SITE=cp-ldap

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
