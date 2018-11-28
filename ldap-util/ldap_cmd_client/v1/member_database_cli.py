import msvcrt
import os
import re
import ssl
import secret
import sys
import threading
import time
import traceback
import keyring
from contextlib import redirect_stdout
from getpass import getpass
from io import StringIO

import ldap3
from ansi2html import Ansi2HTMLConverter
from colorama import Back, Fore, Style
from colorama import init as coloramaInit
from pyfiglet import Figlet


class TimeoutExpired(Exception):
    pass

class ldapServer:
    def __init__(self, server_uri, search_base, bind_user, bind_password):
        '''
        Initalize the class with necessary server bind parameters.
        '''
        self.server_uri = server_uri
        self.search_base = search_base
        self.bind_user = bind_user
        self.bind_password = bind_password

    def bind(self):
        print(
            f"{Back.YELLOW}{Fore.BLACK}Connecting to server...{Style.RESET_ALL}", end="\r")
        server = ldap3.Server(self.server_uri, get_info=ldap3.ALL, connect_timeout=4200)
        self.ldap_connection = ldap3.Connection(
            server, self.bind_user, self.bind_password)
        self.ldap_connection.start_tls()
        if not self.ldap_connection.bind():
            return(self.ldap_connection.result)
        
        return True

    def rebind(self, *args, **kwargs):
        return self.ldap_connection.rebind(*args, **kwargs)

    def unbind(self):
        self.ldap_connection.unbind()

    def search(self, search_query):
        self.ldap_connection.search(self.search_base, search_query, attributes=["displayName", "member", "mail", "ieeeMemberNumber"], size_limit=1000)
        users_in_search = self.ldap_connection.entries
        return users_in_search

def clear_screen(status: bool):
    if status:
        os.system('cls' if os.name == 'nt' else 'clear')

class RunMain:
    def reset_query(self):
        self.query_permit = False
        clear_screen(True)
        sys.stdout.write(f"{Back.YELLOW}{Fore.BLACK}For security reasons, you have been logged out. Press ENTER to continue.{Style.RESET_ALL}")

    def cancel_timer(self):
        self.timeout_timer.cancel()

    def main(self):
        self.timeout_timer = threading.Timer(4200.0, self.reset_query)
        coloramaInit()
        clear_screen(True)
        f = Figlet(font='banner3')
        print (f.renderText('CP IEEE'))
        print(Fore.YELLOW + "Cal Poly IEEE Student Branch User Lookup Database (CLI Version)")
        print("---------------------------------------------------------------"+ Style.RESET_ALL)
        print("## LOGIN ##\n")
        user_phone = input("Your Phone Number: ")
        user_phone_validated = re.match(r'^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$', user_phone)
        try:
            user_phone_validated = re.sub("\D", "", user_phone_validated.group(0))
        except AttributeError:
            print(f'{Back.RED}INVALID PHONE NUMBER{Style.RESET_ALL}')
            time.sleep(1)
            self.main()
        user_password = getpass("Your Password: ")
        server_url = secret.DEFAULT_URI
        search_base = secret.SEARCH_BASE
        initialBind = ldapServer(
            server_url, search_base, secret.BIND_USERNAME, secret.BIND_PASSWORD)
        initialBind.bind()
        get_user_data = initialBind.search(f"(mobile={user_phone})")
        if len(get_user_data) == 0 or len(get_user_data) > 1:
            print("Phone number not found")
            time.sleep(2)
            self.main()
        user_login_string = get_user_data[0].entry_dn
        initialBind.unbind()
        self.ldap = ldapServer(server_url, search_base, user_login_string, user_password)
        self.query_permit = True
        self.timeout_timer.start()
        ldapBindResult = self.ldap.bind()
        if ldapBindResult != True:
            print(f"{Back.RED}ERROR{Style.RESET_ALL}")
            print("Description: " + ldapBindResult["description"])
            sys.exit()
        query_parameter = ""
        while(self.query_permit == True):
            sys.stdout.write(Back.MAGENTA + Fore.WHITE + "Input either FIRST name, LAST name, or EMAIL (Type HELP for help message):" + Style.RESET_ALL + " ")
            search_parameter = sys.stdin.readline().strip()
            if self.query_permit == False:
                break
            elif search_parameter.upper() == "HELP":
                print(f"{Fore.YELLOW}SYSTEM HELP{Style.RESET_ALL}")
                print(f"{Back.CYAN}EXIT   : {Style.RESET_ALL} Exit Application")
                print(f"{Back.CYAN}EXPORT : {Style.RESET_ALL} Export Query to HTML file")
                print(f"{Back.CYAN}CLEAR  : {Style.RESET_ALL} Clear Screen")
                print(f"{Back.CYAN}LOGOUT : {Style.RESET_ALL} Logout Current User\n")
            elif search_parameter.upper() == "EXIT":
                raise SystemExit("User exited")
            elif search_parameter.upper() == "CLEAR":
                clear_screen(True)
            elif search_parameter.upper() == "LOGOUT":
                self.ldap.unbind()
                setup()
            elif search_parameter.upper() == "EXPORT":
                print(f"{Back.RED}{Fore.WHITE}KNOWN ISSUE")
                print(
                    f"You may have to run this command twice to generate a proper HTML file. This is a known issue.{Style.RESET_ALL}")
                html = self.export_html(query_parameter)
                sys.stdout.write(Back.MAGENTA + Fore.WHITE + \
                    "Type the path for the output file (with file name). Press enter to accept default. Please note, you must use UNIX style:" + \
                    Style.RESET_ALL + " ")
                file_location = sys.stdin.readline().strip()
                if file_location == "":
                    file = os.path.join(os.getcwd(),"export.html")
                else:
                    file = file_location
                
                print(f"{Back.YELLOW}{Fore.BLACK}The file has been saved at: {file}.{Style.RESET_ALL}")
                fw = open(file, "w")
                fw.write(html)
            else:
                query_parameter = search_parameter
                self.search(search_parameter)
        self.ldap.unbind()
        clear_screen(True)
        self.main()

    def search(self, query):
        search_parameter_fixed = query.replace(
                    ",", "\,")
        search_string = f"(&(objectClass=ieeeUser)(|(givenName={search_parameter_fixed}*)(ieeeMemberNumber={search_parameter_fixed}*)(sn={search_parameter_fixed}*)(mail={search_parameter_fixed}*)))"
        search_result = self.ldap.search(search_string)
        if len(search_result) > 0:
            for user in search_result:
                user_data = user.entry_attributes_as_dict
                if "cn=activeMembers,dc=calpolyieee,dc=com" in user_data['member']:
                    status = Back.GREEN + Fore.BLACK + "ACTIVE" + Style.RESET_ALL
                elif "cn=arrearsMembers,dc=calpolyieee,dc=com" in user_data["member"]:
                    status = Back.RED + "ARREARS" + Style.RESET_ALL
                elif "cn=inactiveMembers,dc=calpolyieee,dc=com" in user_data["member"]:
                    status = Back.RED + "INACTIVE" + Style.RESET_ALL
                else:
                    status = Back.RED + "UNKNOWN"
                first_name = user_data["displayName"][0]
                email_address = user_data["mail"][0]
                member_number = user_data["ieeeMemberNumber"][0]
                print(f"{Back.CYAN}  NAME:{Style.RESET_ALL} {first_name}")
                print(f"{Back.CYAN} EMAIL:{Style.RESET_ALL} {email_address.upper()}")
                print(f"{Back.CYAN}MBR NO:{Style.RESET_ALL} {member_number}")
                print(f"{Back.CYAN}STATUS:{Style.RESET_ALL} {status}")
                print("                " + Style.RESET_ALL)
        else:
            print("NO RESULT FOUND.")
        
    def export_html(self, query):
        f = StringIO()
        cpieee_text = Figlet(font='banner3')
        original = sys.stdout
        sys.stdout = f
        print(cpieee_text.renderText('CP IEEE'))
        print(Fore.YELLOW +
              "Cal Poly IEEE Student Branch User Lookup Database (CLI Version)")
        print(
            "---------------------------------------------------------------" + Style.RESET_ALL)
        print(f"{Back.YELLOW}{Fore.BLACK}Query is: {query}{Style.RESET_ALL}")
        self.search(query)
        sys.stdout = original
        conv = Ansi2HTMLConverter()
        ansi = "".join(f.getvalue())
        html = conv.convert(ansi)
        return html

def setup():
    try:
        print("Loading...")
        newRunner = RunMain()
        newRunner.main()
    except (SystemExit, KeyboardInterrupt) as e:
        print(f'\n{Back.RED}SystemExit or KeyboardInterrupt Raised{Style.RESET_ALL}')
        print(f'{Back.RED}MESSAGE IS{Style.RESET_ALL} {e}')
        print(f'\n{Back.RED}- EXITING -{Style.RESET_ALL}')
        newRunner.cancel_timer()
        time.sleep(2)
    except Exception as e:
        print(f'{Back.RED}ERROR IS{Style.RESET_ALL} {e}')
        print(traceback.format_exc())
        newRunner.cancel_timer()
        time.sleep(2)
    finally:
        exit_prompt = input("Press any key to re-initalize application. Or, type EXIT to exit the application (You may have to do this twice): ")
        if exit_prompt.upper() == "EXIT":
            clear_screen(True)
            raise SystemExit("")
        setup()

if __name__ == "__main__":
    setup()
