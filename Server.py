import socket
import threading
import socket
import random
import struct
from time import sleep
from colorama import Fore, Style
from scapy.arch import get_if_addr


class Server:
    MAGIC_COOKIE = 0xfeedbeef
    TYPE = 0x2
    UDP_PORT = 13117
    server_port = 101

    # IP=get_if_addr('eth1')#'172.18.0.101'
    # TCP_PORT=237

    def __init__(self):
        self.IP = 'localhost'
        self.TCP_PORT = 8081
        self.clients = []
        self.socket_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_TCP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_TCP.settimeout(0.1)
        self.socket_TCP.bind((self.IP, self.TCP_PORT))
        self.create_server()

    # send message from udp
    def send_message_UDP(self):
        print(Style.RESET_ALL + "Server started, listening on IP address {}".format(self.IP))
        try:
            for i in range(10):
                self.socket_UDP.sendto(struct.pack('IbH', self.MAGIC_COOKIE, self.TYPE, self.server_port),
                                       ('<broadcast>', self.UDP_PORT))
                sleep(1)
        except:
            print(Fore.RED +"can not connect to UDP")

    # create thread calling to client
    def create_threads(self):
        try:
            while True:
                socket, address = self.socket_TCP.accept()
                thread_client = threading.Thread(target=self.get_teams_from_client, args=(socket, address))
                thread_client.start()
        except:
            print(Fore.RED + "Socket timeout")

    # get teams from client
    def get_teams_from_client(self, client_socket, client_address):
        try:
            name = client_socket.recv(1024).decode('utf-8')
            self.clients.append((client_socket, client_address, name))
        except:
            print(Fore.YELLOW + "can not get the team name")

    # recieve message from tcp
    def get_message_TCP(self, count_group_a, count_group_b):
        try:
            for socket_1 in count_group_a:
                threading.Thread(target=self.calculate_meassage, args=(socket_1, count_group_a)).start()
            for socket_2 in count_group_b:
                threading.Thread(target=self.calculate_meassage, args=(socket_2, count_group_b)).start()
            sleep(10)
            self.continute_get_message = False

        except:
            print(Fore.RED + "can't receive massage")

    #calculate num of chars on each socket
    def calculate_meassage(self, socket, count):
        while self.continute_get_message:
            try:
                socket.recv(1024)
                count[socket] += 1
            except:
                sleep(1)

    # message start game
    def start_game(self, group_a, group_b):
        message = Fore.CYAN + "Welcome to Keyboard Spamming Battle Royale.\n"
        message += Fore.BLUE + "Group 1:\n"
        message += Fore.BLUE + "==\n"
        for a in group_a:
            message += Fore.BLUE + a[2]
        message += Fore.MAGENTA + "Group 2:\n"
        message += Fore.MAGENTA + "==\n"
        for b in group_b:
            message += Fore.MAGENTA + b[2]
        message += Fore.CYAN + "\nStart pressing keys on your keyboard as fast as you can!!"
        return message

    # initialize game- choose random groups into 2 clients
    def initialize_game(self):
        try:
            group_a = []
            group_b = []
            all_clients = list(self.clients)
            length = len(all_clients)
            indexs_group_for_a = []
            for i in range(0, int(length / 2)):
                random_choose = random.randint(0, len(all_clients) - 1)
                indexs_group_for_a.append(random_choose)

            for i in range(0, length):
                if i in indexs_group_for_a:
                    group_a.append(all_clients[i])
                else:
                    group_b.append(all_clients[i])

            return group_a, group_b
        except:
            print(Fore.BLUE + "there is no enough groups!")

    # create message for the winner and looser
    def end_game(self, points_a, points_b):
        message = Fore.CYAN + 'Game over!\n'
        message += Fore.BLUE + 'Group 1 typed in {} characters.'.format(points_a)
        message += Fore.MAGENTA + ' Group 2 typed in {} characters.\n'.format(points_b)
        if points_a > points_b:
            message += Fore.BLUE + 'Group 1 wins!\n\n'
        else:
            message += Fore.MAGENTA + 'Group 2 wins!\n\n'
        message += Fore.CYAN + 'Congratulations to the winners:\n=='
        message += '\n'
        return message

    # create game - main
    def create_game(self):
        # invalid num of players
        # print(Fore.LIGHTBLUE_EX + "clients in here: {}".format(len(self.clients)))
        # if len(self.clients) < 2:
        #     print(Fore.YELLOW + "There is no two groups of players")
        if len(self.clients) >= 2:
            group_a, group_b = self.initialize_game()
            group_a_names = []
            group_b_names = []
            for i in group_a:
                group_a_names.append(i[2])
            for i in group_b:
                group_b_names.append(i[2])

            count_group_a = {}
            count_group_b = {}
            for i in range(0, len(group_a)):
                client_socket = group_a[i][0]
                count_group_a[client_socket] = 0

            for i in range(0, len(group_b)):
                client_socket = group_b[i][0]
                count_group_b[client_socket] = 0

            try:
                self.continute_get_message = True
                server_run = threading.Thread(target=self.get_message_TCP, args=(count_group_a, count_group_b))
                server_run.start()
                start_game_message = self.start_game(group_a, group_b)

                all_clients=self.clients.copy()
                # send message to client
                for client in all_clients:
                    client[0].send(bytes(start_game_message, 'utf-8'))

                server_run.join()

                ##end game
                sum_points_a = sum(count_group_a.values())
                sum_points_b = sum(count_group_b.values())
                message = self.end_game(sum_points_a, sum_points_b)

                if sum_points_a > sum_points_b:
                    for a in group_a_names:
                        message += a + '\n'
                else:
                    for b in group_b_names:
                        message += b + '\n'

                # send message to client
                for client in self.clients:
                    print(client[0])
                    client[0].send(bytes(message, 'utf-8'))
                # remove existing clients and finish game
                try:
                    print(Fore.WHITE + "Game over, sending out offer requests...")
                    for i in self.clients:
                        i[0].shutdown(socket.SHUT_RDWR)
                        i[0].close()
                except:
                    print("client is still connected ")
                self.clients = []

            except:
                print(Fore.RED + "threads not working")

    # inialize server threads
    def create_server(self):
        self.socket_TCP.listen()
        try:
            while True:
                sleep(3)
                udp_message = threading.Thread(target=self.send_message_UDP)
                udp_message.setDaemon(True)
                udp_message.start()
                tcp_message = threading.Thread(target=self.create_threads)
                tcp_message.setDaemon(True)
                tcp_message.start()

                udp_message.join()
                tcp_message.join()
                self.create_game()
        except:
            print(Fore.RED + "There is no server connection")


if __name__ == '__main__':
    Server()
