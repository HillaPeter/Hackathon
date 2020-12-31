import socket
import threading
import socket
import random
import struct
from time import sleep
from colorama import Fore,Style
from scapy.arch import get_if_addr

class Server:
    
    MAGIC_COOKIE= 0xfeedbeef
    TYPE = 0x2
    UDP_PORT=13117
    server_port=101
    IP=get_if_addr('eth1')#'172.18.0.101'
    TCP_PORT=237

    def __init__(self,team_name1):
        self.team_name=team_name1
        self.clients =[]
        self.socket_UDP = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket_UDP.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
        self.socket_TCP = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket_TCP.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.socket_TCP.settimeout(0.1)
        self.socket_TCP.bind((self.IP,self.TCP_PORT))
        self.create_server()

    #send message from udp
    def send_message_from_UDP(self):
        print(Style.RESET_ALL+"Server started, listening on IP address",self.IP)
        try:
            for i in range(10):
                self.socket_UDP.sendto(struct.pack('IbH', self.MAGIC_COOKIE, self.TYPE, self.server_port), ('<broadcast>', self.UDP_PORT))
                sleep(1)
        except:
            print("cant connect to UDP")

    #recieve message from tcp
    def get_message_from_TCP(self, count_group_a,count_group_b):
        try:
            for socket_1 in count_group_a:
                while self.is_receive_message:
                    mas = socket_1.recv(1024)
                    count_group_a[socket_1] += 1
                threading.Thread(target=mas, args=(socket_1, count_group_a)).start()

            for socket_2 in count_group_b:
                while self.is_receive_message:
                    mas_2 = socket_2.recv(1024)
                    count_group_b[socket_2] += 1
                threading.Thread(target=mas_2, args=(socket_2, count_group_b)).start()
        except:
            print("can't recive massage")
        sleep(10)

    def to_connect(self):
        try:
            while self.udp_is_sending_message:
                client_socket,client_address = self.socket_TCP.accept()
                client_thread = threading.Thread(target=self.get_name_of_team, args=(client_socket,client_address))
                client_thread.start()
        except:
            print("server time out")

    #get teams name from client
    def get_name_of_team(self,client_socket,client_address):
        try:
            name =client_address.recv(1024).decode('utf-8')
            self.clients.append((client_socket,client_address,name))   
        except:
            print("cant get the team")   

    #message start game
    def start_game(self,group_a,group_b):
        message = Fore.CYAN+"Welcome to Keyboard Spamming Battle Royale.\n"
        message+=+Fore.BLUE+"Group 1:\n"+ "==\n"    
        for a in group_a:
            message = message + a[2]      
        message = message +Fore.MAGENTA+"Group 2:\n"
        message+=Fore.MAGENTA+"==\n"
        for b in group_b:
            message = message + b[2]  
        message = message +Fore.CYAN+"Start pressing keys on your keyboard as fast as you can!!"  
        return message

    #initialize game- choose random groups into 2 clients
    def initialize_game(self):
        group_a=[]
        group_b =[]
        all_clients = list(self.clients)
        for i in range(all_clients/2):
            random_choose = random.randint(0, len(all_clients)-1)
            group_a.append(all_clients.pop(random_choose))

        for client in all_clients:
            group_b.append(all_clients.pop(client))
        
        return group_a, group_b

    #create thread calling to client
    def create_threads(self):
        while self.is_receive_message:
            try:
                socket, address=self.socket_TCP.accept()
                thread_client=threading.Thread(target=self.team_name, args=(socket, address))
                thread_client.start()

            except:
                print(Fore.RED +"Socket timeout")

    #create message for the winner and looser
    def end_game(self, points_a, points_b):
        message= Fore.CYAN+'Game over!\nGroup 1 typed in {} characters. Group 2 typed in {} characters.\n'.format(points_a, points_b)
        if points_a > points_b:
            message += Fore.BLUE+'Group 1 wins!\n\n'
        else:
            message += Fore.MAGENTA+'Group 2 wins!\n\n'
        message += Fore.CYAN+'Congratulations to the winners:\n=='
        message+='\n'
        return message

    #initialize 
    def insert_to_groups(self,group,char):
        #initialize groups points
        group_initialize=self.initialize_game()
        if char=='a':
            print("group_a: {}".format(group_initialize))
        elif char == 'b':
            print("group_b: {}".format(group_initialize))
        return group_initialize

    #create game - main
    def create_game(self):
        #invalid num of players
        if(len(self.clients)!= 2) :
            print(Fore.YELLOW+"There is no two groups of players")
            #remove existing clients
            try:
                for i in self.clients:
                    i[0].shutdown(socket.SHUT_RDWR)
                    i[0].close()
            except:
                print("client is still connected ")
            self.clients=[]
        
        group_a, group_b=self.initialize_game()
        
        group_a_sum=self.insert_to_groups(group_a,'a')
        group_b_sum=self.insert_to_groups(group_b,'b')

        count_group_a = {}      
        for i in group_a_sum:
            count_group_a[i] = 0

        count_group_b = {}      
        for i in group_b_sum:
            count_group_b[i] = 0
        try:
            server_run=threading.Thread(target=self.get_message_from_TCP,args=(count_group_a,count_group_b))
            server_run.start()
        except:
            print("threads not working")


        start_game_message=self.start_game(count_group_a,count_group_b)
        
        #send message to client
        for client in self.clients:
            client.send(bytes(str(start_game_message),"utf-8"))

        server_run.join()

        print()
        print(count_group_a)
        print()
        print(count_group_b)
        print()

        ##end game
        sum_points_a = sum(count_group_a.values())
        sum_points_b = sum(count_group_b.values())
        message=self.end_game(sum_points_a,sum_points_b)

        if sum_points_a > sum_points_b:
            for a in group_a:
                message += a[2] + '\n'
        else:
            for b in group_b:
                message += b[2] + '\n'
        print(message)

        #remove existing clients
        try:
            for i in self.clients:
                i[0].shutdown(socket.SHUT_RDWR)
                i[0].close()
        except:
            print("client is still connected ")
        self.clients=[]



    #inialize server threads
    def create_server(self):
        self.socket_TCP.listen()
        try:
            while True:
                udp_message= threading.Thread(target=self.send_message_from_UDP)
                udp_message.setDaemon(True)
                udp_message.start()
                tcp_message= threading.Thread(target=self.create_threads)
                tcp_message.setDaemon(True)
                tcp_message.start()

                udp_message.join()
                tcp_message.join()
                self.create_game()
        except:
            print(Fore.RED +"There is no server connection")

if __name__ == '__main__':
    Server("NetaHilla")