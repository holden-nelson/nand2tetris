// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.
    @SelectedScreenWord
    M=0

(BlackLoop)
    @KBD
    D=M

    @SwitchToWhiteLoop
    D;JEQ

    @SelectedScreenWord
    D=M
    @SCREEN
    A=D+A
    M=-1

    @SelectedScreenWord
    M=M+1

    @BlackLoop
    0;JMP

(WhiteLoop)
    @KBD
    D=M

    @SwitchToBlackLoop
    D;JGT

    @SelectedScreenWord
    D=M
    @SCREEN
    A=D+A
    M=0

    @SelectedScreenWord
    M=M+1

    @WhiteLoop
    0;JMP

(SwitchToWhiteLoop)
    @SelectedScreenWord
    M=0

    @WhiteLoop
    0;JMP

(SwitchToBlackLoop)
    @SelectedScreenWord
    M=0

    @BlackLoop
    0;JMP

