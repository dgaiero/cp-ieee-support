To create standalone exe:
`pyinstaller --onefile --add-data "C:\Users\dgaiero\AppData\Local\Programs\Python\Python36\Lib\site-packages\pyfiglet";./pyfiglet member_database_cli.py`
Change location to pyfiglet

To setup on new computer:
1.`cp secret_template.py secret.py`
2. Fill in server parameters.
3. Run secret.py to configure credentials in credential manager.