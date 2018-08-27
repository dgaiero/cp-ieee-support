import logging

import click

import custom_csv
import ldap_processor

logger = logging.getLogger('main')



def process_default_ieee_csv(server_uri, search_base, search_filter, bind_user, bind_password, csv_location):
    logger.info(f'READ ARGUMENT: server_uri WITH VALUE {server_uri}')
    logger.info(f'READ ARGUMENT: search_base WITH VALUE {search_base}')
    logger.info(f'READ ARGUMENT: search_filter WITH VALUE {search_filter}')
    logger.info(f'READ ARGUMENT: bind_user WITH VALUE {bind_user}')
    logger.info(f'READ ARGUMENT: bind_password WITH VALUE {bind_password}')
    logger.info(f'READ ARGUMENT: csv_location WITH VALUE {csv_location}')
    userProcessor = ldap_processor.ProcessUsers(server_uri,
                                 search_base, search_filter, bind_user, bind_password, csv_location)
    users_in_server = userProcessor.get_users_ldap_server()
    users_in_csv = userProcessor.read_users_csv()

    userProcessor.compare_users(users_in_server, users_in_csv)


def process_custom_csv(server_uri, search_base, search_filter, bind_user, bind_password, csv_location):
    logger.info(f'READ ARGUMENT: server_uri WITH VALUE {server_uri}')
    logger.info(f'READ ARGUMENT: search_base WITH VALUE {search_base}')
    logger.info(f'READ ARGUMENT: search_filter WITH VALUE {search_filter}')
    logger.info(f'READ ARGUMENT: bind_user WITH VALUE {bind_user}')
    logger.info(f'READ ARGUMENT: bind_password WITH VALUE {bind_password}')
    logger.info(f'READ ARGUMENT: csv_location WITH VALUE {csv_location}')
    add_data = custom_csv.read_csv(csv_location)
    custom_csv.add_data_ldap(
        add_data, server_uri, search_base, search_filter, bind_user, bind_password)



@click.command()
@click.option('--server_uri', default='ldap://ldap.calpolyieee.com', help='The URI of the IEEE LDAP server')
@click.option('--search_base', default='dc=members,dc=calpolyieee,dc=com', help='The search base for the queries.')
@click.option('--search_filter', default='(objectClass=ieeeUser)', help='The search filter for what users to find.')
@click.argument('bind_user')
@click.argument('bind_password')
@click.option('--run_method', type=click.Choice(['ieee', 'custom']), help='Set to ieee if you have a csv file directly from the IEEE website. Set to custom for adding custom user attributes.')
@click.argument('csv_location', type=click.Path(exists=True))
def main(server_uri, search_base, search_filter, bind_user, bind_password, csv_location, run_method):
    '''
    This script imports specificed user data into the Cal Poly IEEE SB LDAP database.
    There are two scripts that can be run. ieee_process_default and custom_process.

    \b
    The Bind user must be specified with format cn=,dc=,dc=,...
    The CSV location path string must be formatted UNIX style.
    \b
    
    ieee_process_default:
    Use the CSV file directly from IEEE.

    custom_process:
    This funciton reads a properly formatted csv file and formats it for addition into the LDAP database.
    Format for the CSV file is as follows:
    dn, MODIFY_MODE.attribute, MODIFY_MODE.attribute, etc...
    DN MUST be the first field. All attributes have a (dot) between the insertion mode and the attribute name.

    This function takes the properly formatted data read by the CSV file and modifys the LDAP database.
    NOTE: Right now, all MODIFY modes are supported, however MODIFY_REPLACE is the only mode that will work.
    '''


    if run_method == 'custom':
        process_custom_csv(server_uri, search_base, search_filter,
                           bind_user, bind_password, csv_location)
    elif run_method == 'ieee':
        process_default_ieee_csv(
            server_uri, search_base, search_filter, bind_user, bind_password, csv_location)


if __name__ == "__main__":
    logger.setLevel(logging.INFO)

    # create file handler which logs info messages
    fh = logging.FileHandler('ldap_insert.log', 'w', 'utf-8')
    fh.setLevel(logging.INFO)

    # create console handler with a debug log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # creating a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)-8s: %(message)s')

    # setting handler format
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    try:
        main()
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logger.error(f'ERROR IS {e}', exc_info=True)
