import matplotlib.pyplot as plt


def get_chain_info(chain):
    result = ""
    for i in range(len(chain)):
        result += f" ({chain[i][0]:.1f},{chain[i][1]:.1f})"
    return result

def print_chain_h(x_values, y_values, color="red", linestyle="-", is_annotate=True):
    plt.plot(x_values, y_values, color=color, marker="o", linestyle=linestyle)
    if is_annotate == True:
        for x, y in zip(x_values, y_values):
            plt.annotate(f"({y}, {x})", (x, y), textcoords="offset points", xytext=(6, 6), fontsize=8)

def print_label_for_list_h(x_prev, x_current, y_prev, y_current, text, color, d_x=0.4, d_y=0.4):    
        x= (x_prev + x_current) / 2
        y= (y_prev + y_current) / 2

        plt.text(x - d_x, y - d_y, text, fontsize=8, color=color, ha="center", va="center")


def print_chain_v(x_values, y_values, color="red", linestyle="-", is_annotate=True):
    # было: plt.plot(x_values, y_values, ...)
    plt.plot(y_values, x_values, color=color, marker="o", linestyle=linestyle)
    if is_annotate == True:
        for x, y in zip(x_values, y_values):
            # было: (x, y)
            plt.annotate(f"({y}, {x})", (y, x), textcoords="offset points", xytext=(6, 6), fontsize=8)

def print_label_for_list_v(x_prev, x_current, y_prev, y_current, text, color, d_x=0.4, d_y=0.4):
    x = (x_prev + x_current) / 2
    y = (y_prev + y_current) / 2
    # было: plt.text(x, y - d_y, ...)
    plt.text(y - d_y, x - d_x, text, fontsize=8, color=color, ha="center", va="center")

def segment_intersection(p1, p2, p3, p4, eps=1e-9):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < eps:
        return None  # параллельны или совпадают

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    u = ((x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)) / den

    if -eps <= t <= 1 + eps and -eps <= u <= 1 + eps:
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        return (ix, iy)  # точка пересечения

    return None  # пересекаются только продолжения прямых, не отрезки


def process_peaks(peak_list, valley_list):   

    res = []
    dictSpecialPoints = {}
    
    # res.append(('a', [
    #                     peak_list[0], valley_list[0], peak_list[1] 
    #                  ]))

    # res.append(('d', [
    #                     peak_list[4], valley_list[4], peak_list[5] 
    #                  ]))

    # res.append(('d1', [
    #                     peak_list[5], valley_list[5] 
    #                  ]))

    # res.append(('c', [
    #                     peak_list[6], valley_list[6], peak_list[7] 
    #                  ]))

    for current_index in range(0, len(peak_list)):
        current_peak = peak_list[current_index]
        current_peak_x = current_peak[0]
        #current_res = []

        if current_index >= len(valley_list):
            current_valley = None
        else:
            current_valley = valley_list[current_index]
        
        next_index = current_index  + 1

        if next_index >= len(peak_list):
            next_peak = None
        else:
            next_peak = peak_list[next_index]

        if next_index >= len(valley_list):
            next_valley = None
        else:
            next_valley = valley_list[next_index]

        
        #peak is last
        # case (a) It reaches the end of the time history;
        if next_peak == None:
            if current_valley != None:               
                if current_peak_x in dictSpecialPoints: 
                    spec = dictSpecialPoints[current_peak_x]
                    res.append(('al', [
                         current_peak, spec
                    ]))
                else:
                    res.append(('al', [
                         current_peak, current_valley
                    ]))
        elif (current_peak_x in dictSpecialPoints):
            #The half-cycle starting at peak 9 terminates where it is interrupted by a flow from earlier peak 8 (case b);
            spec = dictSpecialPoints[current_peak_x]
            res.append(('bb', [
                         current_peak, spec
                    ]))
        else:
            current_res = []
            current_res.append(current_peak)
          
            if current_valley != None:
                #current_res.append(current_valley)
                x = current_valley[0]
                if x in dictSpecialPoints:
                     #case (b) It merges with a flow that started at an earlier tensile peak;                    
                    spec = dictSpecialPoints[x]
                    current_res.append(spec)
                    res.append(('b', current_res))
                    continue
                else:
                    current_res.append(current_valley)


            is_case_c = False
            index_after_current = 0
            while next_peak != None:
                      
                next_peak_y = next_peak[1]
                current_peak_y = current_peak[1]


                if next_peak_y >= current_peak_y:
                    #case (c) An opposite tensile peak has greater or equal magnitude compared to the starting point of the half-cycle.
                    if current_valley != None:
                        #current_res.append(current_valley)
                        is_case_c = True
                    break
                else:
                    if current_valley != None:
                        

                        next_valley_x = current_valley[0] + 2*(index_after_current + 1) 
                       #current_valley_y_ = current_valley[1]
                        current_valley_y = current_res[len(current_res) - 1][1]
                        next_peak_x = next_peak[0]


                        next_point = (next_valley_x, current_valley_y)
                        point_intersected = None
                        if next_valley != None and current_valley_y > next_valley[1]:
                            point_intersected = segment_intersection(current_valley, next_point, next_peak, next_valley)
                        if point_intersected != None:
                            current_res.append(point_intersected)
                            if next_peak_x in dictSpecialPoints:
                                spec = dictSpecialPoints[next_peak_x]
                                current_res.append(spec)
                                is_case_c = True
                                dictSpecialPoints[next_peak_x] = point_intersected 
                                break     
                            else:
                                current_res.append(next_valley)
                            
                            dictSpecialPoints[next_peak_x] = point_intersected 
                        
                        else:
                             current_res.append(next_point)
                       

                index_after_current = index_after_current + 1
                next_index = next_index + 1

                if next_index >= len(peak_list):
                    next_peak = None
                else:
                    next_peak = peak_list[next_index]

                if next_index >= len(valley_list):
                    next_valley = None
                else:
                    next_valley = valley_list[next_index]
            
            if is_case_c == True:
                res.append(('c', current_res))
            else:
                next_valley_x = current_res[len(current_res) - 1][0] + 1
                current_valley_y = current_res[len(current_res) - 1][1]
                current_res.append((next_valley_x, current_valley_y))
                res.append(('b', current_res))

    return res






def main():

    is_vertical = False
    is_peaks = False


    # first shoul be peak
    source_values = [0, -150, 100, 0, 130, -120, 110, -50, 80, 0, 150, -100, 100, 0, 130, 0]
    source_values = [2, -14, 10, 0, 13, -9, 11, -8, 8, -9, 15, -4, 10, 0, 13, 0]

    if is_peaks == False:
        copied_negated = [-x for x in source_values]
        source_values = copied_negated[1:]
        source_taple = list(enumerate(source_values, start=2))
    else:
        source_taple = list(enumerate(source_values, start=1))

    peak_list = source_taple[0::2]
    valley_list = source_taple[1::2]
 

    color_list = ['green', 'yellow', 'blue', 'purple', (0.9, 0.647, 0.402), 'black', (0., 0.847, 0.902), (0.678, 0., 0.902), (0.678, 0.847, 0.902), 'orange' ]

    y_values = [item[0] for item in source_taple]
    x_values = [item[1] for item in source_taple]

    if is_peaks == False:
        values = [-item for item in x_values]
        x_values = values

    if is_vertical == True:
        print_chain_v(x_values, y_values, color="red")
    else:
        print_chain_h(x_values, y_values, color="red")


    processed_peaks = process_peaks(peak_list, valley_list)
    
    if is_peaks == False:
        processed  = []
        for idx, case in enumerate(processed_peaks):
            case_info = case[0]
            chain = case[1]
            processed.append((case_info  , [(item[0], -item[1]) for item in chain])) 
        processed_peaks = processed


    d_y = 0.15
    
    for idx, case in enumerate(processed_peaks):
        case_info = case[0]
        chain = case[1]
        
        color = color_list[idx % len(color_list)]    
        cur_inestyle = "--" if idx % 2 == 0 else ":"  
        #cur_dy = d_y if idx % 2 == 0 else 2 * d_y     
        cur_dy = (idx % 4 + 1) * d_y
        if is_vertical == True:  
            print_chain_v(
                [item[1] for item in chain],
                [(item[0] - cur_dy) for item in chain],
                color = color,
                linestyle=cur_inestyle,
                is_annotate=False
            )
            print_label_for_list_v(chain[0][1], chain[1][1], chain[0][0], chain[1][0], f"({case_info}:{idx + 1})", color)   
  
        else:
            print_chain_h(
                [item[1] for item in chain],
                [(item[0] - cur_dy) for item in chain],
                color = color,
                linestyle=cur_inestyle,
                is_annotate=False
            )
            info = ""
            info = get_chain_info(chain)
            print_label_for_list_h(chain[0][1], chain[1][1], chain[0][0], chain[1][0], f"({case_info}:{idx + 1}) {info}", color)  



    plt.title("Rainflow Counting")

    plt.xlabel("X")
    plt.ylabel("Y")
    if is_vertical == False:
        plt.ylim(len(y_values)+2, 0)
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.show()



if __name__ == "__main__":
    main()
