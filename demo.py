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

def runSVG(inputstring,style,bias,color,width,outputfile):
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

def runStrokes(inputstring,style,bias,color,width):
    hand = Hand()
    lines = inputstring.split("\n")
    lines = accomodate_list_to_character_limit(lines)
    biases = [bias for i in lines]
    styles = [style for i in lines]
    stroke_colors = [color for i in lines]
    stroke_widths = [width for i in lines]

    stt = hand.write_get_strokes(
        lines=lines,
        biases=biases,
        styles=styles,
        stroke_colors=stroke_colors,
        stroke_widths=stroke_widths
    )
    params = {
        'strokes': stt[0],
        'strokes_text': stt[1],
        'line_numbers': stt[2],
        'lines':stt[3],
        'removed_characters': stt[4],
        'stroke_colors': stt[5],
        'stroke_widths': stt[6],
        'line_height':stt[7],
        'view_width':stt[8],
        'align_center':stt[9],
        'biases':stt[10],
        'styles':stt[11],
    }
    return hand.Gdraw(
        params['strokes'],params['strokes_text'], params['line_numbers'], params['lines'], params['removed_characters'], stroke_colors=params['stroke_colors'],
         stroke_widths=params['stroke_widths'],
              line_height=params['line_height'], view_width=params['view_width'], align_center=params['align_center'],biases=params['biases'], styles=params['styles']
    )


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
            print('test.py -i <inputfile> -o <outputfile>')
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

    runSVG(inputstring,style,bias,color,width,outputfile)
    
    print('writen to '+outputfile)



if __name__ == '__main__':
    main(sys.argv[1:])

