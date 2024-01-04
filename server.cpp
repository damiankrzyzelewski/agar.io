#include <iostream>
#include <thread>
#include <vector>
#include <cstring>
#include <string>
#include <cstdlib>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

std::vector<std::string> pos = {"0:20,20", "1:400,20", "2:20,400"};
std::string currentId = "0";

void threaded_client(int client_socket) {
    char buffer[2048];
    send(client_socket, currentId.c_str(), currentId.size(), 0);

    currentId = std::to_string(std::stoi(currentId) + 1);

    // Send initial positions after sending client ID
    std::string initialPositions = pos[0] + "|" + pos[1] + "|" + pos[2];
    send(client_socket, initialPositions.c_str(), initialPositions.size(), 0);

    std::string reply;

    while (true) {
        memset(buffer, 0, sizeof(buffer));
        int bytes_received = recv(client_socket, buffer, sizeof(buffer), 0);

        if (bytes_received <= 0) {
            send(client_socket, "Goodbye", sizeof("Goodbye"), 0);
            break;
        } else {
            std::cout << "Received: " << buffer << std::endl;

            std::string data = buffer;
            std::string player_data;
            size_t pos_separator = data.find("|");

            for (int i = 0; i < 3; ++i) {
                player_data = data.substr(0, pos_separator);
                data = data.substr(pos_separator + 1);

                // Extract player ID and position
                size_t id_separator = player_data.find(":");
                int player_id = std::stoi(player_data.substr(0, id_separator));
                std::string player_position = player_data.substr(id_separator + 1);

                // Update the position for the corresponding player ID
                pos[player_id] = std::to_string(player_id) + ":" + player_position;
            }

            // Construct the reply with the positions of all players
            reply = pos[0] + "|" + pos[1] + "|" + pos[2];
            std::cout << "Sending: " << reply << std::endl;
        }

        send(client_socket, reply.c_str(), reply.size(), 0);
    }

    std::cout << "Connection Closed" << std::endl;
    close(client_socket);
}


int main() {
    int server_socket = socket(AF_INET, SOCK_STREAM, 0);

    sockaddr_in server_address, client_address;
    server_address.sin_family = AF_INET;
    server_address.sin_port = htons(5555);
    server_address.sin_addr.s_addr = INADDR_ANY;

    bind(server_socket, (struct sockaddr*)&server_address, sizeof(server_address));
    listen(server_socket, 2);
    std::cout << "Waiting for a connection" << std::endl;

    while (true) {
        socklen_t client_size = sizeof(client_address);
        int client_socket = accept(server_socket, (struct sockaddr*)&client_address, &client_size);

        std::cout << "Connected to: " << inet_ntoa(client_address.sin_addr) << std::endl;

        std::thread client_thread(threaded_client, client_socket);
        client_thread.detach();  // Allow the thread to run independently
    }

    close(server_socket);

    return 0;
}
