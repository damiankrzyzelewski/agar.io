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

// Struktura reprezentująca informacje o małej kulce
struct Ball {
    int x;
    int y;
};

std::mutex smallBallsMutex;
std::vector<std::string> playerInfo = {"0:20,20,10", "1:400,20,10", "2:20,400,10"};
std::vector<Ball> smallBalls;  // Informacje o małych kulach

std::string currentId = "0";

// Funkcja do generowania informacji o małych kulach
std::string generateSmallBallsInfo() {
    smallBallsMutex.lock();
    std::string smallBallsInfo;
    for (size_t i = 0; i < smallBalls.size(); ++i) {
        smallBallsInfo += std::to_string(smallBalls[i].x) + "," + std::to_string(smallBalls[i].y);
        if (i < smallBalls.size() - 1) {
            smallBallsInfo += "|";
        }
    }
    smallBallsMutex.unlock();
    return smallBallsInfo;
}

// Funkcja do inicjalizacji informacji o małych kulach
void initializeSmallBalls(int numBalls, int boardWidth, int boardHeight) {
    for (int i = 0; i < numBalls; ++i) {
        Ball ball;
        ball.x = rand() % boardWidth;
        ball.y = rand() % boardHeight;
        smallBalls.push_back(ball);
    }
}

void generateNewBalls() {
    while (true) {
        std::this_thread::sleep_for(std::chrono::seconds(3));

        // Dodaj nowe małe piłki
        Ball newBall;
        newBall.x = rand() % 800;  // Zakładam szerokość planszy 800 (dostosuj do rzeczywistej szerokości)
        newBall.y = rand() % 600;  // Zakładam wysokość planszy 600 (dostosuj do rzeczywistej wysokości)
        smallBallsMutex.lock();
        smallBalls.push_back(newBall);
        smallBallsMutex.unlock();
        std::cout << "Added a new small ball at (" << newBall.x << "," << newBall.y << ")" << std::endl;
    }
}

void threaded_client(int client_socket) {
    char buffer[2048];
    send(client_socket, currentId.c_str(), currentId.size(), 0);

    currentId = std::to_string(std::stoi(currentId) + 1);

    // Send initial positions after sending client ID
    std::string initialPlayerPositions = playerInfo[0] + "|" + playerInfo[1] + "|" + playerInfo[2];

    // Send player and smallBalls positions
    std::string initialMessage = initialPlayerPositions + "?" + generateSmallBallsInfo();
    send(client_socket, initialMessage.c_str(), initialMessage.size(), 0);

    std::string reply;

    while (true) {
        memset(buffer, 0, sizeof(buffer));
        int bytes_received = recv(client_socket, buffer, sizeof(buffer), 0);

        if (bytes_received <= 0) {
            send(client_socket, "Goodbye", sizeof("Goodbye"), 0);
            break;
    } else {
        //std::cout << "Received: " << buffer << std::endl;

        std::string data = buffer;
        size_t posSeparator = data.find("?");

        std::string playerData;  // Przeniesienie deklaracji tutaj

        for (int i = 0; i < 3; ++i) {
            playerData = data.substr(0, posSeparator);
            data = data.substr(posSeparator + 1);

            // Extract player ID, position, and radius
            size_t idSeparator = playerData.find(":");
            int playerId = std::stoi(playerData.substr(0, idSeparator));
            std::string playerPositionAndRadius = playerData.substr(idSeparator + 1);

            // Update the position and radius for the corresponding player ID
            playerInfo[playerId] = std::to_string(playerId) + ":" + playerPositionAndRadius;
        }

           // Extract player position and radius after the loop
            size_t idSeparator = playerData.find(":");
            int playerId = std::stoi(playerData.substr(0, idSeparator));
            std::string playerPositionAndRadius = playerData.substr(idSeparator + 1);
            size_t commaSeparator = playerPositionAndRadius.find(",");
            int playerX = std::stoi(playerPositionAndRadius.substr(0, commaSeparator));
            int playerY = std::stoi(playerPositionAndRadius.substr(commaSeparator + 1));
            size_t lastComma = playerPositionAndRadius.rfind(",");
            int playerRadius = std::stoi(playerPositionAndRadius.substr(lastComma + 1));
            smallBallsMutex.lock();
            for (size_t i = 0; i < smallBalls.size(); ++i) {
                // Sprawdzamy kolizję z małą piłką
                int distance = std::sqrt(std::pow(playerX+playerRadius - smallBalls[i].x, 2) + std::pow(playerY+playerRadius - smallBalls[i].y, 2));
                if (distance < playerRadius) {
                    // Gracz "zjada" małą piłkę
                    playerRadius += 2;
                    // Usuwamy małą piłkę z listy
                    smallBalls.erase(smallBalls.begin() + i);
                    std::cout << playerId << ": " << playerRadius << std::endl;

                    // Zaktualizuj playerInfo[playerId] po zwiększeniu promienia
                    playerInfo[playerId] = std::to_string(playerId) + ":" + std::to_string(playerX) + "," + std::to_string(playerY) + "," + std::to_string(playerRadius);
                    std::cout << playerInfo[playerId] << std::endl;
                    break;  // Przerwij pętlę, gdy już doszło do kolizji
                }
            }
            smallBallsMutex.unlock();
            // Construct the reply with the positions and radius of all players
            reply = playerInfo[0] + "|" + playerInfo[1] + "|" + playerInfo[2];

            // Append small balls positions to the reply
            reply += "?" + generateSmallBallsInfo();
            std::cout << "Sending: " << reply << std::endl;
        }

        send(client_socket, reply.c_str(), reply.size(), 0);
    }
    std::cout << "Connection Closed" << std::endl;
    close(client_socket);
}

int main() {
    // Initialize smallBalls
    initializeSmallBalls(20, 800, 600);
    std::thread newBallsThread(generateNewBalls);
    int serverSocket = socket(AF_INET, SOCK_STREAM, 0);

    sockaddr_in serverAddress, clientAddress;
    serverAddress.sin_family = AF_INET;
    serverAddress.sin_port = htons(5555);
    serverAddress.sin_addr.s_addr = INADDR_ANY;

    bind(serverSocket, (struct sockaddr*)&serverAddress, sizeof(serverAddress));
    listen(serverSocket, 2);
    std::cout << "Waiting for a connection" << std::endl;

    while (true) {
        socklen_t clientSize = sizeof(clientAddress);
        int clientSocket = accept(serverSocket, (struct sockaddr*)&clientAddress, &clientSize);

        std::cout << "Connected to: " << inet_ntoa(clientAddress.sin_addr) << std::endl;

        std::thread clientThread(threaded_client, clientSocket);
        clientThread.detach();  // Allow the thread to run independently
    }

    close(serverSocket);

    return 0;
}
