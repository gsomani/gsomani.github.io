---
layout: post
date: 2024-04-22
title: The Almost impossible chessboard puzzle
author: Gaurav Somani
issue: 2
---

There is a 8x8 chess board with a coin placed in each of its squares. Each of the coins is either heads up or tails up. The key to a jail room is kept under one of the squares of a chessboard. The warden proposes to free the two prisoners if they can solve the following puzzle.

**Puzzle**: The first prisoner is told the location of the key and he can flip atmost one coin to indicate the location of the key. The second prisoner needs to find the location of the keys by observing the final configuration of the board after flipping the coin.

The video of the puzzle can be found [here](https://www.youtube.com/watch?v=wTJI_WuZSwE)

I encourage you to try the puzzle on your own. The hints can be revealed sequentially.

**Observations (Hints)**

<details>
    <summary> Hint 1 (Board configuration) </summary>
<p> The configuration of the board can be represented by a 64-bit number where each bit represents coin orientation (heads being 0 and tails being 1). </p>
</details>

<br>
<details>
    <summary> Hint 2 (Key location) </summary>
<p> The location of the key can be encoded as a 6-bit number ranging from ($0_{10}$ to $63_{10}$). </p>
</details>

<br>
<details>
    <summary> Hint 3 (Reachable configurations) </summary>
<p> Since the warden can leave the board in any of the states, each of the configuration reachable (by atmost 1 bit flip) from the current configuration should cover at least one configuration corresponding to each of the key locations. </p>
</details>

<br>
<!---
Since there are 65 configurations reachable from current configuration (including current one), two configurations must point to same location and other 63 configurations each pointing to one specific location. This suggests that one of the possible 64 bit flips does not change the key location and it is just liking adding zero to a number does not change it.
-->

<details>
    <summary> Hint 4 (Encoding key location) </summary>
<p> Since the second prisoner only sees the final 64-bit configuration, each 64-bit configuration of the board corresponds to a single 6 bit key location. The 64-bit number is like encoding of 6-bit number. Any change in input 6-bit number should require atmost 1 bit flip in encoded data. This property is almost opposite of what we want in good error correcting codes. Since the key can be anywhere(from position 0 to 63) xor any configuration, a bit flip anywhere on the board might be required. Hence, at least 6 bits are required to represent a bit flip. </p>
</details>

<br>

**Solution**

<details>
    <summary> Solution </summary>
<p> Assign an unique 6-bit representation from $0_{10}$ to $63_{10}$ to each of the squares. Then do a XOR of all the numbers which correspond to 1 in 64-bit configuration of squares ( tails up according to our convention here). This gives us a 6-bit number xor each 64-bit configuration. To traverse to another 64-bit configuration with different 64-bit configuration, we just need to flip 1 bit.
To see that, consider $a$ to be 6-bit number xor current configuration and $b$ be 6-bit number encoding the location of the key. Then,

$a$ $\oplus$ ($a \oplus b$) = $b$

So, we need to just flip the coin on the square corresponding to $a \oplus b$ to reach a configuration such that 6-bit number computation results in $b$. Then, second prisoner just needs to XOR numbers of all the tails up.

  </p>
</details>

<br>

<p> Try to guess the key location as the second prisoner give the following chessboard. <span style="color:red"> Heads is represented by red. </span> and <span style="color:blue"> Tails is represented by blue. </span> Click on the square to find out whether the key is under that. The key location is determined by above solution strategy. 
</p>

<style>
  .chessboard {
    display: grid;
    grid-template-columns: repeat(8, 70px);
    grid-template-rows: repeat(8, 70px);
  }
  .square {
    width: 70px;
    height: 70px;
    background-color: #f0d9b5; /* Light color for chessboard */
    border: 1px solid black;
    display: flex;
    justify-content: center;
    align-items: center;
    font-weight: bold;
    cursor: pointer;
  }
</style>

<div class="chessboard" id="chessboard"></div>

<script>
  const size = 8;

  function paddedBinary(num, size)
  { return num.toString(2).padStart(size, '0');}

  function createChessboard(size) {
    const chessboard = document.getElementById('chessboard');
    chessboard.innerHTML = '';

    const squares = 'repeat(' + size + ', 70px)';

    chessboard.style.setProperty('grid-template-columns', squares);
    chessboard.style.setProperty('grid-template-rows', squares);

    const coins = [0, 1];
    var configuration = Array();
    const numBits = Math.ceil(2*Math.log2(size));
    
    const colors = ['red', 'blue'];

    for (let row = 0; row < size; row++) {
      for (let col = 0; col < size; col++) {
        const square = document.createElement('div');
        square.classList.add('square');
        chessboard.appendChild(square);

        const randomCoin = coins[Math.floor(Math.random() * coins.length)];
        square.innerHTML  = `${paddedBinary(configuration.length, numBits)}`;
        square.style.color = colors[randomCoin]; 
        
        square.setAttribute('id', configuration.length);
        configuration.push(randomCoin);
        
        square.addEventListener('click', handleClick);
      }
    }
    return configuration;
  }

   function handleClick(event) {
      const id = event.target.id;
      check(id); 
    }

  function configToKey(config){
    var sum = 0;
    for (i in config)
      sum ^= (config[i]*i);
    return sum;
  }

  const config = createChessboard(size);
  const key = configToKey(config);

  function check(guess){
    const success = (key == guess);

    if (success)
      alert("Successfull key guess");
    else
      alert("Wrong! Try again");
  }


</script>
<br/>

<br/>

The solution mentioned is the one presented in the [video](https://www.youtube.com/watch?v=wTJI_WuZSwE). I would also like to mention that prisoners can decide to label squares with 6-bit numbers in any permutation leading to possible 64! solutions to this puzzle. But some permutations have more symmetry and require less effort to remember and actually do computations in real time.

There is an alternative solution to this in terms of primitive polynomials which I discovered while studying BCH codes. The primitive polynomials are important in understanding algebraic error correcting codes including BCH and also solve this puzzle.
