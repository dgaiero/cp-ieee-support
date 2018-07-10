# Setup and Configuration of sldap on cpieee-ldap server

In this guide:

* [Setup and Configuration of sldap on cpieee-ldap server](#setup-and-configuration-of-sldap-on-cpieee-ldap-server)
    * [Assumptions](#assumptions)
    * [Setting up server](#setting-up-server)

## Assumptions

In using this guide, there are several software and server configuration instructions shown below:

* Ubuntu 16.04 LTS
* sldap 2.4.42

## Setting up server

In Google Cloud Platform Console, visit the VM Instances section. Select `CREATE INSTANCE`. Under Instance Type, type the following:
    Identifier | Value
    ---|---
    Name|cpieee-ldap
    Region|us-west1 (Oregon)|us-west1-a
    Machine Type|small (1 shared CPU)
    Boot Disk|Ubuntu 16.04 LTS
    Boot disk type|SSD persistent disk
    Size|10 GB
    Firewall|Allow both
    Networking > Network Tags|ldap,ldaps
    SSH Keys|Add your SSH key

