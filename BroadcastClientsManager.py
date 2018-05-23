from datetime import datetime

class BroadcastClientsManager():

    def __init__(self, expiration_time):
        self.__expiration_time = expiration_time
        self.__broadcast_clients = {}

    def __cleanClients(self):
        continue_cleaning = True
        while continue_cleaning:
            continue_cleaning = False
            for client_id in self.__broadcast_clients:
                if self.__expired(client_id):
                    del self.__broadcast_clients[client_id]
                    continue_cleaning = True
                    break

    def __expired(self, client_id):
        return (datetime.utcnow() - self.__broadcast_clients[client_id][1]).total_seconds() > self.__expiration_time

    def insertClient(self, client_id, messenger):
        current_time = datetime.utcnow();
        self.__broadcast_clients[client_id] = (messenger, current_time)
        self.__cleanClients()

    def broadcastMessage(self, message):
        for client_id in self.__broadcast_clients:
            if not self.__expired(client_id):
                self.__sendMessage(message, self.__broadcast_clients[client_id][0])
        self.__cleanClients()

    def __sendMessage(self, message, messenger):
        messenger(message)
