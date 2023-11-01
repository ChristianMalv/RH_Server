import ssl
import json
from django.http.response import HttpResponse, JsonResponse
from ldap3 import Server, Reader ,ObjectDef,  \
    Connection, \
    SUBTREE, \
    ALL_ATTRIBUTES, \
    Tls, MODIFY_REPLACE

#OBJECT_CLASS = ['top', 'person', 'organizationalPerson', 'user']
LDAP_HOST = '172.16.200.61'
LDAP_USER = 'aprende\{0}'
LDAP_PASSWORD = 'Aprende2022'
LDAP_BASE_DN = 'DC=aprende,DC=mx'
search_filter = "(displayName={0}*)"

ciphers='AES256-GCM-SHA384'
# Establish LDAP connection and initialize connection (conn) object
tls_configuration = Tls(ciphers=ciphers,validate=ssl.CERT_NONE,version=ssl.PROTOCOL_TLS)

#tls_configuration = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1)


def find_ad_users(username):
    try:
        with ldap_connection() as c:
            c.search(search_base=LDAP_BASE_DN,
                    search_filter=search_filter.format(username),
                    search_scope=SUBTREE,
                    attributes=ALL_ATTRIBUTES,
                    get_operational_attributes=True)

        print(json.loads(c.response_to_json()))
        print(c.result)
        print(c.response)
        print(':D')
        return json.loads(c.response_to_json())
    except  Exception as e:
        print(':(')


def get_attributes(user, pwd):
    try:
        with ldap_connection(user, pwd) as c:
            # Firstly find out the DN associated with LDAP group
            #c.search(LDAP_BASE_DN, '(sAMAccountName="cmalvaez")', search_scope=SUBTREE, attributes=['distinguishedName', 'member'])
            #dn_json = json.loads(c.response_to_json())
            #distinguished_name = dn_json["entries"][0]["attributes"]["distinguishedName"]
            #print(distinguished_name)
            # Retrieve data based on DN
            #displayName=Christian Francisco Malvaez Soto
          
            c.search(LDAP_BASE_DN, '(&(sAMAccountName='+ user +'))', 
                            attributes=["givenName", "sn", "mail", "company"])
                   
            user_data = json.loads(c.response_to_json())
            print(':D')      
            for index in range(len(user_data["entries"])):
                print(user_data["entries"][index])
                first_name = user_data["entries"][index]["attributes"]["givenName"]
                surname = user_data["entries"][index]["attributes"]["sn"]
                mail = user_data["entries"][index]["attributes"]["mail"]
                company = user_data["entries"][index]["attributes"]["company"]
                print(':O')
        login_data={"error":False,"nombre": first_name, "apellidos": surname, "company": company}
      
    except Exception as e:
        login_data={"error":True,"exception": e }
        print (':(')
    return login_data    
       

def ldap_connection(usuario, pwd):
    server = ldap_server()
    return Connection(server, LDAP_USER.format(usuario), pwd, auto_bind=True)


def ldap_server():
    return Server(LDAP_HOST, use_ssl=True, tls=tls_configuration)
