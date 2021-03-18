import logging
import os

import numpy as np
import svgwrite

import drawing
from rnn import rnn


class Hand(object):

    def __init__(self):
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        self.nn = rnn(
            log_dir='logs',
            checkpoint_dir='checkpoints',
            prediction_dir='predictions',
            learning_rates=[.0001, .00005, .00002],
            batch_sizes=[32, 64, 64],
            patiences=[1500, 1000, 500],
            beta1_decays=[.9, .9, .9],
            validation_batch_size=32,
            optimizer='rms',
            num_training_steps=100000,
            warm_start_init_step=17900,
            regularization_constant=0.0,
            keep_prob=1.0,
            enable_parameter_averaging=False,
            min_steps_to_checkpoint=2000,
            log_interval=20,
            logging_level=logging.CRITICAL,
            grad_clip=10,
            lstm_size=400,
            output_mixture_components=20,
            attention_mixture_components=10
        )
        self.nn.restore()

    def write(self, filename, lines, biases=None, styles=None, stroke_colors=None,
              stroke_widths=None, line_height=60, view_width=1000, align_center=False):
        print "received lines",lines, "biases", biases, "styles",styles
        valid_char_set = set(drawing.alphabet_perf)
        for line_num, line in enumerate(lines):
            if len(line) > 75:
                raise ValueError(
                    (
                        "Each line must be at most 75 characters. "
                        "Line {} contains {}"
                    ).format(line_num, len(line))
                )

            for char in line:
                if char not in valid_char_set:
                    print("Invalid character {} detected".format(char))
                    # raise ValueError(
                    #     (
                    #         "Invalid character {} detected in line {}. "
                    #         "Valid character set is {}"
                    #     ).format(char, line_num, valid_char_set)
                    # )
        linestosample = []
        line_nums = []
        biasetosample = []
        stylestosample = []
        charbeingremoved = []
        for i in range(len(lines)):
            line_splits = []
            lastpos = 0
            line = lines[i]
            removedchar = []
            for charpos,char in enumerate(line):
                if char not in valid_char_set:
                    print "Removing ", char
                    removedchar.append(char)
                    line_splits.append(
                        line[lastpos:charpos]
                    )
                    lastpos=charpos+1
            line_splits.append(line[lastpos:])
            linestosample.extend(line_splits)
            line_nums.extend([i for x in line_splits])
            biasetosample.extend( [biases[i] for x in line_splits])
            stylestosample.extend([styles[i] for x in line_splits])
            charbeingremoved.append(removedchar)
        print "Sampling for"
        for i in range(len(linestosample)):
            linestosample[i] = linestosample[i]
            if not linestosample[i]:
                linestosample[i]= ''
            print linestosample[i]
                        
        print "Sending samples", linestosample, "Biases", biasetosample, "styles", stylestosample
        strokes = self._sample(linestosample, biases=biasetosample, styles=stylestosample)
        print "Strokes generated", strokes
        self._draw(strokes,linestosample, line_nums, lines, charbeingremoved, filename, stroke_colors=stroke_colors,
                   stroke_widths=stroke_widths, line_height=line_height,
                   view_width=view_width, align_center=align_center,biases=biases,styles=styles)

    def _sample(self, lines, biases=None, styles=None):
        print "Sampling lines"
        print lines
        num_samples = len(lines)
        max_tsteps = 40 * max([len(i) for i in lines])
        biases = biases if biases is not None else [0.5] * num_samples

        x_prime = np.zeros([num_samples, 1200, 3])
        x_prime_len = np.zeros([num_samples])
        chars = np.zeros([num_samples, 120])
        chars_len = np.zeros([num_samples])

        if styles is not None:
            for i, (cs, style) in enumerate(zip(lines, styles)):
                x_p = np.load('styles/style-{}-strokes.npy'.format(style))
                c_p = np.load('styles/style-{}-chars.npy'.format(style)).tostring().decode('utf-8')

                c_p = str(c_p) + " " + cs
                c_p = drawing.encode_ascii(c_p)
                c_p = np.array(c_p)

                x_prime[i, :len(x_p), :] = x_p
                x_prime_len[i] = len(x_p)
                chars[i, :len(c_p)] = c_p
                chars_len[i] = len(c_p)

        else:
            for i in range(num_samples):
                encoded = drawing.encode_ascii(lines[i])
                chars[i, :len(encoded)] = encoded
                chars_len[i] = len(encoded)

        [samples] = self.nn.session.run(
            [self.nn.sampled_sequence],
            feed_dict={
                self.nn.prime: styles is not None,
                self.nn.x_prime: x_prime,
                self.nn.x_prime_len: x_prime_len,
                self.nn.num_samples: num_samples,
                self.nn.sample_tsteps: max_tsteps,
                self.nn.c: chars,
                self.nn.c_len: chars_len,
                self.nn.bias: biases
            }
        )
        samples = [sample[~np.all(sample == 0.0, axis=1)] for sample in samples]
        return samples

    def removeinvalid(self,line, replchar = ''):
        valid_char_set = set(drawing.alphabet)
        chars = set(list(line))
        for c in chars:
            if c not in valid_char_set:
                line=line.replace(c,replchar)
        return line

    def _fix_unknownchar(self,line,dwg,bias=None, style=None,yoff=0,color='black',size=10):
        valid_char_set = set(drawing.alphabet)
        yoff+=size

        for i,c in enumerate(line):
            if c not in valid_char_set:
                l1 = self.removeinvalid(line[:i+0], replchar='  ')
                l2 = self.removeinvalid(line[:i+1], replchar='  ')
                print "Finding cooord using {} bias {} style {}".format(l2,bias,style)
                
                w1 = self.getwidthofline(l1,bias,style)
                w2 = self.getwidthofline(l2,bias,style)
                
                width = (w1+w2)/2

                print "Offset x for {} is {}".format(c,width)
                print "Offset y for {} is {}".format(c,yoff)
                t = dwg.text(c,insert = (width, yoff),font_size=str(size)+'px',fill=color)
                dwg.add(t)

    def getwidthofline(self,line,bias,style):
        strokes = self._sample([line],biases=[bias],styles=[style])
        offsets = strokes[0]
        offsets[:, :2] *= 1.5
        strokes = drawing.offsets_to_coords(offsets)
        strokes = drawing.denoise(strokes)
        strokes[:, :2] = drawing.align(strokes[:, :2])

        strokes[:, 1] *= -1
        return strokes[:, 0].max()

    def _draw(self, strokesmain,sampledsegments, line_nums, lines, removedchars, filename, stroke_colors=None, stroke_widths=None,
              line_height=60, view_width=1000, align_center=True,biases=None, styles=None):
        print "Strokes "
        for i in range(len(strokesmain)):
            print "Stroke ",i+1
            print strokesmain[i]
        
        print "Line nums"
        print line_nums
        print "Removed chars"
        print removedchars
        stroke_colors = stroke_colors or ['black'] * len(lines)
        stroke_widths = stroke_widths or [2] * len(lines)

        view_height = line_height * (len(strokesmain) + 1)

        dwg = svgwrite.Drawing(filename=filename)
        dwg.viewbox(width=view_width, height=view_height)
        dwg.add(dwg.rect(insert=(0, 0), size=(view_width, view_height), fill='white'))

        initial_coord = np.array([0, -(3 * line_height / 4)])

        i=0
        while i<len(line_nums):
            line_num = line_nums[i]
            line_splits = []
            sseg = []
            while True:
                if i<len(line_nums) and line_num == line_nums[i]:
                    sseg.append(sampledsegments[i])
                    line_splits.append(strokesmain[i])
                    i+=1
                else:
                    break
            line = lines[line_num]
            color= stroke_colors[line_num]
            width =stroke_widths[line_num]
            if not line:
                initial_coord[1] -= line_height
                continue
            lastshift = 0

            for split_num,split_val in enumerate(line_splits):
                segment=sseg[split_num]
                print "Drawing line ",line_num, "split ", split_num, "Segment", segment
                if split_num>0:
                    chartoinser = removedchars[line_num][split_num-1]
                    size = 20
                    yoff = -initial_coord[1]
                    g = dwg.g(style="font-size:{};font-family:Caveat;fill:{};".format(size,color,color))
                    t = dwg.text(chartoinser,x=[lastshift],y=[yoff+size],font_size=str(size)+'px',fill=color)
                    g.add(t)
                    dwg.add(g)
                    w = textwidth(chartoinser,fontsize=size)
                    lastshift+=size
                if not segment:
                    print "Skipping segment"
                    continue
                offsets = split_val

                # print "Offsets"
                # print offsets
                offsets[:, :2] *= 1.5
                strokes = drawing.offsets_to_coords(offsets)
                # print "Coords"
                # print strokes
                strokes = drawing.denoise(strokes)
                strokes[:, :2] = drawing.align(strokes[:, :2])

                strokes[:, 1] *= -1
                strokes[:, :2] -= strokes[:, :2].min() + initial_coord

                if align_center:
                    strokes[:, 0] += (view_width - strokes[:, 0].max()) / 2
                
                print "segment starts at ",zip(*strokes.T)[0][0]
                if split_num>0:
                    strokes[:,0]-=zip(*strokes.T)[0][0]
                strokes[:,0]+=lastshift
                

                prev_eos = 1.0
                p = "M{},{} ".format(0, 0)
                print "starting this segment at ",lastshift
                for x, y, eos in zip(*strokes.T):
                    p += '{}{},{} '.format('M' if prev_eos == 1.0 else 'L', x, y)
                    prev_eos = eos
                    if x> lastshift:
                        lastshift = x
                    # print "Made last shift ",x
                path = svgwrite.path.Path(p)
                path = path.stroke(color=color, width=width, linecap='round').fill("none")
                dwg.add(path)

            initial_coord[1] -= line_height
        dwg.save()
        # for lc, offsets, line, color, width in zip(range(len(lines)),strokes, lines, stroke_colors, stroke_widths):

        #     if not line:
        #         initial_coord[1] -= line_height
        #         continue

        #     offsets[:, :2] *= 1.5
        #     strokes = drawing.offsets_to_coords(offsets)
        #     strokes = drawing.denoise(strokes)
        #     strokes[:, :2] = drawing.align(strokes[:, :2])

        #     strokes[:, 1] *= -1
        #     strokes[:, :2] -= strokes[:, :2].min() + initial_coord

        #     if align_center:
        #         strokes[:, 0] += (view_width - strokes[:, 0].max()) / 2

        #     prev_eos = 1.0
        #     p = "M{},{} ".format(0, 0)
        #     for x, y, eos in zip(*strokes.T):
        #         p += '{}{},{} '.format('M' if prev_eos == 1.0 else 'L', x, y)
        #         prev_eos = eos
        #     path = svgwrite.path.Path(p)
        #     path = path.stroke(color=color, width=width, linecap='round').fill("none")
        #     dwg.add(path)

        #     self._fix_unknownchar(line,bias=biases[lc],style=styles[lc],yoff=-initial_coord[1],color=color,dwg=dwg,size=20)

        #     initial_coord[1] -= line_height

        # dwg.save()

def textwidth(text, fontsize=14):
    try:
        import cairo
    except Exception, e:
        return len(str) * fontsize
    surface = cairo.SVGSurface('undefined.svg', 1280, 200)
    cr = cairo.Context(surface)
    cr.select_font_face('Arial', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(fontsize)
    xbearing, ybearing, width, height, xadvance, yadvance = cr.text_extents(text)
    return width