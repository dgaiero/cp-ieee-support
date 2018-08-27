import csv
import datetime
import logging
import re
import sys
import traceback
from copy import deepcopy
from pathlib import Path

import ldap3
import ldif3

logger = logging.getLogger("main." + __name__)


class ProcessUsers:

    def __init__(self, server_uri, search_base, search_filter, bind_user, bind_password, csv_location):
        '''
        Initalize the class with necessary server bind parameters.
        '''
        self.server_uri = server_uri
        self.search_base = search_base
        self.search_filter = search_filter
        self.bind_user = bind_user
        self.bind_password = bind_password
        self.csv_location = csv_location

    def get_users_ldap_server(self):
        '''
        Bind to LDAP server and query for all users in search filter.
        '''
        logger.info(f"Set server URI: {self.server_uri}")
        logger.info(f"Set search base: {self.search_base}")
        users_in_server = []
        server = ldap3.Server(self.server_uri, get_info=ldap3.ALL)
        self.ldap_connection = ldap3.Connection(
            server, self.bind_user, self.bind_password)
        self.ldap_connection.bind()
        logger.info(self.ldap_connection)
        self.ldap_connection.search(
            self.search_base, self.search_filter, attributes=ldap3.ALL_ATTRIBUTES)
        users_in_server = self.ldap_connection.entries
        return users_in_server

    def read_users_csv(self):
        '''
        Reads user from CSV file directly from IEEE.
        '''
        ieeeUser = {
            'objectClass': ['ieeeUser', 'inetOrgPerson', 'organizationalPerson', 'person', 'top'],
            'displayName': [],
            'mail': [],
            'o': ['Cal Poly IEEE Student Branch'],
            'givenName': [],
            'sn': [],
            'uid': [],
            'member': ['cn=activeMembers,dc=calpolyieee,dc=com'],
            'description': [],
            'userPassword': [],
            'mobile': [],
            'ieeeExpiration': [],
            'ieeeMemberNumber': [],
            'cn': [],
            'userStatus': []
        }
        users_in_csv = {}

        with open(Path(self.csv_location), encoding='utf-16') as csvfile:
            readCSV = csv.reader(csvfile, delimiter='\t')
            headers = next(readCSV)
            temp_user_information = {}
            for item in headers:
                temp_user_information[item] = ''

            for row in readCSV:
                for i in range(len(row)):
                    temp_user_information[headers[i]] = row[i]
                user = deepcopy(ieeeUser)
                user['displayName'].append(
                    f"{temp_user_information['Last Name']}, {temp_user_information['First Name']}".upper())
                user['mail'].append(temp_user_information['Email Address'])
                user['givenName'].append(temp_user_information['First Name'])
                user['sn'].append(temp_user_information['Last Name'])
                user['uid'].append(
                    f"{temp_user_information['First Name'][0]}{temp_user_information['Last Name']}".lower())
                user['cn'].append(
                    f"{temp_user_information['First Name']}.{temp_user_information['Last Name']}".lower())
                user['ieeeMemberNumber'].append(int(
                    temp_user_information['Member/Customer Number']))
                if temp_user_information['Renew Year'] == '':
                    temp_user_information['Renew Year'] = 0000
                user['ieeeExpiration'].append(int(
                    temp_user_information['Renew Year']))
                user['userStatus'].append(temp_user_information['IEEE Status'])
                work_number = re.sub(
                    r"\D", "", temp_user_information['Work Number '])
                home_number = re.sub(
                    r"\D", "", temp_user_information['Home Number '])
                user['mobile'] = set_phone_number(work_number, home_number)
                userDN = f"mail={user['mail'][0]},dc=members,dc=calpolyieee,dc=com"
                logger.info(f"CSV USER dn IS {userDN}")
                users_in_csv[userDN] = user
        return users_in_csv

    def compare_users(self, users_in_server, users_in_csv):
        '''
        Cross Reference Users in CSV to LDAP server to see which users need to be added/updated.
        '''
        for user in users_in_server:
            try:
                csv_user_data = users_in_csv[user.entry_dn]
            except KeyError:
                self.set_user_expire(user.entry_dn, int(
                    user.entry_attributes_as_dict['ieeeExpiration'][0]))
                continue
            logger.info(f"FOUND USER {user.entry_dn}")
            server_user_data = user.entry_attributes_as_dict
            for key, value in csv_user_data.items():
                if key != "ieeeExpiration" and \
                   key != "member" and \
                   key != "userStatus":

                    logger.info(f"FOUND KEY {key}")
                    for item in value:
                        try:
                            logger.info(
                                f"{item} IN {server_user_data[key]}")
                        except KeyError:
                            logger.info(f"{item} NOT IN SERVER DATA")
                elif key == "ieeeExpiration":
                    logger.info(f"FOUND KEY {key}")
                    logger.info(f"USER EXPIRATION IS {value[0]}")
                    user_expiration = server_user_data[key][0]
                    actual_expiration = value[0]
                    logger.info(
                        f"USER EXPIRATION {user_expiration} CURRENT YEAR {int(datetime.datetime.now().year)}")
                    if int(actual_expiration) < int(datetime.datetime.now().year):
                        logger.info(f"USER HAS EXPIRED")
                        logger.info("SETTING USER TO INACTIVE")
                        self.set_user_expire(user.entry_dn, actual_expiration)
                    else:
                        self.set_user_active(user.entry_dn, actual_expiration)
            del users_in_csv[user.entry_dn]
        if len(users_in_csv) > 0:
            logger.info(f"USERS FOUND NOT IN QUERY OF {self.search_filter}")
            for dn, _attributes in users_in_csv.items():
                logger.info(f"NEW USER dn IS {dn}")
                if _attributes['userStatus'][0] == 'Active':
                    _attributes['member'] = [
                        'cn=activeMembers,dc=calpolyieee,dc=com']
                elif _attributes['userStatus'][0] == 'Inactive':
                    _attributes['member'] = [
                        'cn=inactiveMembers,dc=calpolyieee,dc=com']
                elif _attributes['userStatus'][0] == 'Arrears':
                    _attributes['member'] = [
                        'cn=arrearsMembers,dc=calpolyieee,dc=com']
                for key, value in _attributes.items():
                    logger.info(f"FOUND ATTRIBUTE {key} EQUALS {value}")
                ldap_user_add_response = self.ldap_connection.add(dn, attributes={'objectClass': ['ieeeUser', 'inetOrgPerson', 'organizationalPerson', 'person', 'top'],
                                                                                  'displayName': _attributes['displayName'],
                                                                                  'cn': _attributes['cn'],
                                                                                  #  'mail': _attributes['mail'],
                                                                                  'o': ['Cal Poly IEEE Student Branch'],
                                                                                  'givenName': _attributes['givenName'],
                                                                                  'sn': _attributes['sn'],
                                                                                  'uid': _attributes['uid'],
                                                                                  'member': _attributes['member'],
                                                                                  })
                logger.info(f"LDAP ADD RESPONSE {ldap_user_add_response}")
                self.ldap_connection.modify(
                    dn, {'mobile': [(ldap3.MODIFY_ADD, _attributes['mobile'])]})
                logger.info(f"COMMAND MODIFY_ADD mobile")
                logger.info(f"RESULT {self.ldap_connection.result}")
                self.ldap_connection.modify(
                    dn, {'ieeeExpiration': [(ldap3.MODIFY_ADD, _attributes['ieeeExpiration'])]})
                logger.info(f"COMMAND MODIFY_ADD ieeeExpiration")
                logger.info(f"RESULT {self.ldap_connection.result}")
                self.ldap_connection.modify(
                    dn, {'ieeeMemberNumber': [(ldap3.MODIFY_ADD, _attributes['ieeeMemberNumber'])]})
                logger.info(f"COMMAND MODIFY_ADD ieeeMemberNumber")
                logger.info(f"RESULT {self.ldap_connection.result}")

    def set_user_expire(self, dn, new_expire_date):
        '''
        Set the user to expire by modifying member attribute.
        '''
        logger.info("PERFORMING WRITE OPERATION ON LDAP SERVER")
        logger.info("COMMAND EXPIRE USER")
        self.ldap_connection.modify(
            dn, {'member': [(ldap3.MODIFY_ADD, ['cn=inactiveMembers,dc=calpolyieee,dc=com'])]})
        logger.info(f"COMMAND MODIFY_ADD cn=inactiveMembers")
        logger.info(f"RESULT {self.ldap_connection.result}")
        self.ldap_connection.modify(
            dn, {'member': [(ldap3.MODIFY_DELETE, ['cn=arrearsMembers,dc=calpolyieee,dc=com'])]})
        logger.info(f"COMMAND MODIFY_DELETE cn=arrearsMembers")
        logger.info(f"RESULT {self.ldap_connection.result}")
        self.ldap_connection.modify(
            dn, {'member': [(ldap3.MODIFY_DELETE, ['cn=activeMembers,dc=calpolyieee,dc=com'])]})
        logger.info(f"COMMAND MODIFY_DELETE cn=activeMembers")
        logger.info(f"RESULT {self.ldap_connection.result}")
        self.ldap_connection.modify(
            dn, {'ieeeExpiration': [(ldap3.MODIFY_REPLACE, [new_expire_date])]})
        logger.info(
            f"COMMAND MODIFY_REPLACE ieeeExpiration {new_expire_date}")
        logger.info(f"RESULT {self.ldap_connection.result}")

    def set_user_active(self, dn, new_expire_date):
        '''
        Set the user to active by modifying member attribute.
        '''
        logger.info("PERFORMING WRITE OPERATION ON LDAP SERVER")
        logger.info("COMMAND ACTIVE USER")
        self.ldap_connection.modify(
            dn, {'member': [(ldap3.MODIFY_ADD, ['cn=activeMembers,dc=calpolyieee,dc=com'])]})
        logger.info(f"COMMAND MODIFY_ADD cn=activeMembers")
        logger.info(f"RESULT {self.ldap_connection.result}")
        self.ldap_connection.modify(dn, {'member': [(
            ldap3.MODIFY_DELETE, ['cn=inactiveMembers,dc=calpolyieee,dc=com'])]})
        logger.info(f"COMMAND MODIFY_DELETE cn=inactiveMembers")
        logger.info(f"RESULT {self.ldap_connection.result}")
        self.ldap_connection.modify(
            dn, {'member': [(ldap3.MODIFY_DELETE, ['cn=arrearsMembers,dc=calpolyieee,dc=com'])]})
        logger.info(f"COMMAND MODIFY_DELETE cn=arrearsMembers")
        logger.info(f"RESULT {self.ldap_connection.result}")
        self.ldap_connection.modify(
            dn, {'ieeeExpiration': [(ldap3.MODIFY_REPLACE, [new_expire_date])]})
        logger.info(
            f"COMMAND MODIFY_REPLACE ieeeExpiration {new_expire_date}")
        logger.info(f"RESULT {self.ldap_connection.result}")

    def set_user_arrears(self, dn, new_expire_date):
        '''
        Set the user to arrears by modifying member attribute.
        '''
        logger.info("PERFORMING WRITE OPERATION ON LDAP SERVER")
        logger.info("COMMAND ARREARS USER")
        self.ldap_connection.modify(
            dn, {'member': [(ldap3.MODIFY_ADD, ['cn=arrearsMembers,dc=calpolyieee,dc=com'])]})
        logger.info(f"COMMAND MODIFY_ADD cn=arrearsMembers")
        logger.info(f"RESULT {self.ldap_connection.result}")
        self.ldap_connection.modify(dn, {'member': [(
            ldap3.MODIFY_DELETE, ['cn=inactiveMembers,dc=calpolyieee,dc=com'])]})
        logger.info(f"COMMAND MODIFY_DELETE cn=inactiveMembers")
        logger.info(f"RESULT {self.ldap_connection.result}")
        self.ldap_connection.modify(
            dn, {'member': [(ldap3.MODIFY_DELETE, ['cn=activeMembers,dc=calpolyieee,dc=com'])]})
        logger.info(f"COMMAND MODIFY_DELETE cn=activeMembers")
        logger.info(f"RESULT {self.ldap_connection.result}")
        self.ldap_connection.modify(
            dn, {'ieeeExpiration': [(ldap3.MODIFY_REPLACE, [new_expire_date])]})
        logger.info(
            f"COMMAND MODIFY_REPLACE ieeeExpiration {new_expire_date}")
        logger.info(f"RESULT {self.ldap_connection.result}")


def set_phone_number(work_number, home_number):
    '''
    Set the phone number for a user. 
    '''
    logger.debug(
        f"SETTING PHONE NUMBER: WORK IS {work_number} HOME IS {home_number}")
    try:
        if len(work_number) <= 11 or len(str(work_number)) >= 10:
            logger.debug(f"SET USER PHONE NUMBER TO {work_number}")
            return [int(work_number)]
    except ValueError:
        pass
    try:
        if len(home_number) <= 11 or len(str(home_number)) >= 10:
            logger.debug(f"SET USER PHONE NUMBER TO {home_number}")
            return [int(home_number)]
    except ValueError:
        pass
    phone = []
    logger.debug(f"SET USER PHONE NUMBER TO {phone}")
    return phone
