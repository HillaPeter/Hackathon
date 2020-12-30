import socket
import struct
from colorama import Fore,Style
from datetime import datetime
import getch
from scapy.arch import get_if_addr

class Client:
    MAGIC_COOKIE= 0xfeedbeef
    TYPE = 0x2
    UDP_PORT=13117

    def __init__(self, team_name1,port1, timeout1):
        self.port = port1
        self.timeout= timeout1
        self.team_name=team_name1
        self.create_client()

    #create a connection
    def create_connection(self):
        #connecting toserver via udp protocol
        print(Style.RESET_ALL+"Client started, listening for offer requests...")
        socket_connection_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_connection_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        socket_connection_udp.settimeout(self.timeout) #10 seconds
        socket_connection_udp.bind(('',self.UDP_PORT))
        while True:
            try:
                data, address=socket_connection_udp.recvfrom(1024)
                server_ip=address[0]
                server_port=data[2]
                print(Style.RESET_ALL+'Received offer from {}, attempting to connect...'.format(server_ip))
                #check if we the message is valid
                if server_ip=='172.18.0.101' and self.check_valid_message(data):
                    #sending to socket answer via tcp protocol
                    self.socket_connection_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    print("2",address[1],server_port)
                    self.socket_connection_tcp.connect((server_ip,address[1]))
                    print("3",self.team_name)
                    self.socket_connection_tcp.send(bytes(self.team_name+'\n','utf-8'))
                else:
                    print(Fore.RED +"Server is not working correctly, try again")
            except:
                raise ConnectionRefusedError("There is no server connection")
        

    #check if the message is valid
    def check_valid_message(self,data):
        valid_message=True
        data_structed = struct.unpack('IbH',data)
        if data_structed[0]!=self.MAGIC_COOKIE or data_structed[1]!=self.TYPE or len(data_structed)!=3:
            valid_message=False
        return valid_message

    #gets from the user keyboard input
    def play(self):
        #counter 10 seconds+ send to server the chars
        self.time_now = datetime.now()
        while (datetime.now()-self.time_now).seconds <= self.timeout:
            key=getch.getch()
            self.socket_connection_tcp.send(bytes(str(key),'utf-8'))

    #check if we can start game-if server connected and we are not in "Game Over"
    def start_game(self):
         while True:
             try:
                message_from_server= self.socket_connection_tcp.recv(1024).decode('utf-8')
                print(message_from_server)
                if message_from_server=="Game over, sending out offer requests...":
                    print(Fore.RED +"Server disconnected, listening for offer requests...")
                    break
                else:
                    self.play()
             except:
                raise ConnectionRefusedError(Fore.CYAN +"There is no server connection")

    #close connection
    def close_connection(self):
        try:
            self.socket_connection_tcp.shutdown(socket.SHUT_RDWR)
            self.socket_connection_tcp.close()
        except:
            print(Fore.YELLOW +"Server is still running")

    #create a client + connect to server
    #start playing the game
    #close connection
    def create_client(self):
        try:
            self.create_connection()
            self.start_game()
            self.close_connection()
        except:
            print(Fore.RED +"There is no server connection")
    

if __name__ == '__main__':
    port = 101
    timeout = 10
    team_name="NetaHilla"
    Client(team_name,port,timeout)
