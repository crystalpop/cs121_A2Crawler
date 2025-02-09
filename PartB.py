import PartA as A
import sys



"""
The python sorting algorithn takes O(nlogn) time for each list.
The while loop runs in linear time relative to the size
of the shorter token list, and each operation done within
the loop is done in constant time.
So, O(nlogn) dominates the time complexity of this funciton.
"""
def common_tokens(token_list1, token_list2):
    # use a set to avoid duplicates
    common = set()
    # sort the lists in place to increase efficiency
    token_list1.sort()
    token_list2.sort()
    i = 0
    j = 0
    #iterate until one of the lists runs out --> no more common tokens
    while i < len(token_list1) and j < len(token_list2):
        # increment the index that points to the smaller value
        if token_list1[i] < token_list2[j]:
            i += 1
        elif token_list2[j] < token_list1[i]:
            j += 1
        # values are equal, add the value to the set
        else:
            common.add(token_list1[i])
            i,j = i+1, j+1
    return len(common)



"""
tokenize() from part A runs in linear O(n) time, so O(nlogn) from common_tokens()
dominates the time complexity of the main function.
"""
def main():
    file_name1 = sys.argv[1]
    file_name2 = sys.argv[2]
    token_list1 = A.tokenize(file_name1)
    token_list2 = A.tokenize(file_name2)
    print(common_tokens(token_list1, token_list2))



if __name__ == '__main__':
    main()
