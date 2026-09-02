# Implementation of the Rainflow Counting Algorithm

`rain_fall_algorithm.py` contains a custom implementation of the rainflow counting algorithm and its graphical visualization. This algorithm is used to analyze cyclic loads: it splits a load time history into separate cycles and half-cycles, which can later be used to estimate fatigue damage in a material.

## General Idea of the Algorithm

Rainflow counting treats the load graph as a sequence of peaks and valleys. A flow is conditionally started from each peak and moves along the graph until one of the stopping conditions is met. This approach makes it possible to identify closed and non-closed load cycles.

This implementation handles three main situations:

- the flow reaches the end of the load history;
- the flow merges with a flow that started earlier;
- the flow stops when it meets an opposite peak with greater or equal amplitude.

## Data Preparation

In the `main()` function, the `source_values` array defines the load history. If the `is_peaks` flag is set to `False`, the values are inverted and the first element is removed. This is done so that the sequence starts with a peak, which is required by the following algorithm logic.

After that, the values are converted into a list of indexed points:

```python
source_taple = list(enumerate(source_values, start=2))
```

Then the points are split into two lists:

- `peak_list` - peaks, meaning every second point starting from the first one;
- `valley_list` - valleys, meaning every second point starting from the second one.

These two lists are passed to the `process_peaks()` function.

## Main Logic of `process_peaks()`

The `process_peaks(peak_list, valley_list)` function is the central part of the implementation. It iterates through all peaks and builds the corresponding rainflow path for each peak.

For every current peak, the following values are determined:

- `current_peak` - the current peak;
- `current_valley` - the valley after it;
- `next_peak` - the next peak;
- `next_valley` - the next valley.

The results are stored in the `res` list. Each result element has the following structure:

```python
(case_name, chain)
```

where `case_name` shows the type of flow termination, and `chain` contains the points through which this flow passes.

## Special Intersection Points

The `dictSpecialPoints` dictionary is used to store special points where one flow intersects or merges with another one. The key is the peak coordinate, and the value is the intersection point.

This is needed so that later flows can correctly end not simply at a peak or valley, but exactly at the point where they meet a previously constructed flow.

## Segment Intersection Check

The `segment_intersection(p1, p2, p3, p4)` function calculates the intersection point of two line segments. It is used when the current rainflow path may intersect the next segment of the graph.

If the segments are parallel or intersect only on the extension of their lines, the function returns `None`. If a real intersection exists inside both segments, the function returns the point `(ix, iy)`.

## Flow Termination Cases

### Case `al`

If the current peak is the last one and there is no next peak, the flow reaches the end of the history. In this case, the result receives a path from the current peak to the current valley, or to a special point if it was already found earlier.

### Case `bb`

If the current peak already exists in `dictSpecialPoints`, it means that the flow is interrupted by a previously constructed flow. In this case, the path ends at the corresponding special point.

### Case `b`

This case is used when the flow merges with a previous flow or reaches the end without meeting an opposite peak with greater amplitude. If a special point already exists for the current valley, the path immediately ends there. Otherwise, the algorithm continues building the horizontal movement of the flow.

### Case `c`

If the next peak has an amplitude greater than or equal to the amplitude of the current peak, the flow stops. This corresponds to the rainflow counting rule where a half-cycle ends when it meets an opposite extremum of no smaller magnitude.

## Building the Flow Path

If the flow does not end immediately, the algorithm enters the `while next_peak != None` loop. Inside this loop, it gradually checks the following peaks and valleys.

To continue the path, the following point is created:

```python
next_point = (next_valley_x, current_valley_y)
```

This point models the horizontal movement of the rainflow path at the level of the current valley. If this horizontal segment intersects the next segment of the graph, `segment_intersection()` is called. The found point is added to the current path and stored in `dictSpecialPoints`.

Thus, the implementation does not only compare amplitudes, but also builds the geometric trajectory of the flow on the graph.

## Visualization

After peak processing, the `main()` function receives the `processed_peaks` list. Then each detected path is drawn with a separate color and line style. The following helper functions are used for this:

- `print_chain_h()` - draws the path in horizontal orientation;
- `print_chain_v()` - draws the path in vertical orientation;
- `print_label_for_list_h()` and `print_label_for_list_v()` - add labels to the detected paths;
- `get_chain_info()` - creates a textual description of the path point coordinates.

The graph shows the original load history and all detected rainflow paths. Each path has a label with the case type and number, for example `b:1` or `c:3`.

## Summary

This program implements a step-by-step geometric interpretation of the rainflow counting algorithm. The code splits the input signal into peaks and valleys, starts flows from each peak, checks termination conditions, finds flow intersection points, and outputs the result as a graph. The main value of this implementation is that it not only follows the cycle detection logic, but also visually shows how the rainflow paths are formed.

## Run

```bash
python rain_fall_algorithm.py
```
