import csv
import logging
import ldap3
from copy import deepcopy

logger = logging.getLogger('main.'+__name__)


def read_csv(csv_location):
    '''
    This funciton reads a properly formatted csv file and formats it for addition into the LDAP database.
    Format for the CSV file is as follows:
    dn, MODIFY_MODE.attribute, MODIFY_MODE.attribute, etc...
    DN MUST be the first field. All attributes have a (dot) between the insertion mode and the attribute name.
    '''
    with open(csv_location, encoding='utf-8') as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        headers = next(readCSV)
        logger.info(f"HEADERS IS {headers}")
        add_data = []
        for i in range(len(headers)):
            if headers[i] != 'dn':
                headers[i] = headers[i].split(".")
            else:
                headers[i] = ['DN', 'dn']

        for entry in readCSV:
            logger.info(f"NEW ENTRY IS {entry}")
            tmp_data = deepcopy(headers)
            for i in range(len(entry)):
                tmp_data[i].append(entry[i])
            add_data.append(tmp_data)
    return add_data


def add_data_ldap(add_data, server_uri, search_base, search_filter, bind_user, bind_password):
    '''
    This function takes the properly formatted data read by the CSV file and modifys the LDAP database.
    NOTE: Right now, all MODIFY modes are supported, however MODIFY_REPLACE is the only mode that will work.
    '''
    logger.info(f"Set server URI: {server_uri}")
    logger.info(f"Set search base: {search_base}")
    server = ldap3.Server(server_uri, get_info=ldap3.ALL)
    ldap_connection = ldap3.Connection(
        server, bind_user, bind_password)
    ldap_connection.bind()
    logger.info(ldap_connection)
    for i in range(len(add_data)):
        dn = add_data[i][0][2]
        for j in range(1, len(add_data[i])):
            attribute = add_data[i][j][1]
            modify_type = add_data[i][j][0]
            data = add_data[i][j][2]
            if data == '':
                continue
            ldap_connection.modify(dn, {attribute: [(modify_type, data)]})
            logger.info(f"COMMAND {modify_type} {attribute} {data}")
            logger.info(f"RESULT {ldap_connection.result}")