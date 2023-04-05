"""class Solution:
    def search(self, nums: list[int], target: int) -> int:
        nums.sort()
        for i in range(len(nums)):
            print(nums[i])
            if nums[i]//2==target:
                return i
            else:
                if nums[i]>target:
                    return (nums[i-1])
                else:
                    return (nums[i+1])


res=Solution().search([2,5,3],2)
print(res)"""

def locate_card(cards,query):
    # Create a variable position with the value 0
    position=0

    # Set up a loop for repetition
    while True:
        # Check if element at the current position matche the query
        if cards[position] == query:
            # Answer found! Return and exit...
            return position
        # Increment the position
        position+=1
        # Check if we have reached the end of the array
        if position==len(cards) :
            # Number not found, return -1
            return -1