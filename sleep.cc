#include <chrono>
#include <thread>

int main()
{
    std::chrono::milliseconds timespan{1000};
    std::this_thread::sleep_for(timespan);
}
