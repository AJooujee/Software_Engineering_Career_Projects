#include <iostream>
#include <string>

int main()
{
    const std::string applicationName{
        "Real-Time Multi-Sensor Monitoring System"
    };

    std::cout << "============================================\n";
    std::cout << applicationName << '\n';
    std::cout << "System status: STARTUP\n";
    std::cout << "Initial setup completed successfully.\n";
    std::cout << "============================================\n";

    return 0;
}