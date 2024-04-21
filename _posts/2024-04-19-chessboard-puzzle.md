---
layout: post
date: 2024-04-19
title: The Almost impossible chessboard puzzle
author: Gaurav Somani
issue: 2
---

There is a 8x8 chess board covered with a coin placed in each of its squares. Each of the coin is either heads or tails up. The key of a jail room is kept under one of the squares of chessboard. The warden proposes to free the two prisoners if they can solve the following puzzle.

**Puzzle**: The first prisoner is told the location of the key and he can flip atmost one coin to indicate the location of the key. The second prisoner needs to find the location of the keys by observing the final configuration of the board after flipping the coin. The video of the puzzle can be found [here] (https://www.youtube.com/watch?v=wTJI_WuZSwE&t=0s)

I encourage you to try the puzzle on your own. The hints can be revealed sequentially.

**Observations (Hints)**

<details>
    <summary> Hint 1 (Board configuration) </summary>
>! The configuration of board can be represented by a 64 bit number where each bit represents coin orientation (heads being 0 and tails being 1) ||
</details>

<details>
    <summary> Hint 2 (Key location) </summary>
>! The location of the key can be encoded as a 6 bit number ranging from (0_{10} to 63_{10}).
</details>

<details>
    <summary> Hint 3 (Reachable configurations) </summary>
>! Since warden can leave the board in any of the states, each of the configuration reachable (by atmost 1 bit flip) from the current configuration should cover at least one configuration corresponding to each of the key locations.
</details>

<!---
Since there are 65 configurations reachable from current configuration (including current one), two configurations must point to same location and other 63 configurations each pointing to one specific location. This suggests that one of the possible 64 bit flips does not change the key location and it is just liking adding zero to a number does not change it.
-->

<details>
    <summary> Hint 4 (Encoding key location) </summary>
>! Since the second prisoner only sees the final 64 bit configuration, each 64 bit configuration of the board corresponds to a single 6 bit key location. The 64 bit number is like encoding of 6 bit number. Any change in input 6 bit number should require atmost 1 bit flip in encoded data. This property is almost opposite of what we want in good error correcting codes. Since the key can be anywhere(from position 0 to 63) for any configuration, a bit flip anywhere on the board might be required. Hence, at least 6 bits are required to represent a bit flip.

</details>
**Solution**
