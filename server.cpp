#include <iostream>
#include <thread>
#include <vector>
#include <cstring>
#include <string>
#include <cstdlib>
#include <cmath>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <mutex>
#include <memory>
#include <chrono>

struct Ball {
    int x;
    int y;
};
int clients;
class Game {
public:
    std::mutex mutex; 
    std::vector<std::string> playerInfo;
    std::vector<Ball> smallBalls;

    Game() : playerInfo{"0:20,20,10", "1:400,20,10", "2:20,400,10"} {
        initializeSmallBalls(20, 800, 600);

        std::thread generatorThread(&Game::generateSmallBallsThread, this);
        generatorThread.detach();
    }
    

    std::string generateSmallBallsInfo() {
        std::lock_guard<std::mutex> lock(mutex); 
        std::string smallBallsInfo;
        if (smallBalls.empty()) {
            Ball ball;
            ball.x = rand() % 800;
            ball.y = rand() % 600;
            smallBalls.push_back(ball);
        }
            
        for (size_t i = 0; i < smallBalls.size(); ++i) {
            smallBallsInfo += std::to_string(smallBalls[i].x) + "," + std::to_string(smallBalls[i].y);
            if (i < smallBalls.size() - 1) {
                smallBallsInfo += "|";
            }
        }
        return smallBallsInfo;
    }

    void initializeSmallBalls(int numBalls, int boardWidth, int boardHeight) {
        std::lock_guard<std::mutex> lock(mutex); 
        for (int i = 0; i < numBalls; ++i) {
            Ball ball;
            ball.x = rand() % boardWidth;
            ball.y = rand() % boardHeight;
            smallBalls.push_back(ball);
        }
    }

    void handleCollision(int playerId, int playerX, int playerY, int playerRadius) {
        std::lock_guard<std::mutex> lock(mutex);  
        for (size_t i = 0; i < smallBalls.size(); ++i) {
            int distance = std::sqrt(std::pow(playerX + playerRadius - smallBalls[i].x, 2) +
                                     std::pow(playerY + playerRadius - smallBalls[i].y, 2));
            if (distance < playerRadius) {
                playerRadius += 2;
                smallBalls.erase(smallBalls.begin() + i);
                playerInfo[playerId] = std::to_string(playerId) + ":" + std::to_string(playerX) + "," +
                                       std::to_string(playerY) + "," + std::to_string(playerRadius);
                break;
            }
        }
    }

    void generateSmallBalls() {
        std::lock_guard<std::mutex> lock(mutex);
        Ball ball;
        ball.x = rand() % 800;
        ball.y = rand() % 600;
        smallBalls.push_back(ball);
    }

    void generateSmallBallsThread() {
        while (true) {
            generateSmallBalls();
            std::this_thread::sleep_for(std::chrono::seconds(8));
        }
    }
};


void threaded_client(int client_socket, std::string currentId, std::shared_ptr<Game> game) {
    char buffer[2048];
    send(client_socket, currentId.c_str(), currentId.size(), 0);
    while (clients % 3 != 0) {}
    std::string initialPlayerPositions = game->playerInfo[0] + "|" + game->playerInfo[1] + "|" + game->playerInfo[2];
    std::string initialMessage = initialPlayerPositions + "?" + game->generateSmallBallsInfo() + "@8,163,18|250,176,2|2,246,250";
    send(client_socket, initialMessage.c_str(), initialMessage.size(), 0);

    std::string reply;

    while (true) {
        memset(buffer, 0, sizeof(buffer));
        int bytes_received = recv(client_socket, buffer, sizeof(buffer), 0);

        if (bytes_received <= 0) {
            send(client_socket, "Goodbye", sizeof("Goodbye"), 0);
            break;
        } else {
            std::string data = buffer;
            size_t posSeparator = data.find("?");

            std::string playerData;

            for (int i = 0; i < 3; ++i) {
                playerData = data.substr(0, posSeparator);
                data = data.substr(posSeparator + 1);

                size_t idSeparator = playerData.find(":");
                int playerId = std::stoi(playerData.substr(0, idSeparator));
                std::string playerPositionAndRadius = playerData.substr(idSeparator + 1);

                game->playerInfo[playerId] = std::to_string(playerId) + ":" + playerPositionAndRadius;
            }

            size_t idSeparator = playerData.find(":");
            int playerId = std::stoi(playerData.substr(0, idSeparator));
            std::string playerPositionAndRadius = playerData.substr(idSeparator + 1);
            size_t commaSeparator = playerPositionAndRadius.find(",");
            int playerX = std::stoi(playerPositionAndRadius.substr(0, commaSeparator));
            int playerY = std::stoi(playerPositionAndRadius.substr(commaSeparator + 1));
            size_t lastComma = playerPositionAndRadius.rfind(",");
            int playerRadius = std::stoi(playerPositionAndRadius.substr(lastComma + 1));

            game->handleCollision(playerId, playerX, playerY, playerRadius);

            reply = game->playerInfo[0] + "|" + game->playerInfo[1] + "|" + game->playerInfo[2];
            reply += "?" + game->generateSmallBallsInfo();
        }

        send(client_socket, reply.c_str(), reply.size(), 0);
    }
    int disconnectedPlayerX = rand() % 800 - 900;
    int disconnectedPlayerY = rand() % 600 - 700;
    int disconnectedPlayerRadius = 9;
    // Ustaw informacje o rozłączonym graczu
    game->playerInfo[std::stoi(currentId)] =
        currentId + ":" +
        std::to_string(disconnectedPlayerX) + "," +
        std::to_string(disconnectedPlayerY) + "," +
        std::to_string(disconnectedPlayerRadius);
    std::cout << "Player has left the game" << std::endl;
    close(client_socket);
}

int main() {
    int serverSocket = socket(AF_INET, SOCK_STREAM, 0);

    sockaddr_in serverAddress, clientAddress;
    serverAddress.sin_family = AF_INET;
    serverAddress.sin_port = htons(5555);
    serverAddress.sin_addr.s_addr = INADDR_ANY;

    bind(serverSocket, (struct sockaddr*)&serverAddress, sizeof(serverAddress));
    listen(serverSocket, 3);
    std::cout << "Waiting for a connection" << std::endl;

    clients = 0;
    std::shared_ptr<Game> game = std::make_shared<Game>();

    while (true) {
        socklen_t clientSize = sizeof(clientAddress);
        int clientSocket = accept(serverSocket, (struct sockaddr*)&clientAddress, &clientSize);
        if (clients % 3 == 0){
            game = std::make_shared<Game>();
            std::cout << "A new game has been created." << std::endl;
        }
        std::cout << "A new client has connected to the server on addr: " << inet_ntoa(clientAddress.sin_addr) << std::endl;
        std::thread clientThread(threaded_client, clientSocket, std::to_string(clients % 3), game);
        clientThread.detach();
        clients += 1;
    }

    close(serverSocket);

    return 0;
}
