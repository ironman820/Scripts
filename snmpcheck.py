import platform    # For getting the operating system name
import subprocess  # For executing a shell command
import sys, getopt # Used for getting command line arguments
from pysnmp import hlapi # SNMP library
import quicksnmp # SNMP function library to make using SNMP easier
from datetime import datetime # Used to get the currnet time for the log
import os # Importing to supress ping statistics while it is running

def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    with open(os.devnull, 'w') as FNULL: # Open null for writing stdout of the ping command
        return subprocess.call(command, stdout=FNULL, stderr=subprocess.STDOUT) == 0

def main(argv):
    pingip = '' # IP we want to ping
    checkip = '' # ePMP IP the snmp command checks
    snmpCommunity = 'public' # default SNMP community
    snmpIndex = '' # Index for the LAN port

    try:
        opts, args = getopt.getopt(argv, "hp:c:",['co=']) # Get the command line arguments
    except getopt.GetoptError:
        '''
        Error handling from getting option, usually none are set
        '''
        print('snmpcheck.py -p pingip -c checkip --co=SNMPCommunity')
        sys.exit(2)

    # print(opts)
    for opt, arg in opts:
        if opt == '-h': # Help print request
            print('snmpcheck.py -p pingip -c checkip --co=SNMPCommunity')
            print('Default SNMP community is RNET41699')
            sys.exit(0)
        elif opt == '-p':
            pingip = arg # The IP we need to ping
        elif opt == '-c':
            checkip = arg # The IP we need to SNMP against
        elif opt == '--co':
            snmpCommunity = arg # The SNMP community

    x = True # Main loop control
    y = True # Flag if the pings have dropped
    pcount = 0 # Bad ping counter
    while x:
        z = ping(pingip) # ping the IP and save if it returned
        if not z: # if it didn't
            print('Dropped a packet')
            pcount += 1 # count the drop
            y = z # record that it dropped
            if snmpIndex == '': # If this is the first drop and we don't have the index of the LAN interface
                links = quicksnmp.get_bulk_auto(checkip, ['1.3.6.1.2.1.2.2.1.2', '1.3.6.1.2.1.2.2.1.8'], hlapi.CommunityData(snmpCommunity), '1.3.6.1.2.1.2.1.0') # Walk the radio interface table
                # print(links)
                for link in links: # Iterate results (should be a list of tupples)
                    for k, v in link.items(): # iterate the tupples
                        if isinstance(v, str) and v[:3] == 'LAN': # If the description starts with LAN (ePMP have WLAN and LAN)
                            oids = k.split('.') # Split the OID listing to get the index
                            snmpIndex = list.pop(oids) # save the index for future runs
                            break # Jump out of the loop
                    if snmpIndex != '': # If we found the index
                        updown = link['1.3.6.1.2.1.2.2.1.8.{}'.format(snmpIndex)] # Get the current link state
                        break # Stop running through the loop of links
            else: # If we already know the index of the interface
                updown = quicksnmp.get(checkip, ['1.3.6.1.2.1.2.2.1.8.{}'.format(snmpIndex)], hlapi.CommunityData(snmpCommunity))['1.3.6.1.2.1.2.2.1.8.{}'.format(snmpIndex)] # Get the link state

            with open('snmplog.txt', 'a') as f: # open the log file for writing and print/log the output
                if updown == 1:
                    print('Link is Up')
                    f.write('{} - Link is UP\n'.format(datetime.now()))
                elif updown == 2:
                    print('Link is down')
                    f.write('{} - Link is DOWN\n'.format(datetime.now()))
                else: # Catch all for various optional states in the MIB
                    print('Link unknown')
                    f.write('{} - Link is UNKNOWN\n'.format(datetime.now()))
        elif not y: # If we pinged, but the last one failed
            if pcount > 9: # if it failed more than 9 times, break the loop to stop the program
                x = False
            else: # otherwise restart the counter and keep going
                pcount = 0
                y = True
            print('Ping is back')

if __name__ == '__main__':
    main(sys.argv[1:])