# Extracting data from an ensemble of trajectories

## Overview

Collecting data such as displacements, velocities, speeds is a common task when
analyzing trajectory data. Therefore, looping over an ensemble of trajectories
ends up in repeated blocks of code specially when the data is wanted to, for
instance, be analyzed at different time scales or be concatenated.

This tutorial provides an step-by-step view over the {py:func}`~stats.collect`
function. It gets a friendly way to "collect" the basic time series researchers
that process trajectories are continuously dealing with.

## Let's begin

Let us first create a fake ensemble of just two (for the sake of illustration)
trajectories using the {py:class}`~yupi.Trajectory` class from `yupi`.

```python
import numpy as np
from yupi import Trajectory
from yupi.stats import collect

# x-coordinate for the first/second trajectory
x1 = 2 * np.arange(5)
x2 = x1 + 1

# y-coordinates
y1 = x1**2
y2 = x2**2

# Time step and ids
dt = .5
id_traj1 = 'traj_01'
id_traj2 = 'traj_02'

# Instantiating the class
traj1 = Trajectory(x=x1, y=y1, dt=dt, traj_id=id_traj1)
traj2 = Trajectory(x=x2, y=y2, dt=dt, traj_id=id_traj2)

# Gather in an ensemble
trajs = [traj1, traj2]
```

At this point, it is quite easy using `yupi` to extract some time series from a
single trajectory. For example:

- position: `traj1.r`
- displacement: `traj1.r.delta`
- velocity: `traj1.v`
- speed: `traj1.v.norm`
- distance: `traj1.delta_r.norm`

But how to get these from an ensemble? How to extract it when time scales are
different from the time step? In what is next, these questions are answered
with some illustrative examples while a detailed explanation of every parameter
is given on the {py:func}`~stats.collect` function.

## Collect general function

By default, the {py:func}`~stats.collect` function takes a list trajectory an returns
an array with all the positional data of each trajectory concatenated.

```python
collect(trajs)
```

```text
array([[ 0.  0.]
       [ 2.  4.]
       [ 4. 16.]
       [ 6. 36.]
       [ 8. 64.]
       [ 1.  1.]
       [ 3.  9.]
       [ 5. 25.]
       [ 7. 49.]
       [ 9. 81.]])
```

The following sections will describe all the parameters available that manipulate
the resulting data within the {py:func}`~stats.collect` function.

### The `lag` parameter

Suppose the underlying ensemble of trajectories as being realizations of a
process with different statistical properties at different time scales. For
such a case, `lag` can be helpful if it is set properly. If `lag` is an
integer it is taken as the number of samples. On the other hand, if `lag` is
of type `float`, it is taken as the time to lag where its units are those of
the time array (i.e., `traj.t`).

If `lag` is not set, the default value is `lag=0` will be assumed.

```python
collect(trajs, lag=2)
```

```text
array([[ 4., 16.],
       [ 4., 32.],
       [ 4., 48.],
       [ 4., 24.],
       [ 4., 40.],
       [ 4., 56.]])
```

```python
collect(trajs, lag=1.0)
```

```text
array([[ 4., 16.],
       [ 4., 32.],
       [ 4., 48.],
       [ 4., 24.],
       [ 4., 40.],
       [ 4., 56.]])
```

### The `concat` parameter

As we show in the very first example, the code for `concat(trajs)` will return
an array with all the positional data of each trajectory concatenated.

If the data is wanted to be split by realizations, the `concat` parameter
should be set to `False`.

```python
collect(trajs, concat=False)
```

```text
array([[[ 0.,  0.],
        [ 2.,  4.],
        [ 4., 16.],
        [ 6., 36.],
        [ 8., 64.]],

       [[ 1.,  1.],
        [ 3.,  9.],
        [ 5., 25.],
        [ 7., 49.],
        [ 9., 81.]]])
```

### The `warnings` parameter

If the given lag is larger than one of the trajectories length, a warning
message will arise and the position of the trajectory in the ensemble and its
*id* will be shown. The {py:func}`~stats.collect` function will skip this
trajectory. To avoid warning messages set the parameter to `False`.

```python
traj1.dt = .01  # redefining dt for the first trajectory
collect(trajs, lag=dt)
```

```text
15:07:11 [WARNING] Trajectory 0 with id=traj_01 is shorten than 50 samples
array([[ 2.,  8.],
       [ 2., 16.],
       [ 2., 24.],
       [ 2., 32.]])
```

```python
collect(trajs, lag=dt, warnings=False)
```

```text
array([[ 2.,  8.],
       [ 2., 16.],
       [ 2., 24.],
       [ 2., 32.]])
```

### The `velocity` parameter

Some times it is useful to have the velocity of the trajectory. To indicate that
the velocity is wanted, the `velocity` parameter should be set to `True`.

```python
collect(trajs, velocity=True)
```

```text
array([[ 4.  8.]
       [ 4. 24.]
       [ 4. 40.]
       [ 4. 56.]
       [ 4. 16.]
       [ 4. 32.]
       [ 4. 48.]
       [ 4. 64.]])
```

Additional if the `lag` is used, the velocity will be calculated according
the given lag.

```python
collect(trajs, lag=2, velocity=True)
```

```text
array([[ 4. 16.]
       [ 4. 32.]
       [ 4. 48.]
       [ 4. 24.]
       [ 4. 40.]
       [ 4. 56.]])
```

### The `func` parameter

All the examples described above only returns raw data from the trajectories. If
the data is wanted to be transformed, the `func` parameter should be set to
a function that will be applied to each vector (before concatenation).

This could help if we want to extract for example the delta velocity of the
trajectories.

```python
collect(trajs, velocity=True, func=lambda vec: vec.delta)
```

```text
array([[ 0. 16.]
       [ 0. 16.]
       [ 0. 16.]
       [ 0. 16.]
       [ 0. 16.]
       [ 0. 16.]])
```

```python
collect(trajs, func=lambda vec: vec.norm)
```

```text
array([ 4.47213595 12.16552506 20.09975124 28.0713377 8.24621125 16.1245155
       24.08318916 32.06243908])
```

### The `at` parameter

When the data is wanted to be extracted at a certain time (or index), the
`at` parameter should be used. If `at` is an integer, it is taken as the
index. If `at` is a float, it is taken as the time (in this case the
index is calculated using the trajectory's dt value).

This paramenter can not be used with `lag` parameter at the same time. In
addition, When the `at` parameter is used, the `concat` parameter is
ignored.

```python
collect(trajs, at=1)
```

```text
array([[ 2.,  4.],
       [ 3.,  9.]])
```

```python
collect(trajs, at=.5)
```

```text
array([[ 2.,  4.],
       [ 3.,  9.]])
```

## Collect specific functions

- {py:func}`~stats.collect_at_step`
- {py:func}`~stats.collect_at_time`
- {py:func}`~stats.collect_step_lagged`
- {py:func}`~stats.collect_time_lagged`

These functions are just spetializations of the {py:func}`~stats.collect`
function. All of them use the {py:func}`~stats.collect` function internally.
Each of them has a different usage depending on if the data is wanted to be
extracted at a certain time or step or if it is wanted to be extracted lagged.
