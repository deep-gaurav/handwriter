import os
import logging

import numpy as np
import svgwrite

import drawing
import lyrics
from rnn import rnn

import sys, getopt
from hand import Hand
from utils.string_utils import accomodate_list_to_character_limit

def main(argv):
    print('starting')
    style = 0
    outputfile = ''
    inputstring = ''
    bias = 0.75
    color = 'blue'
    width = 1
    try:
        opts, args = getopt.getopt(argv,"hi:o:s:b:c:w:",["iline=","ofile=","style=","bias=","color=","width="])  
    except getopt.GetoptError:
        print('demo.py -i <inputstring> -o <outputfile> -s <style> -b <bias> -c <color> -w <stroke width>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'test.py -i <inputfile> -o <outputfile>'
            sys.exit()
        elif opt in ("-i", "--iline"):
            inputstring = arg
        elif opt in ("-o","--ofile"):
            outputfile = arg
        elif opt in ("-s","--style"):
            style = int(arg)
        elif opt in ("-b","--bias"):
            bias = float(arg)
        elif opt in ("-c","--color"):
            color = arg
        elif opt in ("-w","--width"):
            width = int(arg)
    print('writing '+inputstring)

    hand = Hand()
    lines = inputstring.split("\n")
    lines = accomodate_list_to_character_limit(lines)
    biases = [bias for i in lines]
    styles = [style for i in lines]
    stroke_colors = [color for i in lines]
    stroke_widths = [width for i in lines]

    hand.write(
        filename=outputfile,
        lines=lines,
        biases=biases,
        styles=styles,
        stroke_colors=stroke_colors,
        stroke_widths=stroke_widths
    )
    
    print('writen to '+outputfile)


if __name__ == '__main__':
    main(sys.argv[1:])

