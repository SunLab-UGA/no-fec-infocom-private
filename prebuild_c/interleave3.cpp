#include <iostream>
#include <vector>
#include <bitset>

// Helper function to set the nth bit of a byte array
void setBit(char* output, int n, bool value) {
    if (value)
        output[n / 8] |= (1 << (7 - n % 8));
    else
        output[n / 8] &= ~(1 << (7 - n % 8));
}

// Helper function to get the nth bit of a byte array
bool getBit(const char* input, int n) {
    return (input[n / 8] & (1 << (7 - n % 8))) != 0;
}

// Function to reorder bits based on a priority matrix
void reorderBits(const char* input, char* output, const std::vector<int>& priority_matrix) {
    for (int i = 0; i < 96; ++i) {  // 96 bits in 12 bytes
        bool bitValue = getBit(input, i);
        setBit(output, priority_matrix[i], bitValue);
    }
}

int main() {
    const char input[12] = {'p','a','y','l','o','a','d',' ','d','a','t','a'};
    char output[12] = {};  // Initialize all bits to 0

    // temporary variables
    char step_in_bits[12] = {};
    char step_out_bits[12] = {};

    // Priority matrix, high priority (significant) bits get placed near pilot symbols
    std::vector<int> priority_matrix = {
        80, 72, 64, 56, 48, 40, 32, 24, 16, 4, 10, 17, 25, 33, 41, 49, 57, 65, 73, 81, 88, 92, 93, 89, 82, 74, 66, 58, 50, 42, 34, 26, 18, 11, 5, 0,
        2, 6, 12, 19, 27, 35, 43, 51, 59, 67, 75, 83, 84, 76, 68, 60, 52, 44, 36, 28, 20, 13, 7, 3, 1, 8, 14, 21, 29, 37, 45, 53, 61, 69, 77, 85, 90, 94, 95, 91, 86, 78, 70, 62, 54, 46, 38, 30, 22, 15, 9, 23, 31, 39, 47, 55, 63, 71, 79, 87
    };
    std::cout << "Priority Matrix:" << std::endl;
    for (int i = 0; i < priority_matrix.size(); ++i) {
        std::cout << priority_matrix[i] << (i < priority_matrix.size() - 1 ? ", " : "");
        if (i % 32 == 31) {
            std::cout << std::endl;
        }
    }
    std::cout << std::endl;


    // Significance matrix, high significance bits get placed first
    std::vector<int> significance_matrix = {
        0, 32, 64, 1, 33, 65, 2, 34, 66, 3, 35, 67, 4, 36, 68, 5, 37, 69, 6, 38, 70, 7, 39, 71, 8, 40, 72, 9, 41, 73, 10, 42, 74, 11, 43, 75, 12, 44,
        76, 13, 45, 77, 14, 46, 78, 15, 47, 79, 16, 48, 80, 17, 49, 81, 18, 50, 82, 19, 51, 83, 20, 52, 84, 21, 53, 85, 22, 54, 86, 23, 55, 87, 24, 56, 88, 25, 57, 89, 26, 58, 90, 27, 59, 91, 28, 60, 92, 29, 61, 93, 30, 62, 94, 31, 63, 95
    };

    std::cout << "Significance Matrix:" << std::endl;
    for (int i = 0; i < significance_matrix.size(); ++i) {
        std::cout << significance_matrix[i] << (i < significance_matrix.size() - 1 ? ", " : "");
        if (i % 32 == 31) {
            std::cout << std::endl;
        }
    }
    std::cout << std::endl;
    // Calculate the inverse matrix============================
    std::vector<int> inverse_priority_matrix(96);
    std::vector<int> inverse_significance_matrix(96);

    // Calculate the inverse priority matrix
    for (int i = 0; i < priority_matrix.size(); ++i) {
        inverse_priority_matrix[priority_matrix[i]] = i;
    }
    // Print the inverse priority matrix
    std::cout << "Inverse Priority Matrix:" << std::endl;
    for (int i = 0; i < inverse_priority_matrix.size(); ++i) {
        std::cout << inverse_priority_matrix[i] << (i < inverse_priority_matrix.size() - 1 ? ", " : "");
        if (i % 32 == 31) {
            std::cout << std::endl;
        }
    }
    std::cout << std::endl;

    // Calculate the inverse significance_matrix 
    for (int i = 0; i < significance_matrix.size(); ++i) {
        inverse_significance_matrix[significance_matrix[i]] = i;
    }
    // Print the inverse priority matrix
    std::cout << "Inverse Significance Matrix:" << std::endl;
    for (int i = 0; i < inverse_significance_matrix.size(); ++i) {
        std::cout << inverse_significance_matrix[i] << (i < inverse_significance_matrix.size() - 1 ? ", " : "");
        if (i % 32 == 31) {
            std::cout << std::endl;
        }
    }
    std::cout << std::endl;

    //======================================================= START
    //Input
    for (int i = 0; i < 12; ++i) {
        std::cout << std::bitset<8>(input[i]) << " ";
    }std::cout << std::endl;

    for (int i = 0; i < 12; ++i) {
        std::cout << input[i] << " ";
    }std::cout << std::endl;
    

    reorderBits(input, step_in_bits, significance_matrix);
    reorderBits(step_in_bits, step_out_bits, priority_matrix);

    // reverse the interleaving
    reorderBits(step_out_bits, step_in_bits, inverse_priority_matrix);
    reorderBits(step_in_bits, output, inverse_significance_matrix);

    // Output the results for verification
    for (int i = 0; i < 12; ++i) {
        std::cout << std::bitset<8>(output[i]) << " ";
    }std::cout << std::endl;

    for (int i = 0; i < 12; ++i) {
        std::cout << output[i] << " ";
    }std::cout << std::endl;

    return 0;
}
