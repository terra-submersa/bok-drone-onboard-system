# Survey angled pole

The goal is to see how precise we can capture a surveyed positions with a pole, correcting with the angle.
The problem is to see how we can get rid of trying to stabilize vertically while swimming.

## Preliminaries
### Rover Measure precision
**Question:** How precise is the position streamed by the rover with bas FIX corrections?

The device is centimeter precise. But our first tests with NMEA data import show
[strange patterns](../img.png). When the pole is a rest with have errors within 20-30 centimeters. The streamed GGA data is maybe before corrections.

We streamed LLH data and plot the distance of one point towards the average over last 4 seconds  with (../../bok_drone_onboard_system/experiments/survey-angled-pole.py).
The last field is the distance to the average => we are below 1cm !
```
2025-08-24T12:51:45.200 (5.4625614, 43.7376372, 304.94) err=0.010 FIX -> 0.003
2025-08-24T12:51:45.400 (5.4625614, 43.7376372, 304.93) err=0.010 FIX -> 0.001
2025-08-24T12:51:45.600 (5.4625614, 43.7376372, 304.92) err=0.010 FIX -> 0.001
2025-08-24T12:51:45.800 (5.4625614, 43.7376372, 304.93) err=0.010 FIX -> 0.003
2025-08-24T12:51:46.000 (5.4625614, 43.7376372, 304.92) err=0.010 FIX -> 0.002
2025-08-24T12:51:46.200 (5.4625614, 43.7376371, 304.93) err=0.010 FIX -> 0.005
2025-08-24T12:51:46.400 (5.4625614, 43.7376371, 304.93) err=0.010 FIX -> 0.005
2025-08-24T12:51:46.600 (5.4625614, 43.7376372, 304.93) err=0.010 FIX -> 0.001
```

When the rover is disconnected from the base, we fall back on *single* mode ~50cm
```
2025-08-24T12:48:04.000 (5.4625604, 43.7376366, 305.15) err=0.030 FIX -> 0.098
2025-08-24T12:48:04.200 (5.4625604, 43.7376366, 305.17) err=0.150 Single -> 0.093
2025-08-24T12:48:04.400 (5.4625619, 43.7376360, 305.03) err=3.750 Single -> 0.138
2025-08-24T12:48:04.600 (5.4625633, 43.7376357, 304.90) err=3.800 Single -> 0.227
2025-08-24T12:48:04.800 (5.4625646, 43.7376354, 304.77) err=3.850 Single -> 0.321
2025-08-24T12:48:05.000 (5.4625660, 43.7376352, 304.65) err=4.000 Single -> 0.409
2025-08-24T12:48:05.200 (5.4625673, 43.7376348, 304.56) err=4.150 Single -> 0.499
2025-08-24T12:48:05.400 (5.4625678, 43.7376345, 304.51) err=4.400 Single -> 0.527
```
**Answer:** The rover is centimeter precise with LLH streaming.

### BNO08x angle precision throught rotation
Assessing rigorously the BNO08x angle accuracy is not trivial. But we shall first guarantee that the reported angle is not affected through rotation over the pole axis.

**Question** what is the BNO08x angle precision through pole rotation?

Protocol:
1. we set the raspberry PI is angle recording mode.
2. we fix the two ends of the pole.
3. We note the time
4. We rotate the pole without moving the ends
5. repeat 2-4 with different positions
6. We analyse the data to see delta during the tine intervals.

#### Setup
* We left the carbon 12mm pole with is too flexible. Significant errors are observed on steady manipulation.
* We moved to an aluminium broom stick (which is still a bit flexible) and a stabilization system far from perfect (fixing the pole and making it rotate through it axis).
![img.png](images/img.png)
![img_1.png](images/img_1.png)
* We captured 3 different angles, rotating each during 40 seconds at least (this means (400 data points))
* We define one end of the pole fixed `O`(`origin`) and look at the error distribution at the other end `P(t)` during rotation. The pole is 2 meters long. A perfect situation would be an error of 0m.

#### Results
The BN0085 capture a quaternion, which can be converted in a 3D vector (X=>East, Y=>North, Z=>Up), once we give a `natural vector`.
This vector reflects how the BNO08x is placed along the pole axis. By construction, the vector should theoritically be (1, 0, 0).

The computations are done in the [vector_error](../../bok_drone_onboard_system/experiments/vector_error.py) scripts, where the recorded databases in copied form the Raspberry PI attached to the pole

##### Step 1 - nominal correction
During each of the three intervals `interval(ì)`, we compute the average projected position `P_i = average(P(t), t in interval(i))`, then report the mean and standard deviation of error to `P_i`.

| interval | mean   | std     |
|----------|--------|---------|
| 1        | 0.0278 | 0.0091  |
| 2        | 0.0218 | 0.0059  |
| 3        | 0.0241 | 0.0129  |

##### Step 2 - optimal correction

The (1,0,0) vector implies that the BNO08x is perfectly aligned with the pole axis. But the 3D printing enclosure is not that perfect.

We can take one of the interval (here, the first one) and use the data to find an optimal correction by minimizing the error (Nelder-Mead method).

In our experiment, the optimal vector is `(+0.9999	-0.0098	+0.0082)`. This might change under diffrent temperatures/external conditions.

| interval | mean     | std    |
|----------|----------|--------|
| 1        | 0.0133   | 0.0062 |
| 2        | 0.0140   | 0.0044 |
| 3        | 0.0160   | 0.0069 |

#### Conclusion

The pole angle measure accuracy is not perfect, but the error is bearable.
The average lies within 2.4 cm with nominal value and can be optimized 1.45cm.

We shall remind that the setup (pole + stabilization) can be improved and I would not be surprised if we measure a still better one.

Nonetheless, even the currently measured inaccuracy is sufficient for our purpose 

## Rover + angle precision(TODO)
Once the GPS precision and angle accuracy are reached, we can now tackle the overall precision of the combination of them both.

The idea is now to combine rover position + recoded angle with post-treatment.

### Protocol
- Use the previous script to save time + position etc
- start the PI, ensure the time is set precisely with NTP and save the position with the recording script
- reconciliate both recoding (with 18s GPS time leap)