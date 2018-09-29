#!/bin/env python3
import matplotlib.pyplot as plt
import argparse

def load_file(url):
    with open(url, "r") as f:
        l_distance = list()
        l_level = list()
        raw = f.readline()
        while raw not in ["", " ", "\t", "\n"]:
            raw_distance, raw_level = raw.replace("\n","").split("\t")
            f_distance = float(raw_distance)
            f_level = float(raw_level)
            l_distance.append(f_distance)
            l_level.append(f_level)
            raw = f.readline()
    return l_distance, l_level

def trim(l_traces):
    """
    Cut at first sample < 5dB
    """
    index = 0
    cutoff_level = 1.0
    l_level = l_traces[0][1]
    while l_level[index] > cutoff_level:
        index += 1
    l_new_traces = list()
    for l_distance, l_level in l_traces:
        l_new_distance = l_distance[:index]
        l_new_level = l_level[:index]
        l_new_traces.append((l_new_distance, l_new_level))
    return l_new_traces

def identify(l_traces):
    """
        Object      =   gain,   drop,   colour difference
        -----------------------------------------
        Break         =   5.0,    12.0,   False
        Splice      =   0.0,    0.1,    False
        Bend        =   0.0,    0.1,    True
        Coupling    =   1.0,    0.1,

        window_size at 6 seconds = 100
        window_size at 30 seconds = 32
    """

    window_size=72
    averaging_size=window_size//4
    trace_length_min_window = len(l_traces[0][0])-window_size
    d_detected_features = {}
    windows_since_last_successful_detection = 1.0
    b_break = False
    for index in range(0, trace_length_min_window):
        # get out of window of previous successful detection
        if windows_since_last_successful_detection < 1.0:
            windows_since_last_successful_detection += 1/window_size
        else:
            gain = False
            drop = False
            gain_colour_difference = False
            drop_colour_difference = False
            # Get window
            l_level_window = l_traces[0][1][index:index+window_size]
            l_slices = [l_level_window[i:i+averaging_size] for i in range(0, window_size, averaging_size)]
            l_averaged_slices = [sum(l_slice)/averaging_size for l_slice in l_slices]
            # Look for gain
            if (l_averaged_slices[0]+0.25) <= l_averaged_slices[1]:
                gain = (l_averaged_slices[1]-l_averaged_slices[0])
                if len(l_traces) > 1:
                    for l_colour_trace in l_traces:
                        if not(gain_colour_difference):
                            l_colour_level_window = l_colour_trace[1][index:window_size]
                            l_colour_slices = [l_colour_level_window[i:i+averaging_size] for i in range(0, window_size, averaging_size)]
                            l_averaged_colour_slices = [sum(l_slice)/averaging_size for l_slice in l_colour_slices]
                            # Compate the current variance to the variance of another colour
                            if abs( (l_averaged_slices[1] - l_averaged_slices[0]) - (l_averaged_colour_slices[1] - l_averaged_colour_slices[0]) ) > 1.0:
                                gain_colour_difference = True
            # Look for drop
            if (l_averaged_slices[-2]-0.2) >= l_averaged_slices[-1]:
                drop = l_averaged_slices[0]-l_averaged_slices[-1]
                if len(l_traces) > 1:
                    for l_colour_trace in l_traces:
                        if not(drop_colour_difference):
                            l_colour_level_window = l_colour_trace[1][index:window_size]
                            l_colour_slices = [l_colour_level_window[i:i+averaging_size] for i in range(0, window_size, averaging_size)]
                            l_averaged_colour_slices = [sum(l_slice)/averaging_size for l_slice in l_colour_slices]
                            # Compate the current variance to the variance of another colour
                            if abs( (l_averaged_slices[0] - l_averaged_slices[-1]) - (l_averaged_colour_slices[0] - l_averaged_colour_slices[-1]) ) > 0.5:
                                drop_colour_difference = True
            # if there is a gain >= 5 and a drop >= 12 then it's a break
            f_distance = l_traces[0][0][index+(window_size//2)]
            #print(f_distance, gain, drop, drop_colour_difference)
            if (gain >= 4) and (drop>=3):
                d_detected_features[f_distance] = "Break"
                b_break = True
            else:
                if b_break:
                    pass
                # if there is a gain >= 1 and a drop >= 0.1 then it's a coupling
                elif (gain >= 0.1) and (drop>=0.1):
                    d_detected_features[f_distance] = "Coupling"
                # if there is no significant gain and a drop >= 0.1 and no colour drop_colour_difference then it's a splice
                elif (drop>=0.1) and not drop_colour_difference:
                    d_detected_features[f_distance] = "Splice"
                # if threre is no significant gain and a drop >= 0.1 and there is a drop_colour_difference then it's a bend
                elif (drop>=0.5) and drop_colour_difference:
                    d_detected_features[f_distance] = "Bend"

            if f_distance in d_detected_features.keys():
                windows_since_last_successful_detection = 0.0
    return d_detected_features

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", metavar='FILE', nargs='+')
    args = parser.parse_args()
    l_traces = [load_file(name) for name in args.files]
    l_traces = trim(l_traces)
    fig, axs = plt.subplots(len(l_traces))
    for i in range(len(l_traces)):
        axs[i].plot(l_traces[i][0], l_traces[i][1])
    plt.show()
    print(identify(l_traces))
