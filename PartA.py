import sys
import re



"""
Python's .lower() method runs in linear time relative to the size of input as it must check/transform each character.
re.findall also runs in linear time, as it must compare each character.
.extend() runs in linear time for each element must be appended.
The for loop simply runs through each line in the file, so in relation to the number of
characters in a file, this function runs in O(n) linear time.
"""
def tokenize(file_name):
    token_list = []
    with open(file_name, 'r') as file:
        # read line by line to save memory
        for line in file:
            content = line.lower()
            # get only alphanumeric characters
            token_list.extend(re.findall(r"[0-9a-zA-Z]+", content))
    return token_list



""" 
To iterate through each token in the input list takes linear time, and each
operation performed within the loop can be done in constant time, so the
function runs in O(n) linear time.
"""
def computeWordFrequencies(token_list):
    # empty dict
    token_frequencies = {}
    # if dict does not contain token, add it. else, increment value.
    for token in token_list:
        if token not in token_frequencies:
            token_frequencies[token] = 1
        else:
            token_frequencies[token] += 1
    return token_frequencies



"""
Online resources have stated that the sorted() method runs in O(nlogn) time.
The for-loop runs in linear time as each operation within it takes constant time.
The time complexity of the function is O(nlogn).
"""
def printFrequencies(frequencies):
    # sort the dict items first by value (frequency) in descending order, then alphabetically
    freq_list = sorted(frequencies.items(), key=lambda x: (-x[1], x[0]))
    for token, freq in freq_list:
        print(f"{token} - {freq}")


"""
Since the O(nlogn) time complexity of printFrequencies() dominates the
complexities of the rest of the functions called, this
main function funs in O(nlogn) time.
"""
def main():
    filename = sys.argv[1]
    token_list = tokenize(filename)
    token_freq = computeWordFrequencies(token_list)
    printFrequencies(token_freq)



if __name__ == '__main__':
    main()
